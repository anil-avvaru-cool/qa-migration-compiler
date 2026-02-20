import logging
from datetime import datetime
from typing import Dict, List

from src.ir.models.project import ProjectIR, ProjectMetadata
from src.utils.hashing import deterministic_hash


logger = logging.getLogger(__name__)


class ProjectIRBuilder:
    """
    Builds ProjectIR as top-level IR container.
    """

    def build(
        self,
        project_name: str,
        source_language: str,
        tests: List[str],
        suites: List[str],
        environments: List[str],
        compiler_version: str = "0.1.0",
    ) -> ProjectIR:

        logger.info("Building ProjectIR for project: %s", project_name)

        project_id = deterministic_hash(f"project::{project_name}")

        metadata = ProjectMetadata(
            name=project_name,
            version="1.0.0",
            generated_at=datetime.utcnow(),
            source_language=source_language,
            compiler_version=compiler_version,
        )

        project_ir = ProjectIR(
            id=project_id,
            metadata=metadata,
            environments=environments,
            suites=suites,
            tests=tests,
        )

        logger.info("Finished building ProjectIR: %s", project_id)
        return project_ir
