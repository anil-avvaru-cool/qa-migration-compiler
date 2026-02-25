import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from src.ir.models.project import ProjectIR, ProjectMetadata
from src.utils.hashing import deterministic_hash


logger = logging.getLogger(__name__)


class ProjectIRBuilder:
    """
    Builds ProjectIR as top-level IR container with enhanced schema.
    """

    def build(
        self,
        project_name: str,
        source_framework: str,
        target_framework: str,
        architecture_pattern: str = "POM",
        supports_parallel: bool = True,
        ir_version: str = "2.0.0",
        created_on: Optional[str] = None,
        source_language: Optional[str] = None,
        target_language: Optional[str] = None,
        suites: Optional[List[Dict[str, Any]]] = None,
        tests: Optional[List[Dict[str, Any]]] = None,
        environments: Optional[List[Dict[str, Any]]] = None,
        compiler_version: Optional[str] = None,
    ) -> ProjectIR:
        """
        Build ProjectIR with enhanced schema.
        
        Args:
            project_name: Project name
            source_framework: Source framework (e.g., Selenium-Java-TestNG)
            target_framework: Target framework (e.g., Playwright-TS)
            architecture_pattern: Architecture pattern (default: POM)
            supports_parallel: Whether parallel execution is supported
            ir_version: IR schema version
            created_on: Creation date (YYYY-MM-DD format, defaults to today)
            source_language: Source language (used in metadata)
            target_language: Target language (used in metadata)
            suites: Optional list of suite objects
            tests: Optional list of test objects
            environments: Optional list of environment objects
            compiler_version: Compiler version string
        """
        logger.info("Building ProjectIR for project: %s", project_name)

        if created_on is None:
            created_on = datetime.now().strftime("%Y-%m-%d")

        # Generate a deterministic project ID
        project_id = deterministic_hash(f"project::{project_name}")

        # Generate timestamp for IR generation
        generated_at = datetime.now().isoformat()

        # Create metadata
        metadata = ProjectMetadata(
            name=project_name,
            source_language=source_language or source_framework,
            target_language=target_language or target_framework,
            version="1.0.0",
            generated_at=generated_at,
            compiler_version=compiler_version or ir_version,
        )

        project_ir = ProjectIR(
            id=project_id,
            irVersion=ir_version,
            projectName=project_name,
            sourceFramework=source_framework,
            targetFramework=target_framework,
            architecturePattern=architecture_pattern,
            supportsParallel=supports_parallel,
            createdOn=created_on,
            metadata=metadata,
            suites=suites or [],
            tests=tests or [],
            environments=environments or [],
        )

        logger.info("Finished building ProjectIR: %s", project_name)
        return project_ir


