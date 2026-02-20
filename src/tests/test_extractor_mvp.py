import logging
from src.extraction.extractor import IRExtractor
from src.ast.models import ASTNode, ASTTree
from src.parser.java.java_parser import JavaParser
from src.parser.java.java_ast_adapter import JavaASTAdapter

logger = logging.getLogger(__name__)

def test_extractor_basic_flow(tmp_path):

    java_code = """
    package tests;

    import base.BaseTest;
    import org.openqa.selenium.support.ui.ExpectedConditions;
    import org.testng.Assert;
    import org.testng.annotations.Test;
    import pages.HomePage;
    import pages.LoginPage;

    public class TC_LOGIN_VALID_001 extends BaseTest {

        @Test
        public void validLoginTest() {

            String username = "testuser1";
            String password = "Password123";
            String expectedMessage = "Welcome testuser1";

            driver.get(baseUrl + "/login");

            LoginPage loginPage = new LoginPage(driver);
            loginPage.enterUsername(username);
            loginPage.enterPassword(password);
            loginPage.clickLogin();

            HomePage homePage = new HomePage(driver);

            wait.until(ExpectedConditions.visibilityOfElementLocated(
                    homePage.getWelcomeLocator()
            ));

            String actualMessage = homePage.getWelcomeMessage();

            Assert.assertEquals(actualMessage, expectedMessage);
        }
    }
    """

    file_path = tmp_path / "LoginPage.java"
    file_path.write_text(java_code)

    parser = JavaParser()
    adapter = JavaASTAdapter()

    ast_tree = adapter.adapt(parser.parse(str(file_path)), str(file_path))

    extractor = IRExtractor()

    result = extractor.extract(
        ast_tree=ast_tree,
        project_name="DemoProject",
        source_language="java",
    )
    logger.debug(f"Extraction result: {result}")

    assert result["project_name"] == "DemoProject"
    assert len(result["tests"]) == 1
    #assert result["tests"][0]["name"] == "ValidLogin"
