import unittest
from unittest.mock import Mock

from src.core.pipeline import IRGenerationPipeline


class TestIRGenerationPipeline(unittest.TestCase):

    def test_pipeline_happy_path(self):
        # Mocks
        parser = Mock()
        adapter = Mock()
        extractor = Mock()
        builder = Mock()
        writer = Mock()

        parser.parse.return_value = "compilation_unit"
        adapter.adapt.return_value = "ast_tree"

        extraction_result = Mock()
        extraction_result.tests = ["T1"]
        extraction_result.suites = ["S1"]
        extraction_result.environments = ["E1"]
        extractor.extract.return_value = extraction_result

        builder.build.return_value = Mock(model_dump=lambda: {"project": "ok"})

        pipeline = IRGenerationPipeline(
            parser=parser,
            adapter=adapter,
            extractor=extractor,
            ir_builder=builder,
            writer=writer,
            validator=None,
        )

        result = pipeline.run(
            project_name="demo",
            source_language="java",
            source_files=["a.java"],
            output_path="output.json",
        )

        parser.parse.assert_called_once()
        adapter.adapt.assert_called_once()
        extractor.extract.assert_called_once()
        builder.build.assert_called_once()
        writer.write.assert_called_once()

        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
