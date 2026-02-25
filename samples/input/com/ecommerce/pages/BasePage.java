package com.ecommerce.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;

public class BasePage {
    protected WebDriver driver;
    protected WebDriverWait wait;
    
    private static final long TIMEOUT_SECONDS = 10;
    
    public BasePage(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(TIMEOUT_SECONDS));
    }
    
    // Locators
    protected By headerLogout = By.xpath("//header//button[contains(text(), 'Logout')]");
    protected By navigationMenu = By.id("navMenu");
    protected By userGreeting = By.className("user-welcome");
    protected By footerCopyright = By.xpath("//footer//span[@class='copyright']");
    
    // Helper methods
    public void navigateTo(String url) {
        driver.navigate().to(url);
    }
    
    public void waitForElement(By locator) {
        wait.until(ExpectedConditions.presenceOf(driver.findElement(locator)));
    }
    
    public void clickElement(By locator) {
        WebElement element = wait.until(ExpectedConditions.elementToBeClickable(locator));
        element.click();
    }
    
    public void typeText(By locator, String text) {
        WebElement element = wait.until(ExpectedConditions.presenceOf(driver.findElement(locator)));
        element.clear();
        element.sendKeys(text);
    }
    
    public String getText(By locator) {
        WebElement element = wait.until(ExpectedConditions.visibilityOf(driver.findElement(locator)));
        return element.getText();
    }
    
    public boolean isElementDisplayed(By locator) {
        try {
            return driver.findElement(locator).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }
    
    public void waitForPageToLoad() {
        wait.until(driver -> ((org.openqa.selenium.JavascriptExecutor) driver)
            .executeScript("return document.readyState").equals("complete"));
    }
    
    public String getPageTitle() {
        return driver.getTitle();
    }
    
    public String getCurrentUrl() {
        return driver.getCurrentUrl();
    }
    
    public void logout() {
        clickElement(headerLogout);
    }
}
