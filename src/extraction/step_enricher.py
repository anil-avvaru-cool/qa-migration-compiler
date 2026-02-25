# src/extraction/step_enricher.py

import logging
import re
from typing import List, Dict, Optional


logger = logging.getLogger(__name__)


class StepEnricher:
    """
    Enrich extracted steps with proper target IDs and input data sources.
    
    Responsibilities:
    - Link step target references to actual target IDs from targets.json
    - Create proper StepInput objects with source/field
    - Create StepTarget objects for navigation
    - Infer data sources from method parameters
    - Normalize step structure for IR builder
    
    Resolution Strategies (in order):
    1. Already has explicit targetId
    2. Fuzzy match target_name_id in targets
    3. NEW: CallGraph resolution for navigation methods
    4. Mark as unresolved
    """

    def __init__(self, extracted_targets: List[Dict]):
        """
        Initialize enricher with extracted targets.
        
        Args:
            extracted_targets: List of target dicts from LocatorExtractor
        """
        # Build lookup maps
        self.targets_by_name = {}
        self.targets_by_id = {}

        for target in extracted_targets:
            target_id = target.get("targetId")
            name = target.get("name")

            if target_id:
                self.targets_by_id[target_id] = target
            if name:
                self.targets_by_name[name] = target

        logger.info("StepEnricher initialized with %d targets", len(extracted_targets))
        
        # NEW: Injected by pipeline
        self.call_graph = None
        self.extracted_targets = extracted_targets

    def enrich(self, extracted_steps: List[Dict], test_data: Optional[Dict] = None) -> List[Dict]:
        """
        Enrich extracted steps with proper structure.
        
        Args:
            extracted_steps: List of step dicts from ActionMapper
            test_data: Optional test data for field matching
        
        Returns:
            List of enriched step dicts
        """
        enriched_steps = []

        for i, step in enumerate(extracted_steps, 1):
            enriched_step = self._enrich_step(step, i, test_data)
            if enriched_step:
                enriched_steps.append(enriched_step)

        logger.info("Enriched %d steps", len(enriched_steps))
        return enriched_steps

    def _enrich_step(self, step: Dict, step_index: int, test_data: Optional[Dict] = None) -> Optional[Dict]:
        """Enrich a single step."""

        action = step.get("action", "generic")

        # Resolve targetId
        target_id = self._resolve_target_id(step)

        # Build step input
        step_input = None
        if action in ("type", "select", "clear"):
            step_input = self._build_step_input(step, test_data)

        # Build step target (for navigation)
        step_target = None
        if action == "navigate" or step.get("target"):
            step_target = self._build_step_target(step)

        # Build normalized step
        enriched = {
            "stepId": step.get("stepId") or f"STEP_{step_index:02d}",
            "action": action,
            "targetId": target_id,
            "target": step_target,
            "input": step_input,
            "parameters": step.get("parameters", {}),
        }

        return enriched

    def _resolve_target_id(self, step: Dict) -> Optional[str]:
        """
        Resolve target ID with multi-level fallback strategies.
        
        Strategy 1: Already has explicit targetId
        Strategy 2: Fuzzy match target_name_id
        Strategy 3: NEW - CallGraph for navigation methods
        Strategy 4: Return None (unresolved)
        """
        
        # Strategy 1: Already has explicit targetId
        if step.get("targetId"):
            logger.debug("[StepEnricher] Strategy 1: Using explicit targetId: %s", step["targetId"])
            return step["targetId"]

        # Strategy 2: Fuzzy match target_name_id in targets
        target_ref = step.get("target_name_id") or step.get("targetId")
        if target_ref:
            # Try to find in maps
            if target_ref in self.targets_by_id:
                logger.debug("[StepEnricher] Strategy 2: Exact match in targets_by_id: %s", target_ref)
                return target_ref
            
            if target_ref in self.targets_by_name:
                result = self.targets_by_name[target_ref].get("targetId")
                logger.debug("[StepEnricher] Strategy 2: Exact match in targets_by_name: %s", target_ref)
                return result

            # Try fuzzy matching (camelCase to SNAKE_CASE)
            uppercase_ref = re.sub(r'(?<!^)(?=[A-Z])', '_', target_ref).upper()
            if uppercase_ref in self.targets_by_id:
                logger.debug("[StepEnricher] Strategy 2: Fuzzy match transformed (%s -> %s)", target_ref, uppercase_ref)
                return uppercase_ref

        # Strategy 3: NEW - CallGraph resolution for navigation
        if step.get("action") == "navigate" and self.call_graph and step.get("page_class"):
            try:
                logger.debug("[StepEnricher] Strategy 3: Attempting CallGraph resolution for navigate action")
                
                page_class = step.get("page_class")
                method_name = step.get("method_name") or step.get("name")
                
                if method_name:
                    # Resolve method definition
                    method_def = self.call_graph.resolve_method_definition(page_class, method_name)
                    
                    if method_def:
                        # Find driver.get() calls inside method
                        get_calls = self.call_graph.find_internal_calls(
                            page_class, method_name, "get", "driver"
                        )
                        
                        if get_calls:
                            # Extract URL from first get call
                            url = self._extract_url_from_node(get_calls[0])
                            if url:
                                # Try to match URL to navigation target
                                nav_target_id = self._find_navigation_target_by_url(url)
                                if nav_target_id:
                                    logger.debug("[StepEnricher] Strategy 3: Resolved via CallGraph: %s -> %s", 
                                               method_name, nav_target_id)
                                    return nav_target_id
            except Exception as e:
                logger.debug("[StepEnricher] Strategy 3 failed: %s", e)

        # Strategy 4: Mark as unresolved
        logger.debug("[StepEnricher] Could not resolve targetId for step with action=%s, target_name_id=%s",
                    step.get("action"), target_ref)
        return None

    def _extract_url_from_node(self, node) -> Optional[str]:
        """Extract URL from a driver.get() node."""
        if not hasattr(node, 'children'):
            return None
        
        for child in node.children:
            value = child.properties.get("value") if hasattr(child, 'properties') else None
            if value and isinstance(value, str):
                if value.startswith("http://") or value.startswith("https://"):
                    return value
        
        return None

    def _find_navigation_target_by_url(self, url: str) -> Optional[str]:
        """Find navigation target in extracted_targets that matches URL."""
        for target in self.extracted_targets:
            if target.get("type") == "navigation":
                target_url = target.get("target", {}).get("value")
                if target_url == url:
                    return target.get("targetId")
        
        return None

    def _build_step_input(self, step: Dict, test_data: Optional[Dict] = None) -> Optional[Dict]:
        """Build proper StepInput from step information."""

        # Check if step already has input info
        if step.get("input"):
            input_spec = step["input"]
            source = input_spec.get("source", "constant")
            field = input_spec.get("field")
            value = input_spec.get("value")

            # If source is "constant" but value not set, try to infer from test data
            if source == "constant" and value and field and test_data:
                if field in test_data:
                    return {
                        "source": "data",
                        "field": field,
                        "masked": False,
                    }

            return {
                "source": source,
                "field": field or (field if field else None),
                "masked": input_spec.get("masked", False),
            }

        return None

    def _build_step_target(self, step: Dict) -> Optional[Dict]:
        """Build StepTarget from step information (mainly for navigate actions)."""

        # Check if step already has target
        if step.get("target"):
            return step["target"]

        return None

    def match_test_data_fields(self, enriched_steps: List[Dict], test_data: Dict) -> List[Dict]:
        """
        Match step inputs to actual test data fields.
        
        For steps with input type="constant", try to match to test_data fields
        to convert to type="data".
        
        Args:
            enriched_steps: List of enriched steps
            test_data: Test data dict
        
        Returns:
            Steps with updated input mappings
        """
        for step in enriched_steps:
            if not step.get("input"):
                continue

            input_spec = step["input"]

            # If already mapped to data source, skip
            if input_spec.get("source") == "data":
                continue

            # Try to infer field name from target ID or action context
            inferred_field = self._infer_data_field(step, test_data)

            if inferred_field:
                step["input"] = {
                    "source": "data",
                    "field": inferred_field,
                    "masked": self._should_mask_field(inferred_field),
                }

        return enriched_steps

    def _infer_data_field(self, step: Dict, test_data: Dict) -> Optional[str]:
        """Infer data field name from step targetId or action."""

        target_id = step.get("targetId", "").lower()

        # Try direct field name mapping
        for field_name in test_data.keys():
            field_lower = field_name.lower()

            if field_lower in target_id:
                return field_name

            if target_id in field_lower:
                return field_name

        # Try pattern matching based on target semantics
        if "username" in target_id or "user" in target_id or "email" in target_id:
            if "username" in test_data:
                return "username"
            if "email" in test_data:
                return "email"

        if "password" in target_id:
            if "password" in test_data:
                return "password"

        if "search" in target_id:
            if "searchTerm" in test_data:
                return "searchTerm"
            if "productName" in test_data:
                return "productName"

        return None

    def _should_mask_field(self, field_name: str) -> bool:
        """Determine if a field should be masked in logs."""
        sensitive_keywords = {
            "password",
            "pin",
            "token",
            "secret",
            "apikey",
            "cvv",
            "ssn",
        }

        return any(keyword in field_name.lower() for keyword in sensitive_keywords)
