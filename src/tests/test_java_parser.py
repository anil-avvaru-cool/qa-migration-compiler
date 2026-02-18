import tempfile
from pathlib import Path

from src.parser.java.java_parser import JavaParser


SIMPLE_JAVA = """
public class LoginTest {
    public void testLogin() {
        System.out.println("Hello");
    }
}
"""


def test_java_parser_returns_compilation_unit():
    with tempfile.TemporaryDirectory() as tmp:
        file_path = Path(tmp) / "LoginTest.java"
        file_path.write_text(SIMPLE_JAVA)

        parser = JavaParser()
        compilation_unit = parser.parse(str(file_path))

        # Basic sanity checks
        assert compilation_unit is not None
        assert hasattr(compilation_unit, "types")
        assert len(compilation_unit.types) == 1
