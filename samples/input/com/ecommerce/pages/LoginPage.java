package com.ecommerce.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

public class LoginPage extends BasePage {
    
    // Locators
    private By emailInput = By.id("email");
    private By passwordInput = By.id("password");
    private By loginButton = By.xpath("//button[@type='submit' and contains(text(), 'Login')]");
    private By rememberMeCheckbox = By.id("rememberMe");
    private By forgotPasswordLink = By.linkText("Forgot Password?");
    private By errorMessage = By.className("error-alert");
    private By loginPageTitle = By.xpath("//h1[text()='Sign In']");
    private By signUpLink = By.linkText("Create Account");
    
    public LoginPage(WebDriver driver) {
        super(driver);
    }
    
    public void navigateToLogin() {
        driver.get("https://ecommerce-app.localhost/login");
        waitForPageToLoad();
    }
    
    public void enterEmail(String email) {
        typeText(emailInput, email);
    }
    
    public void enterPassword(String password) {
        typeText(passwordInput, password);
    }
    
    public void clickRememberMe() {
        clickElement(rememberMeCheckbox);
    }
    
    public void clickLoginButton() {
        clickElement(loginButton);
    }
    
    public void clickForgotPassword() {
        clickElement(forgotPasswordLink);
    }
    
    public void clickSignUpLink() {
        clickElement(signUpLink);
    }
    
    public void login(String email, String password) {
        enterEmail(email);
        enterPassword(password);
        clickLoginButton();
    }
    
    public String getErrorMessage() {
        waitForElement(errorMessage);
        return getText(errorMessage);
    }
    
    public boolean isErrorMessageDisplayed() {
        return isElementDisplayed(errorMessage);
    }
    
    public boolean isLoginPageDisplayed() {
        return isElementDisplayed(loginPageTitle);
    }
    
    public String getLoginPageTitle() {
        return getPageTitle();
    }
}
