"""
Extraction functions for different content types and use cases.

Each extraction function takes (content, filename) and returns extracted text.
"""

from synapse.agents import MAP_USER_MESSAGE_TEMPLATE, map_agent


async def extract_person_profiles(content: str, filename: str) -> str:
    """Extract person profiles from transcript content."""
    user_prompt = MAP_USER_MESSAGE_TEMPLATE.format(
        transcript_text=content,
        transcript_filename=filename
    )
    result = await map_agent.run(user_prompt)
    return result.output


# Newsletter extraction functions will go here
# async def extract_newsletter_meeting(content: str, filename: str) -> str:
#     """Extract newsletter content from meeting transcripts."""
#     pass