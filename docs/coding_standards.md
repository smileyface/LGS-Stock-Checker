# LGS Stock Checker - Coding Standards

This document outlines the coding standards and best practices to be followed when contributing to the LGS Stock Checker backend. Adhering to these guidelines ensures code consistency, readability, and maintainability.

## 1. Code Style

The project follows the [PEP 8 -- Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/). It is recommended to use an automated linter and formatter like `flake8` and `black` to ensure compliance.

Key points:

- **Naming Conventions**:
  - `snake_case` for functions, methods, variables, and modules.
  - `PascalCase` for classes.
  - `UPPER_SNAKE_CASE` for constants.
- **Line Length**: Maximum of 120 characters per line.
- **Docstrings**: All modules, classes, and functions should have descriptive docstrings explaining their purpose, arguments, and return values.

## 2. Imports

Proper import management is crucial for avoiding circular dependencies and maintaining a clear project structure.

### Import Order

Imports should be grouped in the following order:

1. Standard library imports (e.g., `os`, `sys`, `datetime`).
2. Third-party library imports (e.g., `pytest`, `requests`, `sqlalchemy`).
3. Internal application imports (e.g., `from managers import ...`, `from utility import ...`).

### Internal Imports

For imports within the same top-level package (e.g., within the `managers` package), **relative imports are preferred**. This helps prevent circular dependencies that can arise from absolute import paths.

**Do this:**

```python
# In managers/store_manager/stores/storefronts/crystal_commerce_store.py
from ..store import Store
```

**Avoid this:**

```python
# Avoid using absolute paths for internal modules
from managers.store_manager.stores.store import Store
```

### Package Structure

Every directory that is intended to be a Python package or sub-package **must** contain an `__init__.py` file. This file can be empty. This practice is essential for the Python interpreter and static type checkers to correctly recognize and traverse the project's module structure.

## 3. Type Hinting

All new code should be fully type-hinted. This improves code clarity, allows for static analysis, and helps prevent bugs.

- All function and method signatures must include type hints for arguments and the return value.
- Use types from the `typing` module (`List`, `Dict`, `Optional`, `Any`, `Callable`, etc.).
- Avoid using `# type: ignore` unless absolutely necessary. If used, it must be accompanied by a comment explaining why it is needed (e.g., to handle a known bug in a third-party library's stubs or a complex, unresolvable circular dependency).

**Example:**

```python
from typing import List, Dict, Any, Optional

def fetch_card_availability(card_name: str, specifications: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    # function body
    pass
```

## 4. Logging

A centralized logger is configured in the `utility` package. All logging throughout the application should use this instance.

**Do this:**

```python
from utility import logger

logger.info("This is an informational message.")
logger.error(f"An error occurred: {e}")
```

**Avoid this:**

```python
import logging

# Avoid creating new, separate logger instances in modules.
log = logging.getLogger(__name__)
```

## 5. Configuration

- **Environment Variables**: All configuration that varies between environments (development, testing, production) or contains sensitive data (e.g., `SECRET_KEY`, `DATABASE_URL`) must be loaded from environment variables.
- **`settings.py`**: This file defines configuration classes (`DevelopmentConfig`, `TestingConfig`, etc.) and should be the single source of truth for application configuration.

## 6. Testing

- **Isolation**: Unit tests must be isolated and self-contained. They **must not** make real network calls to external services. Use `unittest.mock` (`patch`, `MagicMock`) to mock external dependencies like APIs, database connections, and file systems.
- **Fixtures**: Use `pytest` fixtures to provide a consistent and clean state for tests. This includes database sessions (`db_session`), seeded data (`seeded_user`), and common mocks.
- **Coverage**: Tests should cover:
  - The "happy path" (successful execution).
  - Expected failure modes (e.g., invalid input, network errors).
  - Edge cases (e.g., empty lists, `None` values).
- **Smoke Tests**: The smoke test suite (`test_for_explosions.py`) is designed for broad, shallow testing. Its goal is to ensure that all functions in the application can be called with basic, safe inputs without crashing. It is not a substitute for detailed unit tests.

## 7. Error Handling

- **Custom Exceptions**: For application-specific error conditions (e.g., `InvalidSpecificationError`), define custom exception classes. This makes error handling more explicit and robust.
- **Graceful Failures**: Functions that interact with external services (e.g., web scrapers) should handle exceptions gracefully (e.g., `requests.exceptions.RequestException`) and return a sensible default value (like an empty list) instead of crashing.
