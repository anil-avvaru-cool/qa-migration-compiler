package com.ecommerce.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import java.util.List;

public class ProductPage extends BasePage {
    
    // Locators
    private By searchInput = By.id("searchBox");
    private By searchButton = By.xpath("//button[@id='searchBtn']");
    private By productResults = By.xpath("//div[@class='product-card']");
    private By productName = By.className("product-name");
    private By productPrice = By.className("product-price");
    private By productRating = By.className("product-rating");
    private By filterByCategoryDropdown = By.id("categoryFilter");
    private By filterByPriceInput = By.id("priceFilter");
    private By sortDropdown = By.id("sortBy");
    private By addToCartButton = By.xpath("//button[contains(text(), 'Add to Cart')]");
    private By noResultsMessage = By.xpath("//span[text()='No products found']");
    private By productDetails = By.className("product-detail-panel");
    
    public ProductPage(WebDriver driver) {
        super(driver);
    }
    
    public void navigateToProducts() {
        driver.get("https://ecommerce-app.localhost/products");
        waitForPageToLoad();
    }
    
    public void searchProduct(String productName) {
        typeText(searchInput, productName);
        clickElement(searchButton);
    }
    
    public int getProductCount() {
        List<WebElement> products = driver.findElements(productResults);
        return products.size();
    }
    
    public void selectProductByName(String name) {
        By productLocator = By.xpath("//div[@class='product-card']//span[contains(text(), '" + name + "')]");
        clickElement(productLocator);
    }
    
    public String getFirstProductName() {
        waitForElement(productName);
        return getText(productName);
    }
    
    public String getFirstProductPrice() {
        return getText(productPrice);
    }
    
    public void filterByCategory(String category) {
        clickElement(filterByCategoryDropdown);
        By categoryOption = By.xpath("//option[contains(text(), '" + category + "')]");
        clickElement(categoryOption);
    }
    
    public void sortBy(String sortOption) {
        clickElement(sortDropdown);
        By option = By.xpath("//option[contains(text(), '" + sortOption + "')]");
        clickElement(option);
    }
    
    public void addFirstProductToCart() {
        clickElement(addToCartButton);
    }
    
    public boolean isNoResultsMessageDisplayed() {
        return isElementDisplayed(noResultsMessage);
    }
    
    public boolean isProductDetailsDisplayed() {
        return isElementDisplayed(productDetails);
    }
    
    public String getProductRating() {
        return getText(productRating);
    }
}
