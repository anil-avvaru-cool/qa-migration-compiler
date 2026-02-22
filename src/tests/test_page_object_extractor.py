import logging
from src.extraction.page_object_extractor import PageObjectExtractor
from src.parser.java.java_parser import JavaParser
from src.parser.java.java_ast_adapter import JavaASTAdapter

logger = logging.getLogger(__name__)

def test_page_object_extraction(tmp_path):
    java_code = """
    package pages;

    import org.openqa.selenium.By;
    import org.openqa.selenium.WebDriver;

    public class LoginPage {

        private WebDriver driver;

        private By username = By.cssSelector("#username");
        private By password = By.cssSelector("#password");
        private By loginButton = By.cssSelector("#login-btn");

        public LoginPage(WebDriver driver) {
            this.driver = driver;
        }

        public void enterUsername(String user) {
            driver.findElement(username).sendKeys(user);
        }

        public void enterPassword(String pass) {
            driver.findElement(password).sendKeys(pass);
        }

        public void clickLogin() {
            driver.findElement(loginButton).click();
        }
    }
    """

    file_path = tmp_path / "LoginPage.java"
    file_path.write_text(java_code)

    parser = JavaParser()
    adapter = JavaASTAdapter()

    ast_node = adapter.adapt(parser.parse(str(file_path)))
    from src.ast.models import ASTTree
    tree = ASTTree(root=ast_node, language="java", file_path=str(file_path))

    extractor = PageObjectExtractor()
    pages = extractor.extract(tree)
    logger.info(f"Extracted pages: {pages}")

    assert len(pages) == 1
    assert pages[0]["name"] == "LoginPage"
