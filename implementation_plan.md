# Individual Profile Files Implementation Plan (Refined)

## Overview

This document outlines the plan to modify Synapse to generate individual markdown files for each profile rather than a single consolidated file. Each file will contain YAML frontmatter with structured metadata and the full markdown content for that profile.

The implementation leverages Pydantic AI's structured output capabilities to automatically parse LLM responses into structured data models.

## Implementation Steps

### 1. Configuration Updates ✅

- **File**: `/src/synapse/config.py`
- Replace `output_markdown_file` with `output_profiles_dir` in `ReducePhaseConfig`
- Set default to `./profiles`

### 2. Define Pydantic Models for Structured Output ✅

**File**: `/src/synapse/processors/reduce.py`

The models are already defined in the codebase:
- `ProfileMetadata`: Structured information about a person
- `Profile`: Complete profile information

### 3. Update reduce.py to Use Structured Output

**File**: `/src/synapse/processors/reduce.py`

Modify the `run_reduce_phase()` function to:
- Create an agent with `output_type=List[Profile]` parameter
- Process the structured response to write individual files for each profile
- Generate YAML frontmatter from the metadata
- Create profile filenames based on sanitized person names

### 4. Update Reduce Agent Prompt

**File**: `/src/synapse/agents.py`

Simplify the prompts to focus on the core information needed without duplicating structural details:
- Update `REDUCE_SYSTEM_PROMPT` to emphasize structured output
- Update `REDUCE_USER_MESSAGE_TEMPLATE` to remove complex formatting instructions
- Let Pydantic AI handle parsing and validating the response into our structured Profile objects

### 5. Update Agent Initialization

**File**: `/src/synapse/agents.py`

Modify the reduce agent initialization to use the structured output type:
```python
# Update the reduce agent initialization at the bottom of the file
reduce_agent = Agent(
    model=settings.reduce_phase.llm_model,
    instructions=REDUCE_SYSTEM_PROMPT,
    output_type=List[Profile]
)
```

### 6. Update Main Module for Profile Directory

**File**: `/src/synapse/main.py`

Ensure the main module correctly references the profiles directory:
- Update any references to the output file path to use the directory instead
- Add code to ensure the profiles directory exists

## Testing and Validation

1. Test with small sample of transcripts first
2. Verify correct parsing and file generation
3. Check that YAML frontmatter is valid
4. Ensure all profile content is preserved

## Why This Approach Works Better

1. **Leverages Pydantic AI's Strengths**: The LLM will parse its output directly into structured models
2. **Simplified Prompt**: Focus on information requirements, not structural details
3. **Type Safety**: Pydantic models ensure data validation
4. **Clean Separation**: Metadata in YAML frontmatter, content in markdown
5. **Improved Maintainability**: Easier to modify data structure without changing prompts
6. **Simplified Structure**: Using `List[Profile]` directly as the output type is cleaner than a wrapper class