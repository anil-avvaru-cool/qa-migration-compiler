import json
import os
import tempfile
import unittest
import logging

from src.parser.java.java_parser import JavaParser
from src.parser.java.java_ast_adapter import JavaASTAdapter
from src.extraction.extractor import IRExtractor
from src.ir.builder.project_ir_builder import ProjectIRBuilder
from src.ir.writer.file_writer import FileWriter
from src.core.pipeline import IRGenerationPipeline

logger = logging.getLogger(__name__)

class TestEndToEndPipeline(unittest.TestCase):

    def test_full_pipeline_generates_valid_ir_json(self):
        """
        True integration test:
        No mocks.
        """
       
        java_code = """
        import org.junit.Test;

        public class LoginTest {

            @Test
            public void ValidLogin() {
                System.out.println("Login success");
            }

            @Test
            public void InvalidLogin() {
                System.out.println("Login failed");
            }
           
        }
        """

        with tempfile.TemporaryDirectory() as tmpdir:
            # ----------------------------------------
            # 1️⃣ Write sample Java file
            # ----------------------------------------
            source_path = os.path.join(tmpdir, "LoginTest.java")
            with open(source_path, "w", encoding="utf-8") as f:
                f.write(java_code)

            output_path = os.path.join(tmpdir, "output_ir.json")

            # ----------------------------------------
            # 2️⃣ Build real pipeline components
            # ----------------------------------------
            parser = JavaParser()
            adapter = JavaASTAdapter()
            extractor = IRExtractor()
            ir_builder = ProjectIRBuilder()
            writer = FileWriter()

            pipeline = IRGenerationPipeline(
                parser=parser,
                adapter=adapter,
                extractor=extractor,
                ir_builder=ir_builder,
                writer=writer,
                # validator=None,
            )
            logger.debug(f"source_path: {source_path}")

            # ----------------------------------------
            # 3️⃣ Run pipeline
            # ----------------------------------------
            result = pipeline.run(
                project_name="demo-project",
                source_language="java",
                source_files=[source_path],
                output_path=output_path,
            )

            # pipeline now returns a dict with keys: project, tests, suites, targets, data, environments
            project_ir = result.get("project")

            logger.debug(f"Generated ProjectIR model: {project_ir}")

            # ----------------------------------------
            # 4️⃣ Validate output file exists
            # ----------------------------------------
            self.assertTrue(os.path.exists(output_path))

            # ----------------------------------------
            # 5️⃣ Load JSON
            # ----------------------------------------
            with open(output_path, "r", encoding="utf-8") as f:
                ir_json = json.load(f)

            # ----------------------------------------
            # 6️⃣ Structural validations
            # ----------------------------------------
            logger.debug("IR JSON content: %s", ir_json)

            # Project metadata is nested under 'project'
            metadata = ir_json.get("project", {}).get("metadata", {})

            self.assertEqual(metadata.get("name"), "demo-project")
            self.assertEqual(metadata.get("source_language"), "java")

            # Tests extracted (top-level 'tests' contains list of test IR objects)
            self.assertIn("tests", ir_json)
            self.assertEqual(len(ir_json["tests"]), 2)


if __name__ == "__main__":
    unittest.main()
