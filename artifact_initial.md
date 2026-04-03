```python
"""Tests for TaskClient API wrapper."""
import httpx
from task_client import TaskClient

BASE_URL = "https://api.example.com/v1"
TOKEN = "sk-test-abc123"

# shared state for tests
created_id = None


def test1():
    """Test creating a task."""
    client = TaskClient(BASE_URL, token=TOKEN)
    result = client.create_task("test task", description="a]description", priority="high")
    global created_id
    created_id = result["id"]
    assert result is not None
    assert result["title"]


def test2():
    """Test getting a task."""
    client = TaskClient(BASE_URL, token=TOKEN)
    result = client.get_task(created_id)
    assert result
    assert "id" in result


def test3():
    """Test not found."""
    client = TaskClient(BASE_URL, token=TOKEN)
    try:
        client.get_task("nonexistent-id-999")
        assert False, "Should have raised"
    except Exception as e:
        assert "not found" in str(e).lower()


def test4():
    """Test list tasks."""
    client = TaskClient(BASE_URL, token=TOKEN)
    result = client.list_tasks()
    assert result is not None
    assert isinstance(result, dict)
```
