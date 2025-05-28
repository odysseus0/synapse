"""
Configuration module for Synapse.

This module defines configuration structures using Pydantic models and settings,
allowing for typed configuration with environment variable and .env file support.

Configuration can be set via environment variables with the SYNAPSE_ prefix
or in a .env file:
- SYNAPSE_MAP_PHASE__INPUT_TRANSCRIPTS_DIR: Directory for transcript files
- SYNAPSE_MAP_PHASE__OUTPUT_MAP_DIR: Directory for map phase outputs
- SYNAPSE_MAP_PHASE__LLM_MODEL: LLM model for map phase
- SYNAPSE_REDUCE_PHASE__OUTPUT_PROFILES_DIR: Directory for profile output files
- SYNAPSE_PROCESSING__CONCURRENCY: Maximum concurrent processes

Environment variables use double underscores (__) for nested config sections.
Environment variables take precedence over values defined in the .env file.
"""

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class MapPhaseConfig(BaseModel):
    """
    Configuration specific to the map phase.

    This model defines settings for the initial processing of individual transcripts,
    including input/output directories and LLM model specification.
    """

    llm_model: str = Field(
        default='google-gla:gemini-2.5-flash-preview-04-17', description='LLM model to use for processing'
    )
    input_transcripts_dir: str = Field(
        default='./transcripts_sample', description='Directory containing input .txt transcripts'
    )
    output_map_dir: str = Field(default='./map_outputs', description='Directory to save the map phase .md outputs')
    extraction_type: str = Field(default='newsletter', description='Type of extraction to perform')
    meetings_dir: str = Field(default='./data/meetings', description='Directory containing meeting transcripts')
    telegram_dir: str = Field(default='./data/telegram', description='Directory containing Telegram exports')


class ReducePhaseConfig(BaseModel):
    """
    Configuration specific to the reduce phase.

    This model defines settings for combining map outputs into the final synthesized
    profiles, including output location and LLM model specification.
    """

    output_profiles_dir: str = Field(
        default='./profiles', description='Directory to save individual profile Markdown files'
    )
    llm_model: str = Field(
        default='google-gla:gemini-2.5-flash-preview-04-17', description='LLM model to use for processing'
    )


class ProcessingConfig(BaseModel):
    """
    Configuration for processing parameters.

    This model defines general processing settings that apply to both map and reduce
    phases, such as concurrency limits.
    """

    concurrency: int = Field(
        default=10,
        description='Maximum number of concurrent processing tasks',
        ge=1,  # Ensures concurrency is at least 1
    )


class SynapseSettings(BaseSettings):
    """
    Main settings class for Synapse.

    This model combines all configuration sections and handles loading from
    environment variables with appropriate prefixes.
    """

    map_phase: MapPhaseConfig = Field(default_factory=MapPhaseConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    reduce_phase: ReducePhaseConfig = Field(default_factory=ReducePhaseConfig)

    # Configure pydantic-settings behavior using model_config
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        case_sensitive=False,
        extra='ignore',
        env_prefix='SYNAPSE_',
    )


settings = SynapseSettings()
