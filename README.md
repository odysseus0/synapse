# Synapse: Weekly Newsletter Generator

Synapse is a text analysis tool that uses a MapReduce approach to process meeting transcripts and Telegram conversations, generating comprehensive weekly newsletters. It uses LLMs to extract and synthesize key information across multiple sources.

## Overview

Synapse automatically generates weekly newsletters by processing:

- **Meeting Transcripts**: Extracts key decisions, project updates, action items, and notable discussions
- **Telegram Conversations**: Captures important announcements, technical discussions, shared resources, and community highlights

The system uses a two-phase MapReduce approach:

- **Map Phase**: Processes each input file individually to extract newsletter-worthy content
- **Reduce Phase**: Combines and synthesizes all extracted content into a cohesive weekly newsletter

## Features

- Processes plain text meeting transcripts and Telegram exports
- Generates structured, readable newsletters in Markdown format
- Supports concurrent processing for efficiency
- Automatically categorizes content by importance and topic
- Creates newsletters optimized for 5-10 minute reading time

## Installation

### Prerequisites

- Python 3.12 or higher
- Access to Google's Gemini AI API (or other compatible LLM)

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/synapse.git
   cd synapse
   ```

2. Install dependencies using UV (Python package manager):

   ```bash
   uv sync
   ```

3. Copy the environment template and configure your API keys:

   ```bash
   cp .env_template .env
   # Edit .env with your API keys and configuration
   ```

4. Set up your API key:
   - Obtain an API key from Google AI Studio (https://makersuite.google.com/app/apikey)
   - Add your API key to the .env file: `GEMINI_API_KEY=your_api_key_here`

## Usage

### Directory Structure

Organize your input files by type:

```
data/
├── meetings/       # Place meeting transcript files here
│   ├── 2025-04-28 all-hands.txt
│   └── 2025-04-30 engineering.txt
└── telegram/       # Place Telegram export files here
    └── telegram_week_2025-04-28.txt
```

### Running the Newsletter Generator

Generate a complete newsletter:

```bash
# Process all files and generate newsletter
uv run -m synapse.main

# Process only the map phase
uv run -m synapse.main --phase map

# Process only the reduce phase (using existing map outputs)
uv run -m synapse.main --phase reduce
```

### Output

- Map phase results: `./map_outputs/` (intermediate extracts)
- Final newsletter: `./output/newsletter.md`

## Configuration

All settings can be configured through environment variables in your `.env` file:

### Input/Output Locations
- `SYNAPSE_MAP_PHASE__MEETINGS_DIR`: Directory for meeting transcripts (default: `./data/meetings`)
- `SYNAPSE_MAP_PHASE__TELEGRAM_DIR`: Directory for Telegram exports (default: `./data/telegram`)
- `SYNAPSE_MAP_PHASE__OUTPUT_MAP_DIR`: Directory for map phase outputs (default: `./map_outputs`)
- `SYNAPSE_REDUCE_PHASE__OUTPUT_DIR`: Directory for final newsletter (default: `./output`)

### Model Selection
- `SYNAPSE_MAP_PHASE__LLM_MODEL`: LLM model for extraction (default: `google-gla:gemini-2.5-flash-preview-04-17`)
- `SYNAPSE_REDUCE_PHASE__LLM_MODEL`: LLM model for synthesis (default: `google-gla:gemini-2.5-flash-preview-04-17`)

### Performance Settings
- `SYNAPSE_PROCESSING__CONCURRENCY`: Maximum concurrent processing tasks (default: `10`)

## Newsletter Structure

The generated newsletter follows a structured template with sections for highlights, progress, discussions, heads-up items, human interest, and resources. The complete newsletter template is defined in [`src/synapse/agents.py`](src/synapse/agents.py) in the `NEWSLETTER_REDUCE_USER_MESSAGE_TEMPLATE`.

## Project Structure

- `src/synapse/`: Main Python package
  - `main.py`: Core execution logic and entry point
  - `config.py`: Configuration management using Pydantic
  - `agents.py`: LLM agent configurations and newsletter templates
  - `processors/`: Map and reduce processing modules
    - `map.py`: Extracts content from individual files
    - `reduce.py`: Synthesizes final newsletter
    - `extractors.py`: Extraction functions for different file types
  - `parsers/`: File parsing utilities
    - `telegram.py`: Telegram export parser
  - `exceptions.py`: Custom exception hierarchy
  - `logging.py`: Structured logging configuration

## Development

### Running Tests

```bash
# Run all tests
uv run -m pytest

# Run with verbose output
uv run -m pytest -v
```

### Linting and Type Checking

```bash
# Run linter
uv run ruff check src/

# Auto-fix linting issues
uv run ruff check --fix src/

# Run type checking
uv run pyright
```

## License

This project is licensed under the MIT License.