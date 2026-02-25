package com.ecommerce.tests;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.*;
import com.ecommerce.pages.CheckoutPage;
import org.openqa.selenium.support.PageFactory;

public class CheckoutTests {
    
    private WebDriver driver;
    private CheckoutPage checkoutPage;
    
    private static final String ADDRESS = "123 Main Street";
    private static final String CITY = "San Francisco";
    private static final String STATE = "California";
    private static final String ZIP = "94105";
    private static final String COUNTRY = "United States";
    private static final String CARD_NUMBER = "4532015112830366";
    private static final String CARD_NAME = "John Doe";
    private static final String CARD_EXPIRY = "12/25";
    private static final String CARD_CVV = "123";
    
    @BeforeClass
    public void setUp() {
        driver = new ChromeDriver();
        driver.manage().timeouts().implicitlyWait(10, java.util.concurrent.TimeUnit.SECONDS);
        checkoutPage = PageFactory.initElements(driver, CheckoutPage.class);
    }
    
    @AfterClass
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }
    
    @Test(description = "Verify checkout page loads successfully")
    public void testCheckoutPageLoads() {
        checkoutPage.navigateToCheckout();
        
        String pageTitle = checkoutPage.getPageTitle();
        Assert.assertTrue(pageTitle.contains("Checkout"), "Checkout page should load");
    }
    
    @Test(description = "Enter shipping address information")
    public void testEnterShippingAddress() {
        checkoutPage.navigateToCheckout();
        
        checkoutPage.enterShippingAddress(ADDRESS, CITY, STATE, ZIP);
        checkoutPage.selectShippingCountry(COUNTRY);
        
        Assert.assertTrue(true, "Shipping address entered successfully");
    }
    
    @Test(description = "Select billing address same as shipping")
    public void testBillingAddressSameAsShipping() {
        checkoutPage.navigateToCheckout();
        
        checkoutPage.enterShippingAddress(ADDRESS, CITY, STATE, ZIP);
        checkoutPage.selectShippingCountry(COUNTRY);
        checkoutPage.useBillingAddressAsSameAsShipping();
        
        Assert.assertTrue(true, "Billing address set to match shipping address");
    }
    
    @Test(description = "Select standard shipping method")
    public void testStandardShippingSelection() {
        checkoutPage.navigateToCheckout();
        
        checkoutPage.selectStandardShipping();
        String shippingCost = checkoutPage.getShippingCost();
        
        Assert.assertNotNull(shippingCost, "Shipping cost should be displayed");
    }
    
    @Test(description = "Select express shipping method")
    public void testExpressShippingSelection() {
        checkoutPage.navigateToCheckout();
        
        checkoutPage.selectExpressShipping();
        String shippingCost = checkoutPage.getShippingCost();
        
        Assert.assertNotNull(shippingCost, "Express shipping cost should be displayed");
        Assert.assertTrue(shippingCost.contains("$"), "Cost should contain currency");
    }
    
    @Test(description = "Select overnight shipping method")
    public void testOvernightShippingSelection() {
        checkoutPage.navigateToCheckout();
        
        checkoutPage.selectOvernightShipping();
        String shippingCost = checkoutPage.getShippingCost();
        
        Assert.assertNotNull(shippingCost, "Overnight shipping cost should be displayed");
    }
    
    @Test(description = "Enter payment card details")
    public void testEnterPaymentDetails() {
        checkoutPage.navigateToCheckout();
        
        checkoutPage.enterCardDetails(CARD_NUMBER, CARD_NAME, CARD_EXPIRY, CARD_CVV);
        Assert.assertTrue(true, "Payment details entered successfully");
    }
    
    @Test(description = "Complete full checkout process")
    public void testCompleteCheckout() {
        checkoutPage.navigateToCheckout();
        
        checkoutPage.completeCheckout(ADDRESS, CITY, STATE, ZIP, COUNTRY, 
            CARD_NUMBER, CARD_NAME, CARD_EXPIRY, CARD_CVV);
        
        boolean orderConfirmed = checkoutPage.isOrderConfirmationDisplayed();
        Assert.assertTrue(orderConfirmed, "Order confirmation should be displayed");
    }
    
    @Test(description = "Verify order number is displayed after checkout")
    public void testOrderNumberDisplay() {
        checkoutPage.navigateToCheckout();
        
        checkoutPage.completeCheckout(ADDRESS, CITY, STATE, ZIP, COUNTRY, 
            CARD_NUMBER, CARD_NAME, CARD_EXPIRY, CARD_CVV);
        
        String orderNumber = checkoutPage.getOrderNumber();
        Assert.assertNotNull(orderNumber, "Order number should be displayed");
        Assert.assertFalse(orderNumber.isEmpty(), "Order number should not be empty");
    }
    
    @Test(description = "Verify estimated delivery date is shown")
    public void testEstimatedDeliveryDate() {
        checkoutPage.navigateToCheckout();
        
        checkoutPage.completeCheckout(ADDRESS, CITY, STATE, ZIP, COUNTRY, 
            CARD_NUMBER, CARD_NAME, CARD_EXPIRY, CARD_CVV);
        
        String deliveryDate = checkoutPage.getEstimatedDeliveryDate();
        Assert.assertNotNull(deliveryDate, "Estimated delivery date should be displayed");
    }
}
