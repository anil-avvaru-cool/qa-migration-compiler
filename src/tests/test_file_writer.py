import json
import os
import tempfile
import unittest

from src.ir.writer.file_writer import FileWriter


class TestFileWriter(unittest.TestCase):

    def test_write_creates_file_and_serializes_json(self):
        writer = FileWriter()

        data = {
            "b": 2,
            "a": 1,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "ir.json")

            writer.write(path, data)

            self.assertTrue(os.path.exists(path))

            with open(path, "r", encoding="utf-8") as f:
                content = json.load(f)

            # Validate structure preserved
            self.assertEqual(content["a"], 1)
            self.assertEqual(content["b"], 2)

    def test_write_raises_on_non_serializable(self):
        writer = FileWriter()

        class NonSerializable:
            pass

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "ir.json")

            with self.assertRaises(TypeError):
                writer.write(path, {"bad": NonSerializable()})


if __name__ == "__main__":
    unittest.main()
