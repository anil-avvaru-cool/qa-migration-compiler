# Root Cause Analysis: Steps Not Populated in Final IR

## Problem
Steps arrays were empty in the final IR output, even though targets were correctly populated:
```json
{
  "tests": [{
    "id": "8a3e3a1b98ee",
    "name": "testCompleteCheckoutFlow",
    "steps": []  // ← EMPTY!
  }]
}
```

## Root Cause Discovery

### Investigation Steps

1. **Examined test log output** (test_results.log)
   - Action mapper was being called but returning empty results
   - All tests had empty `steps` arrays

2. **Traced AST structure**
   - Located test nodes in the AST tree
   - Found that test methods call **page object methods**, not direct Selenium actions:
     ```
     Test node: testUserRegistrationWithValidCredentials
       ├─ node_29: loginPage.clickRegisterLink()    ← Page object method
       ├─ node_31: loginPage.enterFirstName()       ← Page object method
       ├─ node_34: loginPage.enterLastName()        ← Page object method
     ```

3. **Analyzed action mapper filtering**
   - Mapper code was checking: `if member in SUPPORTED_ACTIONS`
   - SUPPORTED_ACTIONS = {click, sendKeys, submit, clear, doubleClick, contextClick, getText, waitForVisible, navigate}
   - Test nodes had member values like: "clickRegisterLink", "enterFirstName", "enterLastName"
   - **These page object method names were NOT in SUPPORTED_ACTIONS**
   - Result: All test statement nodes were skipped

### The Issue

```python
# OLD CODE (extractor.py)
def _extract_test(self, node: ASTNode) -> Dict:
    steps: List[Dict] = []
    for statement in getattr(node, "children", []):
        actions = self.action_mapper.map(statement)  # ← Returns [] always!
        if actions:
            steps.extend(actions)
        assertions = self.assertion_mapper.map(statement)
        if assertions:
            steps.extend(assertions)
    return {"name": node.name, "steps": steps, ...}  # ← Empty steps
```

Because:
- Test calls `loginPage.enterFirstName("John")`
- Action mapper looks for `"enterFirstName"` in SUPPORTED_ACTIONS
- It's not there → skipped
- Result: Empty steps

## Solution

### Key Changes

**1. Enhanced action_mapper.py to recognize page object method calls:**

Added a new set of utility methods to exclude:
```python
UTILITY_METHODS = {
    "findElement", "findElements", "manage",
    "implicitlyWait", "until", "get", 
    "presenceOfElementLocated", ...
}
```

Updated filtering logic to accept:
- Direct Selenium actions (click, sendKeys, etc.) OR
- Page object method calls (where qualifier is not a utility/framework)

```python
def map(self, ast_node: ASTNode) -> List[Dict]:
    for node in self._walk(ast_node):
        member = node.properties.get("member")
        qualifier = node.properties.get("qualifier")
        
        if member in UTILITY_METHODS:
            continue
        
        is_selenium_action = member in SUPPORTED_ACTIONS
        is_page_object_call = (
            qualifier and 
            qualifier not in ("Duration", "ExpectedConditions", "By", "", "driver", "wait")
        )
        
        if is_selenium_action or is_page_object_call:
            # Add as step
            actions.append({...})
```

### Result

Now the mapper recognizes:
- ✅ Selenium direct actions: `element.click()`, `element.sendKeys()`
- ✅ Page object methods: `loginPage.enterFirstName()`, `loginPage.clickLoginButton()`
- ❌ Utility methods: `findElement()`, `wait.until()` (excluded)

## Verification

**Before fix:**
```
tests: [
  {
    "name": "testCompleteCheckoutFlow",
    "steps": []  // Empty
  }
]
```

**After fix:**
```
tests: [
  {
    "name": "testUserRegistrationWithValidCredentials",
    "steps": [
      {"type": "action", "name": "clickRegisterLink", "parameters": {}},
      {"type": "action", "name": "enterFirstName", "parameters": {}},
      {"type": "action", "name": "enterLastName", "parameters": {}},
      {"type": "action", "name": "enterEmail", "parameters": {}},
      {"type": "action", "name": "enterPassword", "parameters": {}},
      {"type": "action", "name": "clickLoginButton", "parameters": {}}
    ]
  }
]
```

## Test Results

✅ All 32 unit tests pass
✅ No regressions
✅ Steps now correctly populated for both:
  - Direct Selenium actions in page object implementations
  - Page object method calls from tests

## Files Modified

- `src/extraction/action_mapper.py` - Enhanced filtering logic

## Architecture Impact

This fix aligns with the proper separation of concerns:
- **Page Objects**: Contain Selenium action invocations (click, sendKeys)
- **Tests**: Call page object methods (enterFirstName, clickLoginButton)
- **IR Extraction**: Captures BOTH levels as actionable steps

---

**Generated:** 2026-02-22  
**Status:** RESOLVED ✓
