"""
File I/O operations for handling transcript and output files.
"""
import logfire
import yaml
from trio import Path

from synapse.exceptions import PromptConfigInvalid, PromptConfigNotFound
from synapse.models.prompts import PromptConfig


async def load_prompt_config(filepath: Path) -> PromptConfig:
    """
    Loads prompt configuration from a YAML file and validates with Pydantic.
    
    Args:
        filepath: Path to the YAML configuration file
        
    Returns:
        Validated PromptConfig object
        
    Raises:
        PromptConfigNotFound: If the file doesn't exist
        PromptConfigInvalid: If the file doesn't match the expected schema
    """
    import trio
    from pydantic import ValidationError
    
    try:
        async with await trio.open_file(filepath, 'r', encoding='utf-8') as f:
            content = await f.read()
            data = yaml.safe_load(content)
        
        if not data:
            raise ValueError('Prompt config file is empty.')

        # Validate and parse the data using Pydantic model
        config = PromptConfig(**data)
        
        logfire.info('Successfully loaded and validated prompt config from {filepath}', filepath=str(filepath))
        return config
    except FileNotFoundError:
        raise PromptConfigNotFound(f'Prompt configuration file not found: {filepath}')
    except ValidationError as e:
        raise PromptConfigInvalid(f'Error validating prompt configuration from {filepath}: {e}')