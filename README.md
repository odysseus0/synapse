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
   git clone https://github.com/odysseus0/synapse.git
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

4. Set up your Gemini API key:
   - Obtain an API key from Google AI Studio (https://makersuite.google.com/app/apikey)
   - Add your API key to the .env file: `GEMINI_API_KEY=your_api_key_here`

## Usage

1. Place your meeting transcript text files in your input directory (default: `./transcripts_sample/`)
   - Transcripts should be simple text files with speaker labels (e.g., "Speaker 1:", "John:", etc.)

2. Run the tool (processes both map and reduce phases):

   ```bash
   # Using the module directly with uv
   uv run -m synapse
   
   # OR using the installed package script
   python -m synapse
   ```

3. Results will be generated in:
   - Map phase results: Your configured map outputs directory (default: `./map_outputs/`)
   - Final synthesized profiles: Your configured output file location (default: `./processed_output/final_profiles.md`)

## Configuration

All directories, model choices, and processing parameters are configurable through environment variables in your `.env` file:

### Input/Output Locations
- `SYNAPSE_MAP_PHASE__INPUT_TRANSCRIPTS_DIR`: Directory containing transcript files (default: `./transcripts_sample`)
- `SYNAPSE_MAP_PHASE__OUTPUT_MAP_DIR`: Directory for map phase outputs (default: `./map_outputs`)
- `SYNAPSE_REDUCE_PHASE__OUTPUT_MARKDOWN_FILE`: Path for final output file (default: `./processed_output/final_profiles.md`)

### Model Selection
- `SYNAPSE_MAP_PHASE__LLM_MODEL`: LLM model for map phase (default: `google-gla:gemini-2.5-flash-preview-04-17`)
- `SYNAPSE_REDUCE_PHASE__LLM_MODEL`: LLM model for reduce phase (default: `google-gla:gemini-2.5-pro-preview-05-06`)

### Performance Settings
- `SYNAPSE_PROCESSING__CONCURRENCY`: Maximum concurrent transcript processing tasks (default: `5`)

The system will automatically create any output directories that don't exist.

## Project Structure

- `src/synapse/`: Main Python package
  - `main.py`: Core execution logic and entry point
  - `config.py`: Configuration management using Pydantic
  - `agents.py`: LLM agent prompts and configurations
  - `processors/`: Map and reduce processing modules
  - `exceptions.py`: Custom exception hierarchy
  - `logging.py`: Structured logging configuration
- `transcripts_sample/`: Example directory for input transcript files
- `SPEC.md`: Detailed project specification

## License

This project is licensed under the MIT License.