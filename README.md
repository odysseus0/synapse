# Synapse: People Synthesis Using MapReduce

Synapse is a text-based meeting analysis tool that uses a MapReduce approach to process meeting transcripts and extract synthesized information about key individuals. It uses LLMs to identify and consolidate information about people across multiple meetings.

## Overview

Synapse processes plain text meeting transcripts to automatically:

1. Identify key individuals mentioned in meetings
2. Synthesize structured information about their contributions, action items, decisions, and interactions
3. Generate comprehensive profiles by consolidating information across multiple transcripts

The system uses a two-phase MapReduce approach:

- **Map Phase**: Processes each transcript individually, generating structured Markdown summaries for each key person
- **Reduce Phase**: Combines and synthesizes information across all transcripts to produce comprehensive profiles

## Features

- Processes plain text meeting transcripts (.txt files)
- Generates structured Markdown outputs
- Performs entity resolution to connect mentions of the same person across meetings
- Extracts action items, decisions, opinions, and interaction patterns
- Generates comprehensive, structured profiles of key individuals
- Supports concurrent processing of transcripts for efficiency

## Installation

### Prerequisites

- Python 3.12 or higher
- Access to Google's Gemini AI API

### Setup

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd synapse
   ```

2. Install dependencies:

   ```bash
   uv sync
   ```

3. Copy the environment template and configure your API keys:

   ```bash
   cp .env_template .env
   # Edit .env with your API keys and configuration
   ```

## Usage

1. Place your meeting transcript text files in the `transcripts` directory (or configure a custom directory in settings)

2. Run the map phase:

   ```bash
   uv run synapse.main
   ```

3. Outputs will be generated in the `map_outputs` directory (or your configured output directory)

## Configuration

Configuration can be set via environment variables or a `.env` file:

- `SYNAPSE_MAP_PHASE__INPUT_TRANSCRIPTS_DIR`: Directory containing transcript files (default: `./transcripts`)
- `SYNAPSE_MAP_PHASE__OUTPUT_MAP_DIR`: Directory for map phase outputs (default: `./map_outputs`)
- `SYNAPSE_MAP_PHASE__PROMPT_CONFIG_PATH`: Path to prompt configuration (default: `./prompt.yaml`)
- `SYNAPSE_PROCESSING__CONCURRENCY`: Maximum concurrent processes (default: `5`)
- `SYNAPSE_PROCESSING__LLM_MODEL`: LLM model to use (default: `google-gla:gemini-2.5-flash-preview-04-17`)

## Project Structure

- `src/synapse/`: Main Python package
  - `main.py`: Core execution logic
  - `config.py`: Configuration handling
- `prompt.yaml`: Prompt templates for LLM interactions
- `SPEC.md`: Detailed project specification
- `transcripts/`: Directory for input transcript files
- `map_outputs/`: Directory for map phase outputs

## License

This project is licensed under the MIT License.
