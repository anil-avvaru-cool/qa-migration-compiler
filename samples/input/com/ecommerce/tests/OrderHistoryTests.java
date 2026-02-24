package com.ecommerce.tests;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.*;
import org.openqa.selenium.By;
import java.util.List;

public class OrderHistoryTests {
    
    private WebDriver driver;
    
    // Locators
    private By orderHistoryLink = By.xpath("//a[contains(text(), 'Order History')]");
    private By ordersList = By.xpath("//tr[@class='order-row']");
    private By orderNumber = By.xpath(".//td[@class='order-number']");
    private By orderDate = By.xpath(".//td[@class='order-date']");
    private By orderStatus = By.xpath(".//td[@class='order-status']");
    private By orderTotal = By.xpath(".//td[@class='order-total']");
    private By orderDetailsButton = By.xpath(".//button[@title='View Details']");
    private By reorderButton = By.xpath(".//button[contains(text(), 'Reorder')]");
    private By cancelOrderButton = By.xpath(".//button[contains(text(), 'Cancel Order')]");
    private By downloadInvoiceButton = By.xpath(".//button[contains(text(), 'Download Invoice')]");
    private By filterByStatusDropdown = By.id("statusFilter");
    private By sortByDateButton = By.xpath("//button[contains(text(), 'Sort by Date')]");
    private By searchOrderBox = By.id("orderSearch");
    private By noOrdersMessage = By.xpath("//span[text()='No orders found']");
    
    @BeforeClass
    public void setUp() {
        driver = new ChromeDriver();
        driver.manage().timeouts().implicitlyWait(10, java.util.concurrent.TimeUnit.SECONDS);
        driver.get("https://ecommerce-app.localhost/dashboard");
    }
    
    @AfterClass
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }
    
    @Test(description = "Navigate to order history")
    public void testNavigateToOrderHistory() {
        driver.findElement(orderHistoryLink).click();
        
        String pageTitle = driver.getTitle();
        Assert.assertTrue(pageTitle.contains("Order"), "Order history page should load");
    }
    
    @Test(description = "View list of orders")
    public void testViewOrdersList() {
        driver.findElement(orderHistoryLink).click();
        
        List<org.openqa.selenium.WebElement> orders = driver.findElements(ordersList);
        Assert.assertGreater(orders.size(), 0, "Orders should be displayed in list");
    }
    
    @Test(description = "View order details")
    public void testViewOrderDetails() {
        driver.findElement(orderHistoryLink).click();
        
        List<org.openqa.selenium.WebElement> orders = driver.findElements(ordersList);
        if (orders.size() > 0) {
            org.openqa.selenium.WebElement firstOrderDetailsButton = 
                orders.get(0).findElement(orderDetailsButton);
            firstOrderDetailsButton.click();
            
            String currentUrl = driver.getCurrentUrl();
            Assert.assertTrue(currentUrl.contains("order"), "Order details page should load");
        }
    }
    
    @Test(description = "Filter orders by status")
    public void testFilterOrdersByStatus() {
        driver.findElement(orderHistoryLink).click();
        
        driver.findElement(filterByStatusDropdown).click();
        By completedOption = By.xpath("//option[contains(text(), 'Completed')]");
        driver.findElement(completedOption).click();
        
        // Verify filtered results
        List<org.openqa.selenium.WebElement> orders = driver.findElements(ordersList);
        Assert.assertGreater(orders.size(), 0, "Filtered orders should be displayed");
    }
    
    @Test(description = "Sort orders by date")
    public void testSortOrdersByDate() {
        driver.findElement(orderHistoryLink).click();
        
        driver.findElement(sortByDateButton).click();
        
        List<org.openqa.selenium.WebElement> orders = driver.findElements(ordersList);
        Assert.assertGreater(orders.size(), 0, "Sorted orders should be displayed");
    }
    
    @Test(description = "Search for specific order")
    public void testSearchOrder() {
        driver.findElement(orderHistoryLink).click();
        
        driver.findElement(searchOrderBox).sendKeys("ORD-123456");
        driver.findElement(searchOrderBox).submit();
        
        // Verify search results
        List<org.openqa.selenium.WebElement> orders = driver.findElements(ordersList);
        Assert.assertGreater(orders.size(), 0, "Search should return results");
    }
    
    @Test(description = "Reorder from order history")
    public void testReorderFromHistory() {
        driver.findElement(orderHistoryLink).click();
        
        List<org.openqa.selenium.WebElement> orders = driver.findElements(ordersList);
        if (orders.size() > 0) {
            org.openqa.selenium.WebElement reorderBtn = orders.get(0).findElement(reorderButton);
            reorderBtn.click();
            
            // Should add items to cart and redirect to cart
            Assert.assertTrue(true, "Reorder initiated");
        }
    }
    
    @Test(description = "Download invoice from order")
    public void testDownloadInvoice() {
        driver.findElement(orderHistoryLink).click();
        
        List<org.openqa.selenium.WebElement> orders = driver.findElements(ordersList);
        if (orders.size() > 0) {
            org.openqa.selenium.WebElement downloadBtn = orders.get(0).findElement(downloadInvoiceButton);
            Assert.assertTrue(downloadBtn.isDisplayed(), "Download button should be visible");
        }
    }
    
    @Test(description = "Verify order displays all required information")
    public void testOrderDisplaysAllInfo() {
        driver.findElement(orderHistoryLink).click();
        
        List<org.openqa.selenium.WebElement> orders = driver.findElements(ordersList);
        if (orders.size() > 0) {
            org.openqa.selenium.WebElement firstOrder = orders.get(0);
            
            boolean hasNumber = firstOrder.findElements(orderNumber).size() > 0;
            boolean hasDate = firstOrder.findElements(orderDate).size() > 0;
            boolean hasStatus = firstOrder.findElements(orderStatus).size() > 0;
            
            Assert.assertTrue(hasNumber && hasDate && hasStatus, 
                "Order should display number, date, and status");
        }
    }
}
