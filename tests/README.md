# Synapse Testing

Simple testing setup for Synapse, focusing on the most important functionality.

## Test Structure

```
tests/
├── conftest.py              # Test fixtures and mocks
├── data/                    # Sample test data
├── test_file_io.py          # Config loading, file operations
├── test_config.py           # Config parsing/validation
└── test_processing.py       # Map/reduce processing
```

## Key Test Areas

1. **File Operations**
   - YAML config loading
   - Error handling for missing/invalid files

2. **Configuration**
   - Default values work correctly
   - Environment variables are parsed properly

3. **Processing Logic**
   - Map phase processes transcripts correctly
   - Reduce phase combines information properly
   - Basic error handling works

## LLM Testing Approach

We use two key approaches from the pydantic-ai library to test our LLM-based functionality:

### 1. Agent Overriding

Use `Agent.override()` to test processing logic with deterministic outputs:

```python
# In test_processing.py
from pydantic_ai import Agent, TestModel

def test_map_phase_processing():
    # Override the agent model for predictable outputs during testing
    with Agent.override("google-gla:gemini-2.5-flash-preview-04-17", TestModel(outputs=["Test person profile"])):
        # Test runs with the overridden model instead of calling the real API
        result = run_map_phase(...)
        assert result[0] == 1  # One file processed
        assert result[1] == 0  # No failures
```

### 2. Message Validation

Use `capture_run_messages()` to verify prompt construction:

```python
# In test_processing.py
from pydantic_ai import capture_run_messages

def test_prompt_formatting():
    # Capture the messages sent to the LLM without making API calls
    with capture_run_messages() as messages:
        agent.run("Test prompt with {variable}", variable="test_value")

    # Verify the prompt was formatted correctly
    assert "Test prompt with test_value" in messages[0]["contents"]
```

### Basic Mock (Fallback Approach)

For simpler tests, we may still use a basic mock:

```python
# Example mock in conftest.py
@pytest.fixture
def mock_agent(mocker):
    mock = mocker.MagicMock()
    mock.run.return_value = mocker.MagicMock(output="Test output")
    return mock
```

## Test Safety Controls

Set `ALLOW_MODEL_REQUESTS=False` globally in your test environment to prevent accidental API calls:

```python
# In conftest.py
import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def block_real_llm_calls():
    """Block any real LLM API calls during testing."""
    os.environ["ALLOW_MODEL_REQUESTS"] = "False"
    yield
    # Restore previous value if needed
    os.environ.pop("ALLOW_MODEL_REQUESTS", None)
```

This ensures all tests will fail explicitly if they try to make real API calls instead of using test models.

## Running Tests

```bash
# Install dependencies
uv pip install pytest pytest-asyncio pytest-mock

# Run tests
pytest
```