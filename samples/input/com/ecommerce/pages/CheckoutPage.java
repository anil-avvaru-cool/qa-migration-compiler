package com.ecommerce.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

public class CheckoutPage extends BasePage {
    
    // Locators - Shipping Section
    private By shippingAddressInput = By.id("shippingAddress");
    private By shippingCityInput = By.id("shippingCity");
    private By shippingStateInput = By.id("shippingState");
    private By shippingZipInput = By.id("shippingZip");
    private By shippingCountrySelect = By.id("shippingCountry");
    
    // Locators - Billing Section
    private By billingSameAsShipping = By.id("billingSameAsShipping");
    private By billingAddressInput = By.id("billingAddress");
    private By billingCityInput = By.id("billingCity");
    
    // Locators - Shipping Method
    private By standardShippingRadio = By.id("standard");
    private By expressShippingRadio = By.id("express");
    private By overnightShippingRadio = By.id("overnight");
    private By shippingCost = By.className("shipping-cost");
    
    // Locators - Payment Section
    private By cardNumberInput = By.id("cardNumber");
    private By cardNameInput = By.id("cardName");
    private By cardExpiryInput = By.id("cardExpiry");
    private By cardCVVInput = By.id("cardCVV");
    private By placeOrderButton = By.xpath("//button[contains(text(), 'Place Order')]");
    private By orderConfirmation = By.xpath("//div[@class='order-confirmation']");
    private By orderNumber = By.className("order-number");
    private By estimatedDelivery = By.className("estimated-delivery");
    
    public CheckoutPage(WebDriver driver) {
        super(driver);
    }
    
    public void navigateToCheckout() {
        driver.get("https://ecommerce-app.localhost/checkout");
        waitForPageToLoad();
    }
    
    // Shipping methods
    public void enterShippingAddress(String address, String city, String state, String zip) {
        typeText(shippingAddressInput, address);
        typeText(shippingCityInput, city);
        typeText(shippingStateInput, state);
        typeText(shippingZipInput, zip);
    }
    
    public void selectShippingCountry(String country) {
        clickElement(shippingCountrySelect);
        By countryOption = By.xpath("//option[contains(text(), '" + country + "')]");
        clickElement(countryOption);
    }
    
    public void useBillingAddressAsSameAsShipping() {
        clickElement(billingSameAsShipping);
    }
    
    public void selectStandardShipping() {
        clickElement(standardShippingRadio);
    }
    
    public void selectExpressShipping() {
        clickElement(expressShippingRadio);
    }
    
    public void selectOvernightShipping() {
        clickElement(overnightShippingRadio);
    }
    
    public String getShippingCost() {
        return getText(shippingCost);
    }
    
    // Payment methods
    public void enterCardDetails(String cardNumber, String cardName, String expiry, String cvv) {
        typeText(cardNumberInput, cardNumber);
        typeText(cardNameInput, cardName);
        typeText(cardExpiryInput, expiry);
        typeText(cardCVVInput, cvv);
    }
    
    public void placeOrder() {
        clickElement(placeOrderButton);
    }
    
    public boolean isOrderConfirmationDisplayed() {
        return isElementDisplayed(orderConfirmation);
    }
    
    public String getOrderNumber() {
        waitForElement(orderNumber);
        return getText(orderNumber);
    }
    
    public String getEstimatedDeliveryDate() {
        return getText(estimatedDelivery);
    }
    
    public void completeCheckout(String address, String city, String state, String zip, 
                                 String country, String cardNumber, String cardName, 
                                 String expiry, String cvv) {
        enterShippingAddress(address, city, state, zip);
        selectShippingCountry(country);
        selectExpressShipping();
        useBillingAddressAsSameAsShipping();
        enterCardDetails(cardNumber, cardName, expiry, cvv);
        placeOrder();
    }
}
