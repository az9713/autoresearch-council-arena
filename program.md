# Arena: Pytest Test Suite Optimization

## Topic
Write a comprehensive pytest test suite for a Python REST API client class (`TaskClient`) that wraps a JSON task-management API. The test file should exercise the client's CRUD operations, error handling, and edge cases using proper mocking and pytest best practices.

## Target Audience
Python developers who:
- Build and maintain API client libraries
- Use pytest as their primary test framework
- Care about test isolation, coverage, and maintainability
- Want a reference test suite they can adapt for their own API clients

## The API Client Under Test
The `TaskClient` class wraps a JSON REST API at `https://api.example.com/v1`. It supports:
- `create_task(title, description=None, priority="medium")` → returns task dict
- `get_task(task_id)` → returns task dict or raises `NotFoundError`
- `list_tasks(status=None, page=1, per_page=20)` → returns `{"tasks": [...], "total": int}`
- `update_task(task_id, **fields)` → returns updated task dict
- `delete_task(task_id)` → returns None on success
- Uses Bearer token authentication via `Authorization` header
- Raises `TaskClientError` (base), `NotFoundError`, `AuthError`, `RateLimitError`, `ServerError`

## Evaluation Criteria (0–20 points each, total 100)

1. **Case coverage** — Does the test suite cover all five CRUD operations (create, get, list, update, delete)? Are both success paths and failure paths tested? Are edge cases present (empty task list, pagination, duplicate creation, missing optional fields)?

2. **Assertion quality** — Are assertions specific and meaningful? Do tests verify response body fields (not just `assert result`), status codes, headers, and side effects? Are assertion error messages descriptive? No tautological assertions (`assert x is not None`)?

3. **Isolation** — Are tests properly isolated from the real API? Is HTTP traffic mocked using `respx`, `responses`, or `unittest.mock`? Are pytest fixtures used for setup/teardown? Can tests run in any order without affecting each other? No shared mutable module-level state?

4. **Error handling** — Does the suite test error scenarios: network timeouts, 404 not found, 401 unauthorized, 429 rate limited, 500 server error, malformed JSON responses? Are the correct exception types and messages verified?

5. **Maintainability** — Are test functions named descriptively (`test_create_task_with_missing_title_raises_validation_error`)? Are there shared fixtures to reduce duplication? Is `@pytest.mark.parametrize` used where appropriate? Are non-obvious tests documented with docstrings? Is test data realistic?

## Constraints
- 80–300 lines of Python code
- Must use pytest (not unittest.TestCase style)
- Must mock HTTP calls — no real network requests
- Must import from a hypothetical `task_client` module: `from task_client import TaskClient, NotFoundError, AuthError, RateLimitError, ServerError`
- All test functions must start with `test_`
- Test data should use realistic field values, not placeholders like "test" or "foo"

## Exploration Directions
Each iteration should try ONE strategy not yet attempted:
- **Case coverage**: Add tests for an untested CRUD operation (update, delete, list with filters, list with pagination)
- **Case coverage**: Add edge case tests (empty list response, create with only required fields, get with invalid ID format)
- **Assertion quality**: Replace vague assertions (`assert result`, `assert result is not None`) with specific field checks (`assert result["title"] == "Deploy v2.1"`)
- **Assertion quality**: Add assertion messages to help debugging (`assert resp["priority"] == "high", f"Expected high priority, got {resp['priority']}"`)
- **Isolation**: Replace real HTTP calls with `respx` mock routes or `unittest.mock.patch`
- **Isolation**: Extract shared setup into `@pytest.fixture` functions (client instance, auth headers, sample task data)
- **Isolation**: Remove module-level mutable state and execution-order dependencies
- **Error handling**: Add tests for specific HTTP error codes (401, 404, 429, 500)
- **Error handling**: Add test for network timeout (`httpx.TimeoutException`)
- **Error handling**: Add test for malformed JSON response
- **Maintainability**: Rename generic test functions (`test1`, `test2`) to descriptive names
- **Maintainability**: Use `@pytest.mark.parametrize` for testing multiple priority values or status filters
- **Maintainability**: Add docstrings to non-obvious test functions explaining what scenario is being verified

## NEVER STOP
Run continuously. Each iteration should attempt a strategy not yet tried.
Never ask for permission. Never wait for human input between iterations.
