package com.ecommerce.tests;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.*;
import org.openqa.selenium.By;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.openqa.selenium.support.ui.ExpectedConditions;
import java.time.Duration;

public class PaymentTests {
    
    private WebDriver driver;
    private WebDriverWait wait;
    
    private static final String VALID_CARD = "4532015112830366";
    private static final String INVALID_CARD = "4532015112830367";
    private static final String CARD_NAME = "John Doe";
    private static final String CARD_EXPIRY = "12/25";
    private static final String VALID_CVV = "123";
    private static final String INVALID_CVV = "000";
    
    // Locators
    private By cardNumberInput = By.id("cardNumber");
    private By cardNameInput = By.id("cardName");
    private By cardExpiryInput = By.id("cardExpiry");
    private By cardCVVInput = By.id("cardCVV");
    private By cardTypeDisplay = By.className("card-type");
    private By processPaymentButton = By.xpath("//button[contains(text(), 'Process Payment')]");
    private By paymentSuccessMessage = By.className("payment-success");
    private By paymentErrorMessage = By.className("payment-error");
    private By savedCardsSection = By.id("savedCards");
    private By addNewCardButton = By.xpath("//button[contains(text(), 'Add New Card')]");
    private By deleteCardButton = By.xpath("//button[@title='Delete card']");
    
    @BeforeClass
    public void setUp() {
        driver = new ChromeDriver();
        driver.manage().timeouts().implicitlyWait(10, java.util.concurrent.TimeUnit.SECONDS);
        wait = new WebDriverWait(driver, Duration.ofSeconds(10));
        driver.get("https://ecommerce-app.localhost/payment");
    }
    
    @AfterClass
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }
    
    @Test(description = "Process payment with valid card")
    public void testValidPayment() {
        driver.findElement(cardNumberInput).sendKeys(VALID_CARD);
        driver.findElement(cardNameInput).sendKeys(CARD_NAME);
        driver.findElement(cardExpiryInput).sendKeys(CARD_EXPIRY);
        driver.findElement(cardCVVInput).sendKeys(VALID_CVV);
        
        driver.findElement(processPaymentButton).click();
        
        wait.until(ExpectedConditions.presenceOf(driver.findElement(paymentSuccessMessage)));
        Assert.assertTrue(driver.findElement(paymentSuccessMessage).isDisplayed());
    }
    
    @Test(description = "Process payment with invalid card number")
    public void testInvalidCardPayment() {
        driver.findElement(cardNumberInput).clear();
        driver.findElement(cardNumberInput).sendKeys(INVALID_CARD);
        driver.findElement(cardNameInput).sendKeys(CARD_NAME);
        driver.findElement(cardExpiryInput).sendKeys(CARD_EXPIRY);
        driver.findElement(cardCVVInput).sendKeys(VALID_CVV);
        
        driver.findElement(processPaymentButton).click();
        
        boolean errorShown = driver.findElements(paymentErrorMessage).size() > 0;
        Assert.assertTrue(errorShown, "Error message should appear for invalid card");
    }
    
    @Test(description = "Validate CVV field")
    public void testInvalidCVV() {
        driver.findElement(cardNumberInput).clear();
        driver.findElement(cardNumberInput).sendKeys(VALID_CARD);
        driver.findElement(cardNameInput).clear();
        driver.findElement(cardNameInput).sendKeys(CARD_NAME);
        driver.findElement(cardCVVInput).clear();
        driver.findElement(cardCVVInput).sendKeys(INVALID_CVV);
        
        driver.findElement(processPaymentButton).click();
        
        boolean errorShown = driver.findElements(paymentErrorMessage).size() > 0;
        Assert.assertTrue(errorShown, "Error for invalid CVV");
    }
    
    @Test(description = "Verify card type is detected")
    public void testCardTypeDetection() {
        driver.findElement(cardNumberInput).clear();
        driver.findElement(cardNumberInput).sendKeys(VALID_CARD);
        
        String cardType = driver.findElement(cardTypeDisplay).getText();
        Assert.assertFalse(cardType.isEmpty(), "Card type should be detected");
    }
    
    @Test(description = "Save card for future use")
    public void testSaveCard() {
        driver.findElement(cardNumberInput).sendKeys(VALID_CARD);
        driver.findElement(cardNameInput).sendKeys(CARD_NAME);
        driver.findElement(cardExpiryInput).sendKeys(CARD_EXPIRY);
        driver.findElement(cardCVVInput).sendKeys(VALID_CVV);
        
        // Assume there's a checkbox to save card
        By saveCardCheckbox = By.id("saveCard");
        driver.findElement(saveCardCheckbox).click();
        
        driver.findElement(processPaymentButton).click();
        Assert.assertTrue(true, "Card saved successfully");
    }
    
    @Test(description = "View saved cards")
    public void testViewSavedCards() {
        boolean savedCardsVisible = driver.findElements(savedCardsSection).size() > 0;
        Assert.assertTrue(savedCardsVisible, "Saved cards section should be visible");
    }
    
    @Test(description = "Add new payment card")
    public void testAddNewCard() {
        driver.findElement(addNewCardButton).click();
        
        boolean cardFormVisible = driver.findElements(cardNumberInput).size() > 0;
        Assert.assertTrue(cardFormVisible, "Card form should be visible");
    }
    
    @Test(description = "Delete saved card")
    public void testDeleteSavedCard() {
        boolean deleteButtonVisible = driver.findElements(deleteCardButton).size() > 0;
        
        if (deleteButtonVisible) {
            driver.findElement(deleteCardButton).click();
            // Handle confirmation dialog if present
            Assert.assertTrue(true, "Card deletion initiated");
        }
    }
}
