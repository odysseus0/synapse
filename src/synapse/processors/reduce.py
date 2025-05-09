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
from datetime import datetime

import logfire
from pydantic_ai import Agent
from trio import Path


async def run_reduce_phase(
    map_output_dir: Path,
    output_file: Path,
    model_name: str,
    system_prompt: str,
    user_template: str
) -> tuple[bool, int]:
    """
    Reads map phase outputs, concatenates them, runs them through a reduce agent,
    and saves the final synthesized Markdown output.
    
    Args:
        map_output_dir: Directory containing map phase output files
        output_file: Path to write the final output file
        model_name: Name of the LLM model to use
        system_prompt: System prompt for the reduce agent
        user_template: User prompt template for the reduce agent
        
    Returns:
        A tuple containing (success: bool, processed_files_count: int)
    """
    logfire.info('--- Starting Reduce Phase ---')
    logfire.info(f'Reading map outputs from: {map_output_dir}')
    logfire.info(f'Target for reduced output: {output_file}')

    async def sort_map_files(markdown_files_list: list[Path]) -> list[Path]:
        """Sort map files chronologically when possible, falling back to alphabetical."""
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
        concatenated_map_data = '\\n\\n'.join(raw_map_outputs)
        logfire.info(f'Processing {len(raw_map_outputs)} map outputs. Total size: {len(concatenated_map_data)} chars.')

        # Initialize the Reduce Agent
        reduce_agent = Agent(
            model=model_name,
            instructions=system_prompt,
        )

        # Format and run the prompt
        reduce_user_prompt = user_template.replace(
            '{{CONCATENATED_MARKDOWN_BLOCKS_HERE}}',
            concatenated_map_data
        )

        try:
            result = await reduce_agent.run(reduce_user_prompt)
            final_reduced_output = result.output if result and result.output else ''

            if not final_reduced_output.strip():
                logfire.info('Reduce agent returned empty output.')
                return False, len(raw_map_outputs)

            # Ensure output directory and write the file
            await output_file.parent.mkdir(exist_ok=True, parents=True)
            logfire.info('Ensured output directory exists: {dir_path}', dir_path=str(output_file.parent))
            await output_file.write_text(final_reduced_output, encoding='utf-8')
            
            logfire.info(f'Reduce phase processed. Output at: {output_file}')
            logfire.info('--- Reduce Phase Complete ---')
            
            return True, len(sorted_files)
        except Exception as e:
            logfire.error(f'Error during Reduce Agent processing: {e}', exc_info=True)
            logfire.info('--- Reduce Phase Failed ---')
            return False, len(raw_map_outputs)