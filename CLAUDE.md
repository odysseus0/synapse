# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Synapse is a text-based meeting analysis tool that uses a MapReduce approach to process meeting transcripts and extract synthesized information about key individuals. It uses LLMs (specifically Google's Gemini) to identify and consolidate information about people across multiple meetings.

The system follows a two-phase process:
1. **Map Phase**: Processes each transcript individually, generating structured Markdown summaries for each key person
2. **Reduce Phase**: Combines and synthesizes information across all transcripts to produce comprehensive profiles

## Commands

### Setup

```bash
# Install dependencies using uv (Python package manager)
uv sync

# Set up environment variables
cp .env_template .env
# Edit .env with your API keys and configuration
```

### Running the tool

```bash
# Run the tool (both map and reduce phases)
uv run synapse.main

# Or using the package script
uv run -m synapse
```

### Linting and Type Checking

```bash
# Run ruff linter
ruff check main.py

# Run type checking with pyright
pyright
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

### Key Dependencies

- **pydantic-ai-slim**: For LLM agent functionality
- **trio**: For async I/O and concurrency
- **logfire**: For structured logging
- **pydantic/pydantic-settings**: For configuration management
- **rich**: For console output and progress bars

### Configuration

The system is highly configurable through environment variables with the `SYNAPSE_` prefix:
- `SYNAPSE_MAP_PHASE__INPUT_TRANSCRIPTS_DIR`: Directory for input transcripts
- `SYNAPSE_MAP_PHASE__OUTPUT_MAP_DIR`: Directory for map phase outputs
- `SYNAPSE_MAP_PHASE__LLM_MODEL`: LLM model to use for map phase
- `SYNAPSE_REDUCE_PHASE__OUTPUT_MARKDOWN_FILE`: Path for final output file
- `SYNAPSE_PROCESSING__CONCURRENCY`: Number of concurrent transcript processing tasks