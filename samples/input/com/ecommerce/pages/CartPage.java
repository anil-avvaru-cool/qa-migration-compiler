package com.ecommerce.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import java.util.List;

public class CartPage extends BasePage {
    
    // Locators
    private By cartItems = By.xpath("//tr[@class='cart-item']");
    private By cartItemName = By.xpath(".//td[@class='item-name']");
    private By cartItemPrice = By.xpath(".//td[@class='item-price']");
    private By cartItemQuantity = By.xpath(".//input[@class='quantity']");
    private By removeItemButton = By.xpath(".//button[@title='Remove item']");
    private By subtotalAmount = By.id("subtotal");
    private By taxAmount = By.id("tax");
    private By totalAmount = By.id("total");
    private By proceedToCheckoutButton = By.xpath("//button[contains(text(), 'Proceed to Checkout')]");
    private By continueShopping = By.xpath("//a[contains(text(), 'Continue Shopping')]");
    private By emptyCartMessage = By.xpath("//p[text()='Your cart is empty']");
    private By applyCouponInput = By.id("couponCode");
    private By applyCouponButton = By.xpath("//button[contains(text(), 'Apply Coupon')]");
    private By discountAmount = By.id("discount");
    
    public CartPage(WebDriver driver) {
        super(driver);
    }
    
    public void navigateToCart() {
        driver.get("https://ecommerce-app.localhost/cart");
        waitForPageToLoad();
    }
    
    public int getCartItemCount() {
        List<WebElement> items = driver.findElements(cartItems);
        return items.size();
    }
    
    public void updateItemQuantity(int itemIndex, int quantity) {
        List<WebElement> items = driver.findElements(cartItems);
        if (itemIndex < items.size()) {
            WebElement quantityInput = items.get(itemIndex).findElement(cartItemQuantity);
            quantityInput.clear();
            quantityInput.sendKeys(String.valueOf(quantity));
        }
    }
    
    public void removeItem(int itemIndex) {
        List<WebElement> items = driver.findElements(cartItems);
        if (itemIndex < items.size()) {
            WebElement removeBtn = items.get(itemIndex).findElement(removeItemButton);
            removeBtn.click();
        }
    }
    
    public String getSubtotal() {
        return getText(subtotalAmount);
    }
    
    public String getTax() {
        return getText(taxAmount);
    }
    
    public String getTotal() {
        return getText(totalAmount);
    }
    
    public void proceedToCheckout() {
        clickElement(proceedToCheckoutButton);
    }
    
    public void continueShopping() {
        clickElement(continueShopping);
    }
    
    public boolean isCartEmpty() {
        return isElementDisplayed(emptyCartMessage);
    }
    
    public void applyCoupon(String couponCode) {
        typeText(applyCouponInput, couponCode);
        clickElement(applyCouponButton);
    }
    
    public String getDiscount() {
        return getText(discountAmount);
    }
    
    public String getFirstItemName() {
        List<WebElement> items = driver.findElements(cartItems);
        if (items.size() > 0) {
            return items.get(0).findElement(cartItemName).getText();
        }
        return "";
    }
}
