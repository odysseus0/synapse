"""
Extraction functions for newsletter generation.

Each extraction function takes (content, filename) and returns extracted text.
"""

from collections.abc import Awaitable, Callable

from synapse.agents import (
    NEWSLETTER_MEETING_MAP_TEMPLATE,
    NEWSLETTER_REDUCE_USER_MESSAGE_TEMPLATE,
    NEWSLETTER_TELEGRAM_MAP_TEMPLATE,
    newsletter_meeting_map_agent,
    newsletter_reduce_agent,
    newsletter_telegram_map_agent,
)

# Type alias for extraction functions
ExtractionFunction = Callable[[str, str], Awaitable[str]]

# Type alias for reduce functions
ReduceFunction = Callable[[str], Awaitable[str]]


# Newsletter extraction functions
async def extract_newsletter_meeting(content: str, filename: str) -> str:
    """Extract newsletter content from meeting transcripts."""
    user_prompt = NEWSLETTER_MEETING_MAP_TEMPLATE.format(
        transcript_text=content,
        transcript_filename=filename
    )
    result = await newsletter_meeting_map_agent.run(user_prompt)
    return result.output


async def extract_newsletter_telegram(content: str, filename: str) -> str:
    """Extract newsletter content from Telegram discussions."""
    user_prompt = NEWSLETTER_TELEGRAM_MAP_TEMPLATE.format(
        transcript_text=content,
        transcript_filename=filename
    )
    result = await newsletter_telegram_map_agent.run(user_prompt)
    return result.output


def get_extraction_function(extraction_type: str, file_type: str) -> ExtractionFunction:
    """Get the appropriate extraction function based on extraction type and file type.
    
    Args:
        extraction_type: Type of extraction (only 'newsletter' supported)
        file_type: Type of file ('meeting', 'telegram')
        
    Returns:
        The appropriate extraction function
        
    Raises:
        ValueError: If extraction_type or file_type is unknown
    """
    if extraction_type == 'newsletter':
        if file_type == 'telegram':
            return extract_newsletter_telegram
        elif file_type == 'meeting':
            return extract_newsletter_meeting
        else:
            raise ValueError(f'Unknown file type: {file_type}')
    else:
        raise ValueError(f'Unknown extraction type: {extraction_type}')


# Reduce functions
async def reduce_newsletter(concatenated_content: str) -> str:
    """Reduce newsletter extracts into a final newsletter.
    
    Returns the complete newsletter markdown content.
    """
    # Format and run the prompt
    reduce_user_prompt = NEWSLETTER_REDUCE_USER_MESSAGE_TEMPLATE.replace(
        '{{CONCATENATED_NEWSLETTER_EXTRACTS}}', concatenated_content
    )
    
    # Run the newsletter reduce agent
    result = await newsletter_reduce_agent.run(reduce_user_prompt)
    
    return result.output


def get_reduce_function(extraction_type: str) -> ReduceFunction:
    """Get the appropriate reduce function based on extraction type.
    
    Args:
        extraction_type: Type of extraction (only 'newsletter' supported)
        
    Returns:
        The appropriate reduce function
        
    Raises:
        ValueError: If extraction_type is unknown
    """
    if extraction_type == 'newsletter':
        return reduce_newsletter
    else:
        raise ValueError(f'Unknown extraction type: {extraction_type}')
