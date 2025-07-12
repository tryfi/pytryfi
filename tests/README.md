# PyTryFi Test Suite

This test suite provides comprehensive coverage for the pytryfi library.

## Test Coverage Status

As of the last run, the test coverage is:

| Module | Coverage | Status |
|--------|----------|--------|
| pytryfi/common/query.py | 100% | ✅ Complete |
| pytryfi/const.py | 100% | ✅ Complete |
| pytryfi/exceptions.py | 100% | ✅ Complete |
| pytryfi/fiBase.py | 100% | ✅ Complete |
| pytryfi/fiDevice.py | 100% | ✅ Complete |
| pytryfi/fiUser.py | 100% | ✅ Complete |
| pytryfi/ledColors.py | 100% | ✅ Complete |
| pytryfi/fiPet.py | 80% | ⚠️ Partial |
| pytryfi/__init__.py | 21% | ⚠️ Partial |
| **TOTAL** | **75%** | |

## Running Tests

1. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install test dependencies:
```bash
pip install -r requirements-test.txt
pip install -r requirements.txt
```

3. Run all tests with coverage:
```bash
python -m pytest --cov=pytryfi --cov-report=term-missing
```

4. Run specific test files:
```bash
python -m pytest tests/test_fi_base.py -v
```

5. Generate HTML coverage report:
```bash
python -m pytest --cov=pytryfi --cov-report=html
open htmlcov/index.html
```

## Test Structure

- `conftest.py` - Shared fixtures and test data
- `test_exceptions.py` - Tests for custom exception classes
- `test_led_colors.py` - Tests for LED color management
- `test_fi_base.py` - Tests for base station functionality
- `test_fi_device.py` - Tests for device/collar functionality
- `test_fi_user.py` - Tests for user management
- `test_fi_pet.py` - Tests for pet functionality
- `test_query.py` - Tests for GraphQL query functions
- `test_pytryfi.py` - Tests for main PyTryFi class

## Known Issues

Some tests for FiPet and the main PyTryFi class are failing due to:
- Complex initialization dependencies
- Mock setup requirements for the full API flow
- Some methods in the codebase that don't exist or have different names than expected

## Future Improvements

To achieve 100% test coverage:
1. Fix the failing FiPet tests by properly mocking dependencies
2. Add integration tests for the main PyTryFi class
3. Mock the GraphQL API responses more comprehensively
4. Add tests for error paths and edge cases in the main module