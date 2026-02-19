import logging
from src.extraction.action_mapper import ActionMapper
from src.parser.java.java_parser import JavaParser
from src.parser.java.java_ast_adapter import JavaASTAdapter

logger = logging.getLogger(__name__)

def test_action_mapper_extraction(tmp_path):
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

    tree = adapter.adapt(parser.parse(str(file_path)), str(file_path))

    actionMapper = ActionMapper()
    actions = actionMapper.map(tree)
    logger.debug(f"Extracted actions: {actions}")

    assert len(actions) == 3
    assert actions[0]["action"] == "sendKeys"
    assert actions[1]["action"] == "sendKeys"
    assert actions[2]["action"] == "click"