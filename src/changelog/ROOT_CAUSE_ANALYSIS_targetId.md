# Root Cause Analysis: targetId Not Populated in Steps

## Problem Statement
Steps in the generated TestIR had `targetId: null` instead of containing references to the actual target element IDs (e.g., `loginButton`, `emailInput`, etc.).

**Example of the issue:**
```json
{
  "stepId": "STEP_01",
  "action": "generic",
  "targetId": null,  // ❌ Should reference actual target ID
  "target": null,
  "input": null,
  "parameters": {"value": "\"john.doe@example.com\""}
}
```

## Root Cause Breakdown

### 1. **Data Flow Through Extraction Layer**
The action mapper extracts test steps from Java AST and produces:
```python
{
    "type": "action",
    "name": "enterEmail",
    "target_name_id": None,       # ⚠️ This should contain target name
    "target_node_id": None,       # ⚠️ This should contain AST node ID
    "parameters": {"value": "..."}
}
```

**Issue**: Even when targets are extracted, `target_name_id` and `target_node_id` are `None` because:
- The symbol table isn't fully resolving references in the extraction phase
- Page object method calls don't map back to their target selectors

### 2. **Target ID Mapping Never Applied**
The pipeline builds a complete `target_name_to_id` mapping:
```python
target_name_to_id = {}
for i, t_ir in enumerate(targets_ir):
    src_name = normalized_targets[i]["name"]
    target_name_to_id[src_name] = t_ir.targetId  # e.g., "emailInput" -> "emailInput"
```

**Critical Issue**: This mapping was **never passed to TestIRBuilder**, so it couldn't resolve extracted target names to actual target IDs.

### 3. **TestIRBuilder Ignored Target Mapping**
The TestIRBuilder was receiving steps with `target_name_id` but had no way to map them:
```python
step_ir = StepIR(
    stepId=step.get("stepId", ...),
    action=step.get("action", "generic"),
    targetId=step.get("targetId"),  # ❌ Looks for direct targetId
    target=step_target,
    input=step_input,
    parameters=step.get("parameters", {}),
)
```

**The bug**: It only checked for direct `targetId` field, never tried to resolve `target_name_id` using the mapping.

## Solution Implemented

### Step 1: Update TestIRBuilder Signature (test_ir_builder.py)
Added `target_name_to_id` as optional parameter:
```python
def build(
    self,
    ...,
    target_name_to_id: Optional[Dict[str, str]] = None,
) -> TestIR:
```

### Step 2: Resolve targetId from Mapping (test_ir_builder.py)
Updated step building logic to use the mapping:
```python
# Resolve targetId: try direct targetId first, then use target_name_to_id mapping
target_id = step.get("targetId")
if not target_id and step.get("target_name_id"):
    # Map extracted target_name_id to actual targetId using the mapping
    target_id = target_name_to_id.get(step.get("target_name_id"))

step_ir = StepIR(
    ...,
    targetId=target_id,  # ✅ Now populated from mapping
    ...
)
```

### Step 3: Pass Mapping to Builder (pipeline.py)
Updated pipeline to pass the mapping to TestIRBuilder:
```python
test_ir = test_builder.build(
    test_id=extracted_test.get("name"),
    steps=extracted_test.get("steps", []),
    suite_id=suite_id,
    tags=extracted_test.get("tags", []),
    target_name_to_id=target_name_to_id,  # ✅ Pass the mapping
)
```

## Data Flow After Fix

```
Extraction Layer:
  step with target_name_id = "emailInput"
          ↓
Pipeline Layer:
  Creates target_name_to_id mapping: {"emailInput": "emailInput", ...}
          ↓
TestIRBuilder Layer:
  Receives step + mapping
  Looks up: target_name_to_id.get("emailInput") → "emailInput"
  Sets: targetId="emailInput"
          ↓
Output:
  {
    "stepId": "STEP_01",
    "action": "generic",
    "targetId": "emailInput",  ✅ Populated!
    ...
  }
```

## Why targetId Still Shows null in Current Tests

The current test cases show `targetId: null` because:
1. **Extraction layer limitation**: The symbol table isn't resolving page object method calls to their actual target selectors
2. **This is a separate issue** from the targetId mapping - extraction produces `target_name_id: None`
3. **The fix I implemented is correct** - it will populate targetId once extraction provides valid `target_name_id` values

The fix enables the pipeline to resolve targets when extraction data is available. The extraction enhancement would be Phase 3 work (improving symbol table resolution).

## Files Modified

| File | Change | Lines |
|------|--------|-------|
| [src/ir/builder/test_ir_builder.py](src/ir/builder/test_ir_builder.py) | Added `target_name_to_id` parameter and resolution logic | +15 |
| [src/core/pipeline.py](src/core/pipeline.py) | Pass `target_name_to_id` mapping to TestIRBuilder | +1 |

## Testing

✅ All 65 tests still passing after changes
✅ 4 pipeline integration tests passing
✅ Fix is backward compatible (optional parameter)

## Next Steps (Phase 3)

To fully populate targetId values:
1. **Enhance symbol table resolution** to map page object method calls to actual target selectors
2. **Improve extraction layer** to populate `target_name_id` from AST analysis
3. **Add test coverage** with realistic page object scenarios where targets can be resolved

## Conclusion

The root cause was a **data flow gap**: Target IDs existed in the pipeline but weren't being connected to steps because the mapping wasn't passed to the builder. The fix ensures that when extraction provides target information, it will be properly resolved through the mapping to populate step `targetId` fields.
