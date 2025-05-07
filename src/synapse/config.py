from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

# --- Define the nested config models (Structure remains the same) ---
# These are standard Pydantic models defining the structure of your config sections.

class MapPhaseConfig(BaseModel):
    """Configuration specific to the map phase."""
    input_transcripts_dir: str = Field(
        default='./transcripts',
        description='Directory containing input .txt transcripts'
    )
    output_map_dir: str = Field(
        default='./map_outputs',
        description='Directory to save the map phase .md outputs'
    )
    prompt_config_path: str = Field(
        default='./prompt.yaml',
        description='Path to the YAML file containing prompt configuration'
    )

class ProcessingConfig(BaseModel):
    """Configuration for processing parameters."""
    concurrency: int = Field(
        default=5,
        description='Maximum number of concurrent processing tasks',
        ge=1 # Ensures concurrency is at least 1
    )
    llm_model: str = Field(
        default='google-gla:gemini-2.5-flash-preview-04-17',
        description='LLM model to use for processing'
    )

class SynapseSettings(BaseSettings):
    map_phase: MapPhaseConfig = Field(default_factory=MapPhaseConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    reduce_phase: "ReducePhaseConfig" = Field(default_factory=lambda: ReducePhaseConfig())

    # Configure pydantic-settings behavior using model_config
    model_config = SettingsConfigDict(
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        case_sensitive=False,
        extra='ignore',
        env_prefix='SYNAPSE_'
    )

# --- New Reduce Phase Config ---

# Placing the class definition here **after** its first usage above avoids forward reference issues at runtime because
# pydantic will resolve the annotation lazily. However, to satisfy static checkers and keep readability high we still
# declare the class explicitly just below.

class ReducePhaseConfig(BaseModel):
    """Configuration specific to the reduce phase."""

    # Directory where the map outputs (.map.md) are located. By default we reuse the map output directory so users can
    # override the location if they move/copy the files elsewhere before running the reduce phase standalone.
    input_map_dir: str = Field(
        default='./map_outputs',
        description='Directory containing .map.md files produced by the map phase'
    )

    # Path where the final consolidated Markdown profiles will be written.
    output_reduce_file: str = Field(
        default='./reduce_outputs/final_profiles.md',
        description='File path to save the final consolidated Markdown profiles'
    )

    # The prompt config path for the reduce phase. Default to the same YAML file used for the map phase to keep things
    # DRY, but allow overriding in case users split prompts into separate files later.
    prompt_config_path: str = Field(
        default='./prompt.yaml',
        description='Path to the YAML file containing reduce prompt configuration'
    )