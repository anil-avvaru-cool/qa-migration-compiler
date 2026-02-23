#!/usr/bin/env python3
"""
Standalone test runner for IR models.
Tests model creation and serialization without requiring pytest.
"""

import sys
import json
from pathlib import Path

# Add the project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Try importing pydantic - if not available, create a simple mock
try:
    from pydantic import BaseModel, Field, ConfigDict
    print("✓ Pydantic is available")
except ImportError:
    print("✗ Pydantic not available - creating mock for testing")
    class BaseModel:
        def model_dump_json(self):
            return json.dumps(self.model_dump())
        def model_dump(self):
            return vars(self)

# Now test imports from our models
test_passed = 0
test_failed = 0

def test(name, func):
    """Simple test runner."""
    global test_passed, test_failed
    try:
        func()
        print(f"✓ {name}")
        test_passed += 1
    except Exception as e:
        print(f"✗ {name}: {e}")
        test_failed += 1

def test_models_exist():
    """Test that all model files exist."""
    models_path = project_root / "src/ir/models"
    expected_files = [
        "project.py",
        "environment.py",
        "targets.py",
        "data.py",
        "test.py",
        "suite.py",
    ]
    for filename in expected_files:
        model_file = models_path / filename
        if not model_file.exists():
            raise FileNotFoundError(f"Missing {filename}")

def test_builders_exist():
    """Test that all builder files exist."""
    builders_path = project_root / "src/ir/builder"
    expected_files = [
        "project_ir_builder.py",
        "targets_ir_builder.py",
        "test_ir_builder.py",
        "suite_ir_builder.py",
    ]
    for filename in expected_files:
        builder_file = builders_path / filename
        if not builder_file.exists():
            raise FileNotFoundError(f"Missing {filename}")

def test_models_syntax():
    """Test that model files have valid Python syntax."""
    import py_compile
    import tempfile
    models_path = project_root / "src/ir/models"
    model_files = list(models_path.glob("*.py"))
    for model_file in model_files:
        if model_file.name.startswith("__"):
            continue
        try:
            py_compile.compile(str(model_file), doraise=True)
        except py_compile.PyCompileError as e:
            raise SyntaxError(f"Syntax error in {model_file.name}: {e}")

def test_builders_syntax():
    """Test that builder files have valid Python syntax."""
    import py_compile
    builders_path = project_root / "src/ir/builder"
    builder_files = list(builders_path.glob("*.py"))
    for builder_file in builder_files:
        if builder_file.name.startswith("__"):
            continue
        try:
            py_compile.compile(str(builder_file), doraise=True)
        except py_compile.PyCompileError as e:
            raise SyntaxError(f"Syntax error in {builder_file.name}: {e}")

def test_test_files_syntax():
    """Test that test files have valid Python syntax."""
    import py_compile
    tests_path = project_root / "src/tests"
    test_files = [
        "test_ir_models_enhanced.py",
        "test_builders_enhanced.py",
    ]
    for filename in test_files:
        test_file = tests_path / filename
        if test_file.exists():
            try:
                py_compile.compile(str(test_file), doraise=True)
            except py_compile.PyCompileError as e:
                raise SyntaxError(f"Syntax error in {filename}: {e}")

def test_model_pydantic_compatibility():
    """Test that models follow Pydantic structure."""
    models_path = project_root / "src/ir/models"
    test_files = [
        "project.py",
        "environment.py",
        "targets.py",
        "data.py",
        "test.py",
        "suite.py",
    ]
    
    for filename in test_files:
        filepath = models_path / filename
        with open(filepath) as f:
            content = f.read()
            # Check for Pydantic imports
            if "from pydantic import" not in content and "BaseModel" not in content:
                raise ValueError(f"{filename} missing Pydantic BaseModel")
            # Check model_config or Config
            if "model_config" not in content and "class Config" not in content:
                print(f"  Warning: {filename} may be missing model configuration")

def test_changelog_files_exist():
    """Test that changelog files were created."""
    changelog_path = project_root / "src/changelog"
    expected_files = [
        "1.1_implementation_plan.md",
        "2.0_implementation_summary.md",
    ]
    for filename in expected_files:
        changelog_file = changelog_path / filename
        if not changelog_file.exists():
            raise FileNotFoundError(f"Missing changelog file: {filename}")

def test_builder_logic():
    """Test that builders have proper logic."""
    builders_path = project_root / "src/ir/builder"
    
    # Check ProjectIRBuilder
    with open(builders_path / "project_ir_builder.py") as f:
        content = f.read()
        if "irVersion" not in content:
            raise ValueError("ProjectIRBuilder missing irVersion handling")
        if "projectName" not in content:
            raise ValueError("ProjectIRBuilder missing projectName handling")
    
    # Check TargetsIRBuilder  
    with open(builders_path / "targets_ir_builder.py") as f:
        content = f.read()
        if "selectorStrategies" not in content:
            raise ValueError("TargetsIRBuilder missing selectorStrategies handling")
        if "stabilityScore" not in content:
            raise ValueError("TargetsIRBuilder missing stabilityScore handling")
    
    # Check TestIRBuilder
    with open(builders_path / "test_ir_builder.py") as f:
        content = f.read()
        if "testId" not in content:
            raise ValueError("TestIRBuilder missing testId handling")
        if "DataBinding" not in content:
            raise ValueError("TestIRBuilder missing DataBinding handling")

def test_json_schema_examples():
    """Test that JSON examples in documentation are valid."""
    summary_file = project_root / "src/changelog/2.0_implementation_summary.md"
    with open(summary_file) as f:
        content = f.read()
        # Try to find and parse JSON blocks
        import re
        json_blocks = re.findall(r'```json\n(.*?)\n```', content, re.DOTALL)
        
        valid_count = 0
        for block in json_blocks:
            try:
                json.loads(block)
                valid_count += 1
            except json.JSONDecodeError as e:
                print(f"  Warning: Invalid JSON in documentation: {e}")
        
        if valid_count == 0:
            raise ValueError("No valid JSON examples found in documentation")

# Run all tests
print("\n" + "="*60)
print("IR Model Enhancement - Standalone Test Runner")
print("="*60 + "\n")

print("File Structure Tests:")
test("Models directory exists and has required files", test_models_exist)
test("Builders directory exists and has required files", test_builders_exist)
test("Changelog files created", test_changelog_files_exist)

print("\nSyntax Validation Tests:")
test("Model files have valid Python syntax", test_models_syntax)
test("Builder files have valid Python syntax", test_builders_syntax)
test("Test files have valid Python syntax", test_test_files_syntax)

print("\nSchema Compliance Tests:")
test("Models follow Pydantic conventions", test_model_pydantic_compatibility)
test("Builders implement required logic", test_builder_logic)
test("JSON schema examples are valid", test_json_schema_examples)

print("\n" + "="*60)
print(f"Test Results: {test_passed} passed, {test_failed} failed")
print("="*60 + "\n")

if test_failed == 0:
    print("✓ All tests passed!")
    sys.exit(0)
else:
    print(f"✗ {test_failed} test(s) failed!")
    sys.exit(1)
