import logging
from typing import Dict, List, Optional

from src.ir.models.suite import SuiteIR


logger = logging.getLogger(__name__)


class SuiteIRBuilder:
    """
    Builds SuiteIR from extracted suite structure or directly from arguments.
    """

    def build(
        self,
        suite_id: Optional[str] = None,
        tests: Optional[List[str]] = None,
        description: Optional[str] = None,
        extracted_suite: Optional[Dict] = None,
    ) -> SuiteIR:
        """
        Build SuiteIR.
        
        Supports two calling patterns:
        1. Direct: build(suite_id="S1", tests=["t1"], description="Desc")
        2. Backward-compatible: build(extracted_suite={"id": "S1", "tests": ["t1"]})
        3. Positional dict: build({"id": "S1", "tests": ["t1"]})
        
        Args:
            suite_id: Unique suite identifier
            tests: List of test IDs in this suite
            description: Optional suite description
            extracted_suite: Optional extracted suite dict (for backward compatibility)
        """
        # Handle backward compatibility: if suite_id is a dict, treat it as extracted_suite
        if isinstance(suite_id, dict):
            extracted_suite = suite_id
            suite_id = None
            tests = None
        
        logger.info("Building SuiteIR for suite: %s", suite_id)

        # Support both direct construction and extracted dict
        if extracted_suite:
            suite_id = extracted_suite.get("id") or extracted_suite.get("name") or suite_id
            tests = extracted_suite.get("tests", tests or [])
            description = extracted_suite.get("description", description)

        suite_ir = SuiteIR(
            suiteId=suite_id,
            description=description,
            tests=tests,
        )

        logger.info("Finished building SuiteIR: %s", suite_id)
        return suite_ir
