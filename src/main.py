import logging
import json
import shutil
import os
from pathlib import Path
from typing import List

from src.parser.base_parser import BaseParser
from src.parser.java.java_parser import JavaParser
from src.parser.java.java_ast_adapter import JavaASTAdapter
from src.extraction.extractor import IRExtractor
from src.ir.builder.project_ir_builder import ProjectIRBuilder
from src.ir.writer.file_writer import FileWriter
from src.core.pipeline import IRGenerationPipeline

# Configure logging
app_log_file = "app.log"
if os.path.exists(app_log_file):
    os.remove(app_log_file)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()  # Also print to console
    ]
)

logger = logging.getLogger(__name__)


def discover_java_files(input_directory: str) -> List[str]:
    """
    Discover all .java files in the input directory recursively.
    
    Args:
        input_directory: Root directory to search
        
    Returns:
        List of absolute paths to .java files
    """
    java_files = []
    input_path = Path(input_directory)
    
    if not input_path.exists():
        logger.warning(f"Input directory does not exist: {input_directory}")
        return java_files
    
    for java_file in input_path.rglob("*.java"):
        java_files.append(str(java_file))
    
    logger.info(f"Discovered {len(java_files)} Java files in {input_directory}")
    return sorted(java_files)


def ensure_output_directory(output_directory: str) -> None:
    """Ensure output directory exists."""
    Path(output_directory).mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory ready: {output_directory}")


def run_ir_generation_pipeline():
    """
    Main entry point: discover Java files and run IR generation pipeline.
    """
    logger.info("=" * 80)
    logger.info("IR Generation Pipeline Starting")
    logger.info("=" * 80)
    
    try:
        # Configuration
        input_directory = "input/"
        output_directory = "output/"
        project_name = "ecommerce-qa"
        source_language = "Selenium-Java-TestNG"
        target_framework = "Cypress-TS"
        compiler_version = "1.0.0"
        
        # Discover source files
        logger.info(f"\n[Step 1/5] Discovering Java files in {input_directory}...")
        source_files = discover_java_files(input_directory)
        
        if not source_files:
            logger.error("No Java files found in input directory!")
            return
        
        logger.info(f"Found {len(source_files)} Java files")
        for file_path in source_files:
            logger.debug(f"  - {file_path}")
        
        # Ensure output directory exists
        logger.info(f"\n[Step 2/5] Preparing output directory...")
        ensure_output_directory(output_directory)
        logger.info(f"Output directory ready: {output_directory}")
        
        # Initialize pipeline components
        logger.info(f"\n[Step 3/5] Initializing pipeline components...")
        
        parser = JavaParser()
        adapter = JavaASTAdapter()
        extractor = IRExtractor()
        ir_builder = ProjectIRBuilder()
        writer = FileWriter()
        
        logger.info("Pipeline components initialized")
        
        # Create and run pipeline
        logger.info(f"\n[Step 4/5] Creating IR generation pipeline...")
        pipeline = IRGenerationPipeline(
            parser=parser,
            adapter=adapter,
            extractor=extractor,
            ir_builder=ir_builder,
            writer=writer
        )
        logger.info("Pipeline created")
        
        # Execute pipeline
        logger.info(f"\n[Step 5/5] Executing pipeline...")
        logger.info(f"  Project: {project_name}")
        logger.info(f"  Source Language: {source_language}")
        logger.info(f"  Target Framework: {target_framework}")
        logger.info(f"  Files to process: {len(source_files)}")
        
        pipeline.run(
            project_name=project_name,
            source_language=source_language,
            source_files=source_files,
            output_path=output_directory,
            target_framework=target_framework,
            compiler_version=compiler_version
        )
        
        logger.info("\n" + "=" * 80)
        logger.info("IR Generation Pipeline Completed Successfully!")
        logger.info("=" * 80)
        logger.info(f"\nOutput files generated in: {output_directory}")
        logger.info(f"Check {output_directory}/ir/ for the generated IR JSON files")
        logger.info(f"Check app.log for detailed execution logs\n")
        
    except Exception as e:
        logger.error(f"\n{'=' * 80}")
        logger.error(f"Pipeline failed with error:")
        logger.error(f"{'=' * 80}")
        logger.exception(e)
        raise


if __name__ == "__main__":
    run_ir_generation_pipeline()