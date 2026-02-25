# src/ir/validator/completeness_validator.py

import logging
from typing import List, Dict, Optional, Any
from src.ir.models.project import ProjectIR
from src.ir.models.test import TestIR
from src.ir.models.targets import TargetIR

logger = logging.getLogger(__name__)


class ValidationReport:
    """Report of IR validation results."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
    
    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
    
    def add_info(self, message: str):
        """Add an info message."""
        self.info.append(message)
    
    def is_complete(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0
    
    def is_valid(self) -> bool:
        """Alias for is_complete()."""
        return self.is_complete()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "complete": self.is_complete(),
            "valid": self.is_valid(),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "info_count": len(self.info),
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
        }
    
    def summary(self) -> str:
        """Get summary string."""
        status = "✓ COMPLETE" if self.is_complete() else "✗ INCOMPLETE"
        return (f"{status} | Errors: {len(self.errors)} | Warnings: {len(self.warnings)} | "
                f"Info: {len(self.info)}")


class CompletenessValidator:
    """
    Validate IR completeness and data integrity.
    
    Checks:
    1. All step targetIds exist in targets
    2. Navigation steps have proper targets
    3. Step inputs are resolved
    4. Assertions are valid
    5. No orphaned references
    """
    
    def __init__(self):
        pass
    
    def validate(self, project_ir: ProjectIR) -> ValidationReport:
        """
        Validate project IR for completeness.
        
        Args:
            project_ir: ProjectIR object to validate
            
        Returns:
            ValidationReport with all issues found
        """
        report = ValidationReport()
        
        logger.info("[CompletenessValidator] Starting validation of project: %s", 
                   project_ir.name if hasattr(project_ir, 'name') else "unknown")
        
        if not project_ir:
            report.add_error("Project IR is None")
            return report
        
        # Build target lookup
        targets_dict = self._build_targets_dict(project_ir)
        
        # Get tests
        tests = project_ir.tests if hasattr(project_ir, 'tests') else []
        if not tests:
            report.add_info("No tests found in project")
        
        # Check 1: All step targetIds exist
        orphaned_count = 0
        for test in tests:
            for step in test.steps if hasattr(test, 'steps') else []:
                orphaned = self._validate_step_target(step, targets_dict, report)
                if orphaned:
                    orphaned_count += 1
        
        # Check 2: Navigation steps have targets
        for test in tests:
            for step in test.steps if hasattr(test, 'steps') else []:
                self._validate_navigation_step(step, report)
        
        # Check 3: Step inputs resolved
        for test in tests:
            for step in test.steps if hasattr(test, 'steps') else []:
                self._validate_step_input(step, report)
        
        # Check 4: Assertions valid
        for test in tests:
            for step in test.steps if hasattr(test, 'steps') else []:
                self._validate_assertions(step, report)
        
        # Add summary info
        total_tests = len(tests)
        total_steps = sum(len(test.steps) if hasattr(test, 'steps') else 0 for test in tests)
        complete_steps = total_steps - orphaned_count
        total_targets = len(targets_dict)
        
        report.add_info(f"Project summary: {total_tests} tests, "
                       f"{total_steps} steps, {complete_steps} complete, "
                       f"{total_targets} targets")
        
        if orphaned_count == 0 and not report.errors:
            report.add_info("✓ All references resolved, no orphaned data")
        
        logger.info("[CompletenessValidator] Validation complete: %s", report.summary())
        return report
    
    def _build_targets_dict(self, project_ir: ProjectIR) -> Dict[str, Any]:
        """Build lookup dictionary of targets."""
        targets = {}
        if hasattr(project_ir, 'targets'):
            for target in project_ir.targets:
                target_id = target.id if hasattr(target, 'id') else target.get("targetId")
                if target_id:
                    targets[target_id] = target
        
        return targets
    
    def _validate_step_target(self, step: Any, targets_dict: Dict, report: ValidationReport) -> bool:
        """
        Validate that step targetId exists in targets.
        
        Returns: True if orphaned, False if resolved
        """
        action = step.action if hasattr(step, 'action') else step.get("action", "unknown")
        
        # Ignore non-targeting actions
        if action in ("waitForVisible", "wait", "scrollTo", "screenshot"):
            return False
        
        # Skip navigation actions (they use target.url, not targetId)
        if action == "navigate":
            return False
        
        # Check for type/click/select/etc that need targets
        if action in ("type", "click", "select", "clear", "getAttribute", "getText"):
            target_id = step.targetId if hasattr(step, 'targetId') else step.get("targetId")
            
            if not target_id:
                test_id = step.testId if hasattr(step, 'testId') else step.get("testId", "unknown")
                step_id = step.stepId if hasattr(step, 'stepId') else step.get("stepId", "UNKNOWN")
                
                message = (f"Test {test_id}, Step {step_id}: "
                          f"Missing targetId for action '{action}'")
                report.add_error(message)
                logger.warning("[CompletenessValidator] %s", message)
                return True
            
            elif target_id not in targets_dict:
                test_id = step.testId if hasattr(step, 'testId') else step.get("testId", "unknown")
                step_id = step.stepId if hasattr(step, 'stepId') else step.get("stepId", "UNKNOWN")
                
                message = (f"Test {test_id}, Step {step_id}: "
                          f"targetId '{target_id}' not found in targets")
                report.add_error(message)
                logger.warning("[CompletenessValidator] %s", message)
                return True
        
        return False
    
    def _validate_navigation_step(self, step: Any, report: ValidationReport):
        """Check that navigation steps have proper targets."""
        action = step.action if hasattr(step, 'action') else step.get("action", "unknown")
        
        if action != "navigate":
            return
        
        # Navigation steps must have either target.type=url or targetId
        has_target_url = False
        has_target_id = False
        
        if hasattr(step, 'target') or 'target' in step:
            target = step.target if hasattr(step, 'target') else step.get("target")
            if target:
                target_type = target.get("type") if isinstance(target, dict) else (
                    target.type if hasattr(target, 'type') else None
                )
                if target_type == "url":
                    has_target_url = True
        
        target_id = step.targetId if hasattr(step, 'targetId') else step.get("targetId")
        if target_id:
            has_target_id = True
        
        if not has_target_url and not has_target_id:
            test_id = step.testId if hasattr(step, 'testId') else step.get("testId", "unknown")
            step_id = step.stepId if hasattr(step, 'stepId') else step.get("stepId", "UNKNOWN")
            
            message = (f"Test {test_id}, Step {step_id}: "
                      f"Navigation step must have target.type='url' or targetId")
            report.add_warning(message)
            logger.warning("[CompletenessValidator] %s", message)
    
    def _validate_step_input(self, step: Any, report: ValidationReport):
        """Check that step inputs are properly resolved."""
        action = step.action if hasattr(step, 'action') else step.get("action", "unknown")
        
        if action not in ("type", "select"):
            return
        
        # These actions should have input
        if not (hasattr(step, 'input') or 'input' in step):
            return
        
        step_input = step.input if hasattr(step, 'input') else step.get("input")
        if not step_input:
            return
        
        source = step_input.get("source") if isinstance(step_input, dict) else (
            step_input.source if hasattr(step_input, 'source') else None
        )
        
        if source == "data":
            field = step_input.get("field") if isinstance(step_input, dict) else (
                step_input.field if hasattr(step_input, 'field') else None
            )
            
            if not field:
                test_id = step.testId if hasattr(step, 'testId') else step.get("testId", "unknown")
                step_id = step.stepId if hasattr(step, 'stepId') else step.get("stepId", "UNKNOWN")
                
                message = (f"Test {test_id}, Step {step_id}: "
                          f"Data source input missing field name")
                report.add_warning(message)
    
    def _validate_assertions(self, step: Any, report: ValidationReport):
        """Check that assertions are valid."""
        if not (hasattr(step, 'assertions') or 'assertions' in step):
            return
        
        assertions = step.assertions if hasattr(step, 'assertions') else step.get("assertions", [])
        if not assertions:
            return
        
        for assertion in assertions:
            if isinstance(assertion, dict):
                expected = assertion.get("expectedValue")
                operator = assertion.get("operator")
            else:
                expected = assertion.expectedValue if hasattr(assertion, 'expectedValue') else None
                operator = assertion.operator if hasattr(assertion, 'operator') else None
            
            if not expected:
                test_id = step.testId if hasattr(step, 'testId') else step.get("testId", "unknown")
                step_id = step.stepId if hasattr(step, 'stepId') else step.get("stepId", "UNKNOWN")
                
                message = (f"Test {test_id}, Step {step_id}: "
                          f"Assertion missing expectedValue")
                report.add_warning(message)
