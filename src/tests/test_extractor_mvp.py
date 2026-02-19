import pytest
from pathlib import Path

from src.extraction.extractor import IRExtractor
from src.ir.models.project import Project


def test_extractor_returns_project(tmp_path):
    # Minimal Java test sample
    java_code = """
    public class LoginTest {
        public void testLogin() {
            System.out.println("Hello");
        }
    }
    """

    file_path = tmp_path / "LoginTest.java"
    file_path.write_text(java_code)

    extractor = IRExtractor()
    result = extractor.extract(str(file_path))

    assert isinstance(result, Project)
    assert result is not None


def test_extractor_is_deterministic(tmp_path):
    java_code = """
    public class Sample {
        public void testA() {}
    }
    """

    file_path = tmp_path / "Sample.java"
    file_path.write_text(java_code)

    extractor = IRExtractor()

    r1 = extractor.extract(str(file_path))
    r2 = extractor.extract(str(file_path))

    assert r1.model_dump() == r2.model_dump()
