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
            public void testValidLogin() {
                System.out.println("Login success");
            }

            @Test
            public void testInvalidLogin() {
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

            # ----------------------------------------
            # 3️⃣ Run pipeline
            # ----------------------------------------
            project_ir = pipeline.run(
                project_name="demo-project",
                source_language="java",
                source_files=[source_path],
                output_path=output_path,
            )

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

            # Project metadata
            self.assertEqual(ir_json["projectName"], "demo-project")
            self.assertEqual(ir_json["sourceLanguage"], "java")

            # Tests extracted
            self.assertIn("tests", ir_json)
            self.assertEqual(len(ir_json["tests"]), 2)

            # Validate test names present
            test_names = [t["name"] for t in ir_json["tests"]]
            self.assertIn("testValidLogin", test_names)
            self.assertIn("testInvalidLogin", test_names)

            # Suites present (may be class-based suite)
            self.assertIn("suites", ir_json)

            # Environments present (may be empty in MVP)
            self.assertIn("environments", ir_json)

            # Compiler version present
            self.assertIn("compilerVersion", ir_json)

            # ----------------------------------------
            # 7️⃣ Deterministic ordering check
            # ----------------------------------------
            # Re-run pipeline and compare JSON equality

            pipeline.run(
                project_name="demo-project",
                source_language="java",
                source_files=[source_path],
                output_path=output_path,
            )

            with open(output_path, "r", encoding="utf-8") as f:
                ir_json_second_run = json.load(f)

            self.assertEqual(ir_json, ir_json_second_run)

            # ----------------------------------------
            # 8️⃣ Model integrity
            # ----------------------------------------
            # Ensure returned model matches file
            self.assertEqual(project_ir.model_dump(), ir_json)


if __name__ == "__main__":
    unittest.main()
