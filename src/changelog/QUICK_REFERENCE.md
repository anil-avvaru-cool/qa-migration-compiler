# IR Model 2.0 - Quick Reference Guide

## What Changed?

### Before (1.0) → After (2.0)

#### ProjectIR
```python
# Before
ProjectIR(
    id="hash_id",
    metadata=ProjectMetadata(name, version, generated_at, source_language, compiler_version),
    environments=["env1"],
    suites=["suite1"],
    tests=["test1"]
)

# After
ProjectIR(
    irVersion="2.0.0",
    projectName="EcommerceAutomation",
    sourceFramework="Selenium-Java-TestNG",
    targetFramework="Playwright-TS",
    architecturePattern="POM",
    supportsParallel=True,
    createdOn="2026-02-22"
)
```

#### EnvironmentIR
```python
# Before
EnvironmentIR(
    id="hash_id",
    name="qa",
    base_url="https://qa.example.com",
    variables={"env": "qa"}
)

# After
EnvironmentIR(
    baseUrls={"qa": "https://qa.example.com", "staging": "..."},
    executionMode="parallel",
    browsers=["chrome", "firefox"],
    timeouts=TimeoutConfig(implicit=5000, explicit=10000, pageLoad=30000),
    retryPolicy=RetryPolicy(enabled=True, maxRetries=2)
)
```

#### TargetIR
```python
# Before
TargetIR(
    id="hash_id",
    name="Username Input",
    type="page",
    locator="#username",
    metadata={"page": "LoginPage"}
)

# After
TargetIR(
    targetId="LOGIN_USERNAME",
    type="ui-element",
    context=TargetContext(page="LoginPage", component=None),
    semantic=SemanticInfo(role="textbox", businessName="Username Input"),
    selectorStrategies=[
        SelectorStrategy(strategy="css", value="#username", stabilityScore=0.96),
        SelectorStrategy(strategy="xpath", value="//input[@id='username']", stabilityScore=0.88),
        SelectorStrategy(strategy="id", value="username", stabilityScore=0.98)
    ],
    preferredStrategy="css"
)
```

#### TestDataIR
```python
# Before
TestDataIR(
    id="hash_id",
    name="LoginData",
    values={"username": "user1", "password": "pass1"}
)

# After
TestDataIR(
    dataSetId="LOGIN_DATA",
    type="inline",
    records=[
        {"username": "testuser1", "password": "Password123", "expectedMessage": "Welcome testuser1"},
        {"username": "testuser2", "password": "Password456", "expectedMessage": "Welcome testuser2"}
    ]
)
```

#### TestIR
```python
# Before
TestIR(
    id="hash_id",
    name="Login Test",
    suite_id="suite_hash",
    environment_id="env_hash",
    data_id="data_hash",
    tags=["smoke"],
    steps=[StepIR(id="step_hash", type="click", name="Click Login", ...)]
)

# After
TestIR(
    testId="TC_LOGIN_VALID_001",
    suiteId="AUTH_SUITE",
    priority="P1",
    severity="Critical",
    dataBinding=DataBinding(dataSetId="LOGIN_DATA", iterationStrategy="row-wise"),
    steps=[
        StepIR(stepId="STEP_01", action="navigate", target=StepTarget(type="url", value="qa:/login")),
        StepIR(stepId="STEP_02", action="type", targetId="LOGIN_USERNAME", inp=StepInput(source="data", field="username")),
        StepIR(stepId="STEP_03", action="type", targetId="LOGIN_PASSWORD", inp=StepInput(source="data", field="password", masked=True))
    ],
    assertions=[
        AssertionIR(assertId="ASSERT_01", type="equals", 
                   actual=DataSource(source="ui", targetId="WELCOME_MESSAGE"),
                   expected=DataSource(source="data", field="expectedMessage"))
    ],
    tags=["smoke", "login"]
)
```

#### SuiteIR
```python
# Before
SuiteIR(
    id="hash_id",
    name="Login Suite",
    parent_id="parent_hash",
    tests=["test_hash1", "test_hash2"]
)

# After
SuiteIR(
    suiteId="AUTH_SUITE",
    description="Authentication Tests",
    tests=["TC_LOGIN_VALID_001", "TC_LOGIN_INVALID_002"]
)
```

---

## New Convenience Classes

### TimeoutConfig
```python
TimeoutConfig(
    implicit=5000,        # milliseconds
    explicit=10000,       # milliseconds
    pageLoad=30000        # milliseconds
)
```

### RetryPolicy
```python
RetryPolicy(
    enabled=True,
    maxRetries=2
)
```

### TargetContext
```python
TargetContext(
    page="LoginPage",      # Page/Screen name
    component=None,        # Nested component
    frame=None            # Iframe name
)
```

### SemanticInfo
```python
SemanticInfo(
    role="textbox",        # ARIA role
    businessName="Username Input"  # Business name
)
```

### SelectorStrategy
```python
SelectorStrategy(
    strategy="css",        # css, xpath, id, uipath-selector, etc.
    value="#username",
    stabilityScore=0.96    # 0.0 - 1.0
)
```

### StepInput
```python
StepInput(
    source="data",         # data, ui, constant, expression
    field="username",
    masked=False
)
```

### StepTarget
```python
StepTarget(
    type="url",            # url, selector, api, etc.
    value="qa:/login"
)
```

### DataSource
```python
DataSource(
    source="ui",           # ui, data, constant, expression
    field=None,
    targetId="WELCOME_MESSAGE",
    value=None,
    masked=False
)
```

### DataBinding
```python
DataBinding(
    dataSetId="LOGIN_DATA",
    iterationStrategy="row-wise"  # row-wise, column-wise
)
```

---

## Migration Path

### Step 1: Update Extractors
Old: Extract to simple dicts
New: Extract to dicts with new fields (context, semantic, strategies, etc.)

### Step 2: Update Builders
Old: Build with hash IDs and flat structures
New: Build with meaningful IDs and nested models

### Step 3: Update Pipeline
Old: Pass lists of entities
New: Pass builder results with full context

### Step 4: Update Writer
Old: Write single monolithic file
New: Write modular JSON files per entity type

### Step 5: Update Tests
Old: Test hash-based IDs
New: Test semantic IDs and nested structures

---

## Common Patterns

### Creating a Project
```python
from src.ir.builder.project_ir_builder import ProjectIRBuilder

builder = ProjectIRBuilder()
project = builder.build(
    project_name="EcommerceAutomation",
    source_framework="Selenium-Java-TestNG",
    target_framework="Playwright-TS",
    architecture_pattern="POM",
    supports_parallel=True,
    created_on="2026-02-22"
)
```

### Creating Targets with Strategies
```python
from src.ir.builder.targets_ir_builder import TargetsIRBuilder

builder = TargetsIRBuilder()
targets = builder.build([
    {
        "targetId": "LOGIN_USERNAME",
        "type": "ui-element",
        "context": {"page": "LoginPage"},
        "semantic": {"role": "textbox", "businessName": "Username Input"},
        "selectorStrategies": [
            {"strategy": "css", "value": "#username", "stabilityScore": 0.96},
            {"strategy": "xpath", "value": "//input[@id='username']", "stabilityScore": 0.88},
        ],
        "preferredStrategy": "css"
    }
])
```

### Creating Tests with Data Binding
```python
from src.ir.builder.test_ir_builder import TestIRBuilder

builder = TestIRBuilder()
test = builder.build(
    test_id="TC_LOGIN_001",
    steps=[
        {"stepId": "STEP_01", "action": "navigate", "target": {"type": "url", "value": "qa:/"}},
        {"stepId": "STEP_02", "action": "type", "targetId": "USERNAME", "input": {"source": "data", "field": "username"}},
    ],
    suite_id="AUTH_SUITE",
    priority="P1",
    data_binding={"dataSetId": "LOGIN_DATA", "iterationStrategy": "row-wise"}
)
```

### Creating Suites
```python
from src.ir.builder.suite_ir_builder import SuiteIRBuilder

builder = SuiteIRBuilder()
suite = builder.build(
    suite_id="AUTH_SUITE",
    tests=["TC_LOGIN_001", "TC_LOGIN_002"],
    description="Authentication Tests"
)
```

### JSON Serialization
```python
# All models support model_dump_json()
json_str = project.model_dump_json()
json_dict = project.model_dump()

# Example output
{
    "irVersion": "2.0.0",
    "projectName": "EcommerceAutomation",
    ...
}
```

---

## Field Reference

### ProjectIR Fields
| Field | Type | Required | Example |
|-------|------|----------|---------|
| irVersion | str | Yes | "2.0.0" |
| projectName | str | Yes | "EcommerceAutomation" |
| sourceFramework | str | Yes | "Selenium-Java-TestNG" |
| targetFramework | str | Yes | "Playwright-TS" |
| architecturePattern | str | No | "POM" |
| supportsParallel | bool | No | true |
| createdOn | str | Yes | "2026-02-22" |

### EnvironmentIR Fields
| Field | Type | Required | Example |
|-------|------|----------|---------|
| baseUrls | Dict[str, str] | No | {"qa": "https://..."} |
| executionMode | str | No | "parallel" |
| browsers | List[str] | No | ["chrome"] |
| timeouts | TimeoutConfig | No | TimeoutConfig(...) |
| retryPolicy | RetryPolicy | No | RetryPolicy(...) |

### TargetIR Fields
| Field | Type | Required | Example |
|-------|------|----------|---------|
| targetId | str | Yes | "LOGIN_USERNAME" |
| type | str | No | "ui-element" |
| context | TargetContext | No | TargetContext(...) |
| semantic | SemanticInfo | Yes | SemanticInfo(...) |
| selectorStrategies | List[SelectorStrategy] | No | [SelectorStrategy(...)] |
| preferredStrategy | str | No | "css" |

### TestIR Fields
| Field | Type | Required | Example |
|-------|------|----------|---------|
| testId | str | Yes | "TC_LOGIN_001" |
| suiteId | str | No | "AUTH_SUITE" |
| priority | str | No | "P1" |
| severity | str | No | "Critical" |
| dataBinding | DataBinding | No | DataBinding(...) |
| steps | List[StepIR] | No | [StepIR(...)] |
| assertions | List[AssertionIR] | No | [AssertionIR(...)] |
| tags | List[str] | No | ["smoke", "login"] |

### SuiteIR Fields
| Field | Type | Required | Example |
|-------|------|----------|---------|
| suiteId | str | Yes | "AUTH_SUITE" |
| description | str | No | "Authentication Tests" |
| tests | List[str] | No | ["TC_LOGIN_001"] |

---

## Stability Score Guidelines

| Score | Meaning | Example |
|-------|---------|---------|
| 0.98-1.0 | Highly stable | ID selector, unique attribute |
| 0.90-0.97 | Very stable | CSS selector with IDs |
| 0.80-0.89 | Stable | XPath with multiple attributes |
| 0.70-0.79 | Moderate | CSS selector with classes |
| 0.60-0.69 | Fragile | XPath with text content |
| < 0.60 | Very fragile | Image XPath, index-based |

---

## Best Practices

1. **Always use multiple selector strategies** for resilience
2. **Document business names** for semantic understanding
3. **Set stability scores** based on selector robustness
4. **Use data binding** for parameterized tests
5. **Add meaningful tags** for test organization
6. **Include priority and severity** for test management
7. **Provide descriptions** in suites for clarity
8. **Mask sensitive data** in step inputs
9. **Use camelCase** in JSON output
10. **Validate stability scores** (0.0-1.0 range)

---

## Common Issues & Solutions

### Issue: "targetId not found"
**Solution**: Ensure targetId in steps matches targetId in targets.json

### Issue: "dataSetId mismatch"
**Solution**: Verify dataBinding.dataSetId matches actual data file dataSetId

### Issue: "Stability score out of range"
**Solution**: Ensure stabilityScore is between 0.0 and 1.0

### Issue: "Missing semantic info"
**Solution**: All targets must have semantic.role and semantic.businessName

### Issue: "Invalid createdOn format"
**Solution**: Use "YYYY-MM-DD" format (e.g., "2026-02-22")

---

## Next Version Enhancement Ideas

- [ ] Conditional assertions
- [ ] Screenshot capture steps
- [ ] API endpoint targets
- [ ] Database query assertions
- [ ] Custom step types
- [ ] Test dependencies
- [ ] Performance assertions
- [ ] Screenshot comparisons
- [ ] Mobile-specific selectors
- [ ] Accessibility testing helpers

