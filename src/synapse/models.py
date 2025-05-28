"""Models and Pydantic data structures used throughout Synapse."""

from pydantic import BaseModel, Field


class ProfileMetadata(BaseModel):
    """Structured metadata about a person identified in meeting transcripts."""

    name: str = Field(description='The canonical/best name for this person')
    aliases: list[str] = Field(default_factory=list, description='List of all name variations observed in transcripts')
    role: str = Field(
        description='Their inferred organizational role or position, which may be internal or external to the organization'
    )
    mentioned_in_sources: list[str] = Field(
        default_factory=list, description='List of transcript filenames where this person appears'
    )
    topics: list[str] = Field(
        default_factory=list, description='List of key topics this person discussed or was involved with'
    )


class Profile(BaseModel):
    """Complete profile information for a person."""

    metadata: ProfileMetadata = Field(description='The structured metadata for this person')
    content: str = Field(description='Full markdown content of the profile with all sections')
