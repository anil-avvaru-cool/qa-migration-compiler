# Root Cause Analysis & Fix Summary: Steps Population Issue

## Executive Summary

**Problem:** Steps arrays were empty in test IR output  
**Root Cause:** Action mapper only recognized Selenium direct actions, not page object method calls  
**Solution:** Enhanced action mapper to recognize both Selenium actions AND page object method invocations  
**Status:** ✅ FIXED - All 32 tests pass, steps now correctly populated

---

## Detailed Root Cause Analysis

### The Problem

After IR generation, test steps were empty:
```json
{
  "tests": [
    {
      "id": "8a3e3a1b98ee",
      "name": "testCompleteCheckoutFlow",
      "steps": []  // ❌ EMPTY!
    }
  ],
  "targets": [...]  // ✅ Targets populated correctly
}
```

### Why Steps Were Empty

**Test Structure in QA Code:**

Tests call **page object methods**, not direct Selenium actions:
```java
@Test
public void testUserRegistrationWithValidCredentials() {
    loginPage.clickRegisterLink();       // ← Page object method call
    loginPage.enterFirstName("John");    // ← Page object method call
    loginPage.enterLastName("Doe");      // ← Page object method call
    loginPage.enterEmail("john@test.com");
    loginPage.enterPassword("SecurePass123!");
    loginPage.clickLoginButton();
}
```

**Page Object Implementation:**

Page objects contain the actual Selenium actions:
```java
public class LoginPage {
    private By emailInput = By.cssSelector("input#email");
    
    public void enterEmail(String email) {
        driver.findElement(emailInput).sendKeys(email);  // ← Selenium action
    }
    
    public void clickLoginButton() {
        driver.findElement(loginButton).click();  // ← Selenium action
    }
}
```

**The Filter Problem:**

The action mapper was filtering actions like this:
```python
if member in SUPPORTED_ACTIONS:
    # Add to steps
```

Where:
- `SUPPORTED_ACTIONS = {"click", "sendKeys", "submit", ...}`
- Test statements had: `member = "clickRegisterLink"`, `"enterFirstName"`, etc.
- These page object method names were **NOT in SUPPORTED_ACTIONS**
- Result: All test statements were filtered out → empty steps

### AST Structure Problem

When processing a test node's children, the mapper received:
```
Test: testUserRegistrationWithValidCredentials
  ├─ Statement node (member="clickRegisterLink")     ← Not in SUPPORTED_ACTIONS
  ├─ Statement node (member="enterFirstName")        ← Not in SUPPORTED_ACTIONS
  ├─ Statement node (member="enterLastName")         ← Not in SUPPORTED_ACTIONS
  └─ ...more page object calls...
```

None matched the SUPPORTED_ACTIONS filter, so all steps were skipped.

---

## The Fix

### Changes to action_mapper.py

**1. Added Utility Methods Exclusion List:**
```python
UTILITY_METHODS = {
    "findElement", "findElements",
    "manage", "timeouts", "implicitlyWait",
    "until", "presenceOfElementLocated",
    "visibilityOfElementLocated", "elementToBeClickable",
    "get", ...
}
```

**2. Enhanced Filtering Logic:**
```python
def map(self, ast_node: ASTNode) -> List[Dict]:
    for node in self._walk(ast_node):
        member = node.properties.get("member")
        qualifier = node.properties.get("qualifier")
        
        # Skip utility methods
        if member in UTILITY_METHODS:
            continue
        
        # Accept actions that are either:
        # 1. Direct Selenium actions (click, sendKeys, etc.)
        is_selenium_action = member in SUPPORTED_ACTIONS
        
        # 2. Page object method calls
        is_page_object_call = (
            qualifier and 
            qualifier not in ("Duration", "ExpectedConditions", "By", "", "driver", "wait")
        )
        
        if is_selenium_action or is_page_object_call:
            actions.append({
                "type": "action",
                "name": member,
                "target_name_id": target_name_id,
                "target_node_id": target_node_id,
                "parameters": parameters,
            })
```

### Key Logic

- **Selenium actions**: `click`, `sendKeys`, `submit`, `clear`, etc.
- **Page object calls**: Any method on a non-framework object
  - ✅ `loginPage.enterEmail()` → qualifier="loginPage"
  - ✅ `loginPage.clickLoginButton()` → qualifier="loginPage"
  - ❌ `driver.findElement()` → qualifier="driver" (excluded)
  - ❌ `wait.until()` → qualifier="wait" (excluded)

---

## Results

### Before Fix
```
Test: testUserRegistrationWithValidCredentials
  steps: []  // Empty
```

### After Fix
```
Test: testUserRegistrationWithValidCredentials
  steps: [
    {"type": "action", "name": "clickRegisterLink", ...},
    {"type": "action", "name": "enterFirstName", "parameters": {"value": "John"}},
    {"type": "action", "name": "enterLastName", "parameters": {"value": "Doe"}},
    {"type": "action", "name": "enterEmail", "parameters": {"value": "john@test.com"}},
    {"type": "action", "name": "enterPassword", "parameters": {"value": "SecurePass123!"}},
    {"type": "action", "name": "clickLoginButton", ...}
  ]
```

### Test Results
✅ **All 32 unit tests PASS**
- test_action_mapper.py
- test_assertion_mapper.py
- test_symbol_table.py (4 new tests)
- test_ir_builder.py
- test_pipeline_integration_indepth.py (10 integration tests)
- All others passing

---

## Design Rationale

This solution properly models the test architecture:

1. **Tests** → Call page object methods (high-level steps)
2. **Page Objects** → Call Selenium actions (low-level steps)
3. **IR Extraction** → Captures BOTH levels as actionable steps

This allows traceability from test intent down to specific UI interactions.

---

## Files Modified

- `src/extraction/action_mapper.py` - Enhanced filtering logic, added UTILITY_METHODS

## Files Created

- `ROOT_CAUSE_ANALYSIS.md` - This comprehensive analysis

---

**Date:** 2026-02-22  
**Status:** ✅ RESOLVED
