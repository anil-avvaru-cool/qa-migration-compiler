import logging
from datetime import datetime
from typing import Optional

from src.ir.models.project import ProjectIR


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
        """
        logger.info("Building ProjectIR for project: %s", project_name)

        if created_on is None:
            created_on = datetime.now().strftime("%Y-%m-%d")

        project_ir = ProjectIR(
            irVersion=ir_version,
            projectName=project_name,
            sourceFramework=source_framework,
            targetFramework=target_framework,
            architecturePattern=architecture_pattern,
            supportsParallel=supports_parallel,
            createdOn=created_on,
        )

        logger.info("Finished building ProjectIR: %s", project_name)
        return project_ir
