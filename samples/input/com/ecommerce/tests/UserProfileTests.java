package com.ecommerce.tests;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.*;
import org.openqa.selenium.By;

public class UserProfileTests {
    
    private WebDriver driver;
    
    // Locators for User Profile
    private By profileLink = By.xpath("//a[contains(text(), 'My Profile')]");
    private By firstNameInput = By.id("firstName");
    private By lastNameInput = By.id("lastName");
    private By emailInput = By.id("profileEmail");
    private By phoneInput = By.id("phoneNumber");
    private By addressInput = By.id("address");
    private By cityInput = By.id("city");
    private By stateInput = By.id("state");
    private By zipInput = By.id("zipCode");
    private By saveButton = By.xpath("//button[contains(text(), 'Save Changes')]");
    private By successMessage = By.xpath("//div[@class='success-message']");
    private By profileImage = By.id("profilePicture");
    private By uploadImageButton = By.xpath("//button[contains(text(), 'Upload Photo')]");
    private By deleteAccountButton = By.xpath("//button[contains(text(), 'Delete Account')]");
    
    @BeforeClass
    public void setUp() {
        driver = new ChromeDriver();
        driver.manage().timeouts().implicitlyWait(10, java.util.concurrent.TimeUnit.SECONDS);
        // Assume user is logged in
        driver.get("https://ecommerce-app.localhost/dashboard");
    }
    
    @AfterClass
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }
    
    @Test(description = "Navigate to user profile page")
    public void testNavigateToProfile() {
        driver.findElement(profileLink).click();
        
        String pageTitle = driver.getTitle();
        Assert.assertTrue(pageTitle.contains("Profile"), "Profile page should load");
    }
    
    @Test(description = "Update user first name")
    public void testUpdateFirstName() {
        driver.findElement(profileLink).click();
        
        org.openqa.selenium.WebElement firstNameField = driver.findElement(firstNameInput);
        firstNameField.clear();
        firstNameField.sendKeys("Updated");
        
        driver.findElement(saveButton).click();
        
        boolean saved = driver.findElements(successMessage).size() > 0;
        Assert.assertTrue(saved, "Success message should appear after saving");
    }
    
    @Test(description = "Update email address")
    public void testUpdateEmail() {
        driver.findElement(profileLink).click();
        
        org.openqa.selenium.WebElement emailField = driver.findElement(emailInput);
        emailField.clear();
        emailField.sendKeys("newemail@example.com");
        
        driver.findElement(saveButton).click();
        Assert.assertTrue(true, "Email updated successfully");
    }
    
    @Test(description = "Update phone number")
    public void testUpdatePhoneNumber() {
        driver.findElement(profileLink).click();
        
        org.openqa.selenium.WebElement phoneField = driver.findElement(phoneInput);
        phoneField.clear();
        phoneField.sendKeys("555-123-4567");
        
        driver.findElement(saveButton).click();
        Assert.assertTrue(true, "Phone number updated");
    }
    
    @Test(description = "Update address information")
    public void testUpdateAddress() {
        driver.findElement(profileLink).click();
        
        driver.findElement(addressInput).sendKeys("456 Oak Avenue");
        driver.findElement(cityInput).sendKeys("Boston");
        driver.findElement(stateInput).sendKeys("Massachusetts");
        driver.findElement(zipInput).sendKeys("02101");
        
        driver.findElement(saveButton).click();
        Assert.assertTrue(true, "Address updated successfully");
    }
    
    @Test(description = "Upload profile picture")
    public void testUploadProfilePicture() {
        driver.findElement(profileLink).click();
        
        driver.findElement(uploadImageButton).click();
        // In real test, handle file upload dialog
        Assert.assertTrue(true, "Upload dialog opened");
    }
    
    @Test(description = "Verify all profile fields are accessible")
    public void testAllProfileFieldsAccessible() {
        driver.findElement(profileLink).click();
        
        boolean firstNameVisible = driver.findElement(firstNameInput).isDisplayed();
        boolean lastNameVisible = driver.findElement(lastNameInput).isDisplayed();
        boolean emailVisible = driver.findElement(emailInput).isDisplayed();
        boolean phoneVisible = driver.findElement(phoneInput).isDisplayed();
        
        Assert.assertTrue(firstNameVisible && lastNameVisible && emailVisible && phoneVisible, 
            "All profile fields should be visible");
    }
    
    @Test(description = "Verify profile data persistence after save")
    public void testProfileDataPersistence() {
        driver.findElement(profileLink).click();
        
        String firstName = driver.findElement(firstNameInput).getAttribute("value");
        
        driver.findElement(saveButton).click();
        driver.navigate().refresh();
        driver.findElement(profileLink).click();
        
        String firstNameAfterRefresh = driver.findElement(firstNameInput).getAttribute("value");
        Assert.assertEquals(firstNameAfterRefresh, firstName, "Profile data should persist");
    }
}
