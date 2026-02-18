import tempfile
from pathlib import Path

from src.parser.java.java_parser import JavaParser
from src.parser.java.java_ast_adapter import JavaASTAdapter


SIMPLE_JAVA = """
public class LoginTest {
    public void testLogin() {
        System.out.println("Hello");
    }
}
"""


def test_java_ast_adapter_builds_ast_tree():
    with tempfile.TemporaryDirectory() as tmp:
        file_path = Path(tmp) / "LoginTest.java"
        file_path.write_text(SIMPLE_JAVA)

        parser = JavaParser()
        compilation_unit = parser.parse(str(file_path))

        adapter = JavaASTAdapter()
        tree = adapter.adapt(
            compilation_unit,
            file_path=str(file_path),           
        )

        # --- Tree metadata ---
        assert tree.language == "java"
        assert tree.file_path == str(file_path)

        # --- Root validation ---
        assert tree.root is not None
        assert tree.root.type == "CompilationUnit"

        # --- Structural integrity ---
        assert len(tree.root.children) > 0

        # --- Deterministic ID check ---
        assert tree.root.id.endswith("_1")

        # --- Parent wiring check ---
        for child in tree.root.children:
            assert child.parent_id == tree.root.id
