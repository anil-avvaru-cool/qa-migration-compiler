import logging
from src.extraction.assertion_mapper import AssertionMapper
from src.parser.java.java_parser import JavaParser
from src.parser.java.java_ast_adapter import JavaASTAdapter

logger = logging.getLogger(__name__)

def test_assertion_mapper_extracts_assert_methods(tmp_path):
    java_code = """
    import static org.junit.Assert.*;

    public class LoginTest {

        public void testLogin() {

            // action (should be ignored)
            driver.findElement(By.id("username")).click();

            // assertions
            assertTrue(true);
            Assert.assertEquals("expected", "actual");
            assertFalse(false);

            // non-assert (ignored)
            System.out.println("Hello");
        }
    }
    """

    file_path = tmp_path / "LoginTest.java"
    file_path.write_text(java_code)

    parser = JavaParser()
    adapter = JavaASTAdapter()

    tree = adapter.adapt(parser.parse(str(file_path)), str(file_path))

    mapper = AssertionMapper()
    assertions = mapper.map(tree)
    logger.debug(f"Extracted assertions: {assertions}")

    # Validate count
    assert len(assertions) == 3

    # Validate assertion names
    assertion_names = {a["assertion"] for a in assertions}

    assert "assertTrue" in assertion_names
    assert "assertEquals" in assertion_names
    assert "assertFalse" in assertion_names


def test_assertion_mapper_is_deterministic(tmp_path):
    java_code = """
    public class Sample {
        public void test() {
            assertTrue(true);
        }
    }
    """

    file_path = tmp_path / "Sample.java"
    file_path.write_text(java_code)

    parser = JavaParser()
    adapter = JavaASTAdapter()
    mapper = AssertionMapper()

    tree1 = adapter.adapt(parser.parse(str(file_path)), str(file_path))
    tree2 = adapter.adapt(parser.parse(str(file_path)), str(file_path))

    r1 = mapper.map(tree1)   

    r2 = mapper.map(tree2)

    assert r1 == r2
