"""
Reduce phase processor for synthesizing information across transcripts.

Note on MapReduce Design:
    The current implementation uses a simplified reduce approach where all map outputs
    are concatenated and processed in a single LLM call. This works efficiently with
    Gemini's 1M context window for moderate-sized datasets.

    For larger datasets where outputs exceed model context limits, a true MapReduce
    implementation would be needed with:
    1. Partitioning by person/entity keys
    2. Parallel reducers for different partitions
    3. Hierarchical reduction for very large datasets

    The current architecture is designed to be extended to this approach in the future
    if/when output sizes exceed single-context processing capabilities.
"""

import re
from collections.abc import Awaitable, Callable
from datetime import datetime

import logfire
from trio import Path

from synapse.config import settings


def sanitize_filename(name: str) -> str:
    """
    Convert a person's name to a valid filename.

    Args:
        name: The person's name

    Returns:
        A sanitized version of the name suitable for use as a filename
    """
    # Replace spaces with underscores and remove any characters not allowed in filenames
    sanitized = re.sub(r'[^\w\-\.]', '_', name).strip('_')
    # Convert to lowercase for better cross-platform compatibility
    return sanitized.lower()


async def sort_map_files(markdown_files_list: list[Path]) -> list[Path]:
    """
    Sort map files chronologically when possible, falling back to alphabetical.

    Args:
        markdown_files_list: List of Path objects to map output files

    Returns:
        List of Path objects sorted first by date (for timestamp-named files)
        and then alphabetically for files without valid timestamps
    """
    # Parse dates from filenames where possible
    parsed_files: list[tuple[datetime, Path]] = []
    unparseable_files: list[Path] = []

    for path in markdown_files_list:
        try:
            # Try to extract timestamp from filename (format: "YYYY-MM-DD HH_MM")
            dt = datetime.strptime(path.name[:16], '%Y-%m-%d %H_%M')
            parsed_files.append((dt, path))
        except ValueError:
            logfire.warn(f'Could not parse timestamp from filename: {path.name}')
            unparseable_files.append(path)

    # Sort chronological files by date, then combine with alphabetically sorted unparseable files
    sorted_parsed = sorted(parsed_files, key=lambda x: x[0])  # Sort by datetime
    sorted_unparseable = sorted(unparseable_files)

    # Return files in order: chronological first, then alphabetical
    return [path for _, path in sorted_parsed] + sorted_unparseable


async def run_reduce_phase(
    reduce_fn: Callable[[str], Awaitable[str]],
) -> tuple[bool, int]:
    """
    Reads map phase outputs, concatenates them, and runs them through the provided reduce function.

    Args:
        reduce_fn: Async function that takes concatenated content and returns reduced output.

    Returns:
        A tuple containing (success: bool, processed_files_count: int)
    """
    # Use module-level settings
    map_output_dir = Path(settings.map_phase.output_map_dir)
    output_dir = Path(settings.reduce_phase.output_dir)

    logfire.info('--- Starting Reduce Phase ---')
    logfire.info(f'Reading map outputs from: {map_output_dir}')
    logfire.info(f'Target directory for outputs: {output_dir}')

    # Find and sort all map output files
    markdown_files: list[Path] = [path for path in await map_output_dir.glob('*.map.md')]

    if not markdown_files:
        logfire.warn(f'No .map.md files found in {map_output_dir}. Skipping reduce agent processing.')
        logfire.info('--- Reduce Phase Complete (Skipped due to no input map files) ---')
        return False, 0

    # Sort files chronologically when possible
    sorted_files: list[Path] = await sort_map_files(markdown_files)

    # Read and concatenate non-empty file contents
    raw_map_outputs: list[str] = []
    for file_path in sorted_files:
        content = await file_path.read_text(encoding='utf-8')
        if content.strip():  # Skip empty content
            raw_map_outputs.append(content)

    if not raw_map_outputs:
        logfire.warn(f'No non-empty content read from .map.md files in {map_output_dir}. Skipping reduce agent.')
        logfire.info('--- Reduce Phase Complete (Skipped due to no map content) ---')
        return False, 0

    # Process content with the reduce agent
    with logfire.span('reduce_agent_processing', files_count=len(raw_map_outputs)):
        # Concatenate content with double newlines between file contents for separation
        concatenated_map_data = '\n\n'.join(raw_map_outputs)
        logfire.info(f'Processing {len(raw_map_outputs)} map outputs. Total size: {len(concatenated_map_data)} chars.')

        try:
            # Run the reduce function
            result = await reduce_fn(concatenated_map_data)

            if not result:
                logfire.info('Reduce function returned empty output.')
                return False, len(raw_map_outputs)

            # Simple fixed output filename
            output_file = output_dir / 'newsletter.md'
            await output_dir.mkdir(exist_ok=True, parents=True)
            await output_file.write_text(result, encoding='utf-8')
            
            logfire.info(f'Reduce phase processed. Output saved to {output_file}')
            logfire.info('--- Reduce Phase Complete ---')

            return True, len(sorted_files)
        except Exception as e:
            logfire.error(f'Error during Reduce Agent processing: {e}', exc_info=True)
            logfire.info('--- Reduce Phase Failed ---')
            return False, len(raw_map_outputs)
