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

class ReducePhaseConfig(BaseModel):
    """Configuration specific to the reduce phase."""
    output_markdown_file: str = Field(
        default='./processed_output/final_profiles.md', # Changed default location
        description='Path to save the final combined Markdown output'
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
    reduce_phase: ReducePhaseConfig = Field(default_factory=ReducePhaseConfig)

    # Configure pydantic-settings behavior using model_config
    model_config = SettingsConfigDict(
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        case_sensitive=False,
        extra='ignore',
        env_prefix='SYNAPSE_'
    )