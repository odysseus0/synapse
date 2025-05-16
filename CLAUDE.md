# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Synapse is a text-based meeting analysis tool that uses a MapReduce-inspired approach to process meeting transcripts and extract synthesized information about key individuals. It uses LLMs (specifically Google's Gemini) to identify and consolidate information about people across multiple meetings. This is a personal script utility program.

The system follows a two-phase process:
1. **Map Phase**: Processes each transcript individually in parallel, generating structured Markdown summaries for each key person
2. **Reduce Phase**: Combines and synthesizes information across all transcripts to produce comprehensive profiles

Note: The current implementation uses a simplified reduce approach that takes advantage of Gemini's large 1M context window to process all map outputs in a single operation. The architecture is designed to be extended to a true distributed MapReduce implementation if needed for larger datasets that exceed context limits.

## Commands

### Setup

```bash
# Install dependencies using uv (Python package manager)
uv sync

# Set up environment variables
cp .env_template .env
# Edit .env with your API keys and configuration

# Add new package 
uv add pyyaml
```

### Running the tool

```bash
# Run the tool (both map and reduce phases)
uv run -m synapse.main

# Run only the map phase
uv run -m synapse.main --phase map

# Run only the reduce phase
uv run -m synapse.main --phase reduce

# See all available options
uv run -m synapse.main --help
```

### Linting and Type Checking

```bash
# Run ruff linter
uv run ruff check src/

# Auto-fix ruff linting issues
uv run ruff check --fix src/

# Run type checking with pyright
uv run pyright --ignoreexternal --verifytypes
```

### Testing

```bash
# Install test dependencies
uv sync

# Run all tests
uv run -m pytest

# Run tests with verbose output
uv run -m pytest -v

# Run tests with stop on first failure
uv run -m pytest -xvs
```

## Code Architecture

### Core Components

1. **Configuration Management** (`config.py`):
   - Uses Pydantic for typed configuration with environment variable support
   - Configurable directories, models, and processing parameters

2. **Execution Flow** (`main.py`):
   - `main()`: Primary async function controlling the full execution flow
   - `run_map_phase()`: Processes transcript files concurrently to generate map outputs
   - `run_reduce_phase()`: Aggregates map outputs and synthesizes final profiles

3. **Error Handling** (`exceptions.py`):
   - Structured hierarchy of exceptions for different failure modes
   - All exceptions inherit from base `SynapseError`

### Data Flow

1. Input text transcripts (from `./transcripts` or configured directory)
2. Map Phase: Each transcript is processed individually by the LLM using the map prompt
   - Outputs individual Markdown files for each transcript in the map output directory
3. Reduce Phase: All map outputs are concatenated and fed to a more powerful LLM
   - Outputs a single Markdown file with synthesized profiles in the specified output location
   - Current implementation processes all outputs in a single LLM call since Gemini's 1M context window is sufficient for moderate data sizes
   - The design can be extended to a true MapReduce implementation for larger datasets

### Key Dependencies

- **pydantic-ai-slim**: For LLM agent functionality
- **trio**: For async I/O and concurrency
- **logfire**: For structured logging
- **pydantic/pydantic-settings**: For configuration management
- **rich**: For console output and progress bars
- **typer**: For command-line interface

#### Trio Path Usage

When using trio.Path methods for file operations:

```python
# Correct usage of trio.Path.glob - await it first, then iterate over the result
files = [path for path in await directory_path.glob('*.txt')]
# NOT: async for path in directory_path.glob('*.txt')  # WRONG!

# Correct usage of trio.Path.read_text - async function
content = await file_path.read_text()

# Correct usage of trio.Path.exists - async function
if await file_path.exists():
    # do something
```

#### TestModel Usage

When mocking LLM agents for testing:

```python
# Import the TestModel
from pydantic_ai.models.test import TestModel
from pydantic_ai import Agent

# Override the agent for testing with a fixed output text
with Agent.override("google-gla:gemini-2.5-flash-preview-04-17",
                   TestModel(custom_output_text="Test output")):
    # Your test code that uses the agent
    result = await agent.run("prompt")
```

### Configuration

The system is highly configurable through environment variables with the `SYNAPSE_` prefix:
- `SYNAPSE_MAP_PHASE__INPUT_TRANSCRIPTS_DIR`: Directory for input transcripts
- `SYNAPSE_MAP_PHASE__OUTPUT_MAP_DIR`: Directory for map phase outputs
- `SYNAPSE_MAP_PHASE__LLM_MODEL`: LLM model to use for map phase
- `SYNAPSE_REDUCE_PHASE__OUTPUT_PROFILES_DIR`: Directory for final profile outputs
- `SYNAPSE_REDUCE_PHASE__LLM_MODEL`: LLM model to use for reduce phase
- `SYNAPSE_PROCESSING__CONCURRENCY`: Number of concurrent transcript processing tasks
