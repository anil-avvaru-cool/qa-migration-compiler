import logging
from src.extraction.page_object_extractor import PageObjectExtractor
from src.parser.java.java_parser import JavaParser
from src.parser.java.java_ast_adapter import JavaASTAdapter

logger = logging.getLogger(__name__)

def test_page_object_extraction(tmp_path):
    java_code = """
    public class LoginPage {
        public void test() {}
    }
    """

    file_path = tmp_path / "LoginPage.java"
    file_path.write_text(java_code)

    parser = JavaParser()
    adapter = JavaASTAdapter()

    tree = adapter.adapt(parser.parse(str(file_path)), str(file_path))

    extractor = PageObjectExtractor()
    pages = extractor.extract(tree)
    logger.info(f"Extracted pages: {pages}")

    assert len(pages) == 1
    assert pages[0]["name"] == "LoginPage"
