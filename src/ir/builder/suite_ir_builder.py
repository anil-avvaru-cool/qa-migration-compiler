import logging
from typing import Dict, List

from src.ir.models.suite import SuiteIR
from src.utils.hashing import deterministic_hash


logger = logging.getLogger(__name__)


class SuiteIRBuilder:
    """
    Builds SuiteIR from extracted suite structure.
    """

    def build(self, extracted_suite: Dict) -> SuiteIR:
        logger.info("Building SuiteIR for suite: %s", extracted_suite.get("name"))

        suite_name = extracted_suite["name"]
        suite_id = deterministic_hash(f"suite::{suite_name}")

        suite_ir = SuiteIR(
            id=suite_id,
            name=suite_name,
            parent_id=extracted_suite.get("parent_id"),
            tests=extracted_suite.get("tests", [])
        )

        logger.info("Finished building SuiteIR: %s", suite_id)
        return suite_ir
