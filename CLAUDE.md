# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Synapse is a text analysis tool that uses a MapReduce-inspired approach to process meeting transcripts and Telegram conversations to generate comprehensive weekly newsletters. It uses LLMs (specifically Google's Gemini) to extract and synthesize key information across multiple sources.

The system follows a two-phase process:
1. **Map Phase**: Processes each input file (meeting transcript or Telegram export) individually in parallel, extracting newsletter-worthy content such as key decisions, project updates, technical discussions, and notable moments
2. **Reduce Phase**: Combines and synthesizes all extracted content to produce a cohesive weekly newsletter

The system uses directory-based file type detection:
- Meeting transcripts go in `data/meetings/`
- Telegram exports go in `data/telegram/`

Note: The current implementation uses a simplified reduce approach that takes advantage of Gemini's large context window to process all map outputs in a single operation.

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
uv run pyright
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
   - `run_map_phase()`: Processes input files concurrently to generate map outputs
   - `run_reduce_phase()`: Aggregates map outputs and synthesizes final newsletter

3. **Error Handling** (`exceptions.py`):
   - Structured hierarchy of exceptions for different failure modes
   - All exceptions inherit from base `SynapseError`

### Data Flow

1. Input files organized by type:
   - Meeting transcripts in `data/meetings/`
   - Telegram exports in `data/telegram/`
2. Map Phase: Each file is processed individually by the LLM using content-specific extraction prompts
   - Outputs individual Markdown files for each input in the map output directory
   - Different extraction functions for meetings vs Telegram content
3. Reduce Phase: All map outputs are concatenated and fed to the LLM
   - Outputs a newsletter file named `newsletter.md`
   - Current implementation processes all outputs in a single LLM call

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
- `SYNAPSE_MAP_PHASE__MEETINGS_DIR`: Directory for meeting transcript files
- `SYNAPSE_MAP_PHASE__TELEGRAM_DIR`: Directory for Telegram export files
- `SYNAPSE_MAP_PHASE__OUTPUT_MAP_DIR`: Directory for map phase outputs
- `SYNAPSE_MAP_PHASE__LLM_MODEL`: LLM model to use for map phase
- `SYNAPSE_REDUCE_PHASE__OUTPUT_DIR`: Directory for final newsletter output
- `SYNAPSE_REDUCE_PHASE__LLM_MODEL`: LLM model to use for reduce phase
- `SYNAPSE_PROCESSING__CONCURRENCY`: Number of concurrent processing tasks
