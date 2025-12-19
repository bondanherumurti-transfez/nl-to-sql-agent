# Testing Guide

This guide covers the comprehensive test suite for the NL-to-SQL Telegram Bot.

## Overview

The project includes **18 automated tests** across 4 test files, covering:
- SQL validation and security
- Core agent logic
- Telegram bot handlers
- Natural language response generation
- Database schema relationships

## Quick Start

### Install Test Dependencies

```bash
pip install pytest pytest-mock pytest-asyncio
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Files

```bash
# SQL Validator tests only
pytest tests/test_sql_validator.py

# Agent core tests only
pytest tests/test_agent.py

# Telegram bot tests only
pytest tests/test_bot_telegram.py
```

### Run Specific Tests

```bash
# Run a single test by name
pytest tests/test_sql_validator.py::test_validate_select_queries

# Run tests matching a pattern
pytest -k "injection"
```

## Test Suite Breakdown

### 1. SQL Validator Tests (`tests/test_sql_validator.py`)

**9 tests** covering SQL cleaning, validation, and security.

#### Security Tests

| Test | What It Validates |
|------|-------------------|
| `test_validate_select_queries` | SELECT and WITH (CTE) queries are allowed |
| `test_validate_disallowed_queries` | DROP, DELETE, UPDATE, INSERT are blocked |
| `test_sql_injection_attempts` | Multiple statements are detected and blocked |
| `test_sql_injection_with_cte` | CTE-based injection attacks are blocked |

#### SQL Cleaning Tests

| Test | What It Validates |
|------|-------------------|
| `test_clean_sql_with_markdown` | Markdown code blocks are stripped from Claude's responses |
| `test_clean_sql_with_text_prefix` | Text prefixes are handled correctly |

#### Safety Feature Tests

| Test | What It Validates |
|------|-------------------|
| `test_add_limit_if_missing` | Queries without LIMIT get one added (default 100) |
| `test_add_limit_preserves_existing` | Queries with existing LIMIT are not modified |
| `test_add_limit_custom_value` | Custom LIMIT values work correctly |

---

### 2. Agent Core Tests (`tests/test_agent.py`)

**4 tests** covering the NL-to-SQL agent with mocked Claude API and PostgreSQL.

| Test | What It Validates |
|------|-------------------|
| `test_agent_initialization` | Agent initializes correctly with environment variables |
| `test_generate_sql` | SQL generation via Claude API works correctly |
| `test_execute_sql_success` | Database execution returns correct results and columns |
| `test_query_integration` | Full flow from natural language to results works end-to-end |

**Mocking Strategy:**
- Claude API is mocked to prevent spending tokens
- PostgreSQL is mocked to avoid needing a live database
- Tests verify behavior without external dependencies

---

### 3. Telegram Bot Tests (`tests/test_bot_telegram.py`)

**4 tests** covering Telegram bot handlers with async mocking.

| Test | What It Validates |
|------|-------------------|
| `test_start_command_allowed` | `/start` command works for allowed users |
| `test_start_command_denied` | `/start` command denies unauthorized users |
| `test_handle_query_success` | Natural language queries are processed correctly |
| `test_schema_command` | `/schema` command returns database schema |

**Mocking Strategy:**
- Telegram API is mocked using `AsyncMock`
- Agent responses are mocked to isolate bot logic
- Tests verify message formatting and access control

---

### 4. Narrative Tests (`tests/test_narrative.py`)

**3 tests** covering natural language summary generation.

| Test | What It Validates |
|------|-------------------|
| `test_generate_narrative_success` | Successful summary generation via Claude |
| `test_generate_narrative_failure` | Graceful fallback when API fails |
| `test_query_includes_natural_query` | Original question is preserved in result |

**Mocking Strategy:**
- Claude API is mocked to test summary generation logic
- Verifies that results are correctly passed to the prompt
- Ensures "Unable to generate summary" is returned on failure

---

### 5. Relationship Tests (`test_relationships.py`)

**1 test** in the project root (legacy test).

| Test | What It Validates |
|------|-------------------|
| `test_table_relationships` | Schema relationship configuration is loaded correctly |

---

## Understanding Test Output

When you run `pytest`, you'll see output like:

```
test_relationships.py .                  [ 4%]
tests/test_agent.py ....                 [ 23%]
tests/test_bot_telegram.py ....          [ 42%]
tests/test_narrative.py ...              [ 57%]
tests/test_sql_validator.py .........    [100%]

==================== 18 passed in 0.33s ====================
```

### What the symbols mean:
- **`.`** = Test passed ✅
- **`F`** = Test failed ❌
- **`E`** = Test error (crash) 💥
- **`s`** = Test skipped ⏭️
- **Percentage** = Progress through all tests (5% → 100%)

---

## Writing New Tests

### Example: Testing a New Feature

```python
import pytest
from sql_validator import SQLValidator

def test_my_new_feature():
    """Test description goes here"""
    # Arrange: Set up test data
    query = "SELECT * FROM users"
    
    # Act: Execute the code being tested
    result = SQLValidator.is_safe_query(query)
    
    # Assert: Verify expected behavior
    assert result[0] is True
```

### Best Practices

1. **Name tests clearly**: `test_what_you_are_testing`
2. **One assertion per test**: Keep tests focused
3. **Use descriptive docstrings**: Explain what's being validated
4. **Mock external dependencies**: Don't hit real APIs or databases
5. **Test edge cases**: Empty inputs, malicious inputs, boundary conditions

---

## Continuous Integration (CI)

To run tests automatically on every push, add this to `.github/workflows/test.yml`:

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: pytest
```

---

## Common Issues

### Import Errors

If you see `ModuleNotFoundError`, make sure you're in the project root:

```bash
cd /path/to/nl-to-sql-agent
pytest
```

### Async Test Warnings

If you see warnings about async tests, ensure `pytest-asyncio` is installed:

```bash
pip install pytest-asyncio
```

### Mock Not Working

If mocks aren't intercepting calls, check:
1. Path in `@patch()` matches the import in your code
2. Fixtures are being used correctly
3. Mock is set up before the code runs

---

## Test Coverage

To see which lines of code are tested:

```bash
pip install pytest-cov
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

This generates a report showing which lines are executed during tests.

---

## Next Steps

- [ ] Add CI/CD pipeline to run tests on every push
- [ ] Increase test coverage to 90%+
- [ ] Add performance tests for large queries
- [ ] Add integration tests with real Telegram API (sandbox)

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock Guide](https://docs.python.org/3/library/unittest.mock.html)
