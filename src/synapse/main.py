import sys

import logfire
import trio
import yaml
from pydantic import BaseModel, ValidationError
from pydantic_ai import Agent
from rich.progress import Progress
from trio import Path  # Use trio.Path for all file operations

from synapse.config import SynapseSettings

logfire.configure(scrubbing=False, token='pylf_v1_us_h899YsnvxK4jGtjBtcD9fmD2B8dJFKLMsWGpJq1T4Xnn')
logfire.instrument_pydantic_ai()


class PromptDetail(BaseModel):
    system_message: str
    user_message_template: str


class PromptConfig(BaseModel):
    map_prompt: PromptDetail
    reduce_prompt: PromptDetail


async def load_prompt_config(filepath: Path) -> PromptConfig:
    """Loads prompt configuration from a YAML file and validates with Pydantic."""
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
        logfire.error('Prompt configuration file not found: {filepath}', filepath=str(filepath))
        sys.exit(1)
    except ValidationError as e:
        logfire.error('Error validating prompt configuration from {filepath}: {error}', filepath=str(filepath), error=str(e), exc_info=True)
        sys.exit(1)
    except Exception as e:
        logfire.error('Error loading prompt configuration from {filepath}: {error}', filepath=str(filepath), error=str(e), exc_info=True)
        sys.exit(1)

# Pydantic model is not needed for the AI output here,
# as we are instructing the AI to return raw Markdown text.

async def run_map_phase(
    transcript_paths: list[Path],
    output_dir: Path,
    agent: Agent,
    prompt_template: str,
    concurrency: int
) -> tuple[int, int]:
    """
    Processes transcript files concurrently to generate Map phase Markdown outputs.

    Args:
        transcript_paths: List of paths to input transcript files.
        output_dir: Path to the directory where map outputs will be saved.
        agent: The configured pydantic_ai Agent.
        prompt_template: The user message template string with placeholders.
        concurrency: Maximum number of concurrent processing tasks.

    Returns:
        A tuple containing (number_of_files_processed, number_of_files_failed).
    """
    processed_stats = {'processed': 0, 'failed': 0}
    send_channel, receive_channel = trio.open_memory_channel[Path](0)

    async def map_worker(worker_receive_channel: trio.MemoryReceiveChannel[Path]):
        """Worker task to process one transcript file."""
        async for transcript_path in worker_receive_channel:
            relative_path_str = str(transcript_path)
            output_filename = transcript_path.name.replace('.txt', '.map.md') # Simple naming convention
            output_path = output_dir / output_filename

            with logfire.span('process_transcript_map', filepath=relative_path_str):
                try:
                    transcript_text = await transcript_path.read_text(encoding='utf-8')
                    transcript_text = transcript_text.strip()

                    if not transcript_text:
                        logfire.warn(
                            'Skipping empty transcript file: {filepath}',
                            filepath=relative_path_str
                        )
                        progress.update(map_task_id, advance=1)
                        continue # Skip empty files

                    # Format the user prompt
                    user_prompt = prompt_template.format(
                        transcript_text=transcript_text,
                        transcript_filename=transcript_path.name
                    )

                    result = await agent.run(user_prompt)
                    map_output_content = result.output

                    if not map_output_content or map_output_content.strip() == 'No key persons identified in this transcript.':
                         logfire.info(
                             'No key persons identified or empty output for: {filepath}',
                             filepath=relative_path_str
                         )
                    else:
                        await output_path.write_text(map_output_content, encoding='utf-8')
                        logfire.info(
                            'Successfully generated map output: {output_path}',
                            output_path=str(output_path)
                        )

                    processed_stats['processed'] += 1

                except Exception as e:
                    processed_stats['failed'] += 1
                    logfire.error(
                        'Error processing transcript {filepath}: {error}',
                        filepath=relative_path_str,
                        error=str(e),
                        exc_info=True
                    )
                finally:
                    progress.update(map_task_id, advance=1)


    with Progress() as progress:
        map_task_id = progress.add_task('[cyan]Mapping transcripts...', total=len(transcript_paths))

        # Ensure output directory exists (async)
        await output_dir.mkdir(exist_ok=True, parents=True)
        logfire.info('Ensured output directory exists: {output_dir}', output_dir=str(output_dir))

        async with trio.open_nursery() as nursery:
            for _ in range(concurrency):
                nursery.start_soon(map_worker, receive_channel.clone())

            # Send transcript paths to workers
            async with send_channel:
                for path in transcript_paths:
                    await send_channel.send(path)

    return processed_stats['processed'], processed_stats['failed']


async def run_reduce_phase(
    map_output_paths: list[Path],
    final_output_path: Path,
    agent: Agent,
    user_template: str,
) -> None:
    """Runs the Reduce phase by concatenating map outputs and invoking the LLM.

    Args:
        map_output_paths: List of .map.md files generated by the Map phase.
        final_output_path: Destination markdown file for consolidated profiles.
        agent: Configured pydantic_ai Agent for reduce prompt.
        user_template: Reduce phase user message template with the placeholder
            ``{{CONCATENATED_MARKDOWN_BLOCKS_HERE}}``.
    """

    if not map_output_paths:
        logfire.warning('No map outputs provided to reduce phase. Skipping reduce step.')
        return

    # Read and concatenate map outputs
    concatenated_blocks: list[str] = []
    for path in map_output_paths:
        try:
            content = await path.read_text(encoding='utf-8')
            if content.strip():
                concatenated_blocks.append(content.strip())
        except Exception as e:
            logfire.error('Failed to read map output {file}: {error}', file=str(path), error=str(e), exc_info=True)

    if not concatenated_blocks:
        logfire.warning('All map outputs were empty. Skipping reduce phase.')
        return

    concatenated_markdown = '\n\n'.join(concatenated_blocks)

    # Insert the concatenated blocks into the template
    if '{{CONCATENATED_MARKDOWN_BLOCKS_HERE}}' not in user_template:
        logfire.warn('Reduce prompt template missing placeholder for concatenated blocks. Proceeding with simple append.')
        user_prompt = f"{user_template}\n\n{concatenated_markdown}"
    else:
        user_prompt = user_template.replace('{{CONCATENATED_MARKDOWN_BLOCKS_HERE}}', concatenated_markdown)

    # Invoke LLM
    try:
        result = await agent.run(user_prompt)
        reduce_output_content = result.output
    except Exception as e:
        logfire.error('Error during reduce phase LLM call: {error}', error=str(e), exc_info=True)
        return

    # Ensure target directory exists
    await final_output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    try:
        await final_output_path.write_text(reduce_output_content, encoding='utf-8')
        logfire.info('Reduce phase output saved to: {output}', output=str(final_output_path))
    except Exception as e:
        logfire.error('Failed to write reduce phase output: {error}', error=str(e), exc_info=True)


async def main():
    """Main execution function for the Map Phase."""
    global config
    
    # Load configuration asynchronously
    config = SynapseSettings()
    
    logfire.info('--- Starting Project Synapse: Map Phase ---')

    # --- Configuration Setup ---
    # Use the configuration loaded from config.py
    input_dir = Path(config.map_phase.input_transcripts_dir)
    output_dir = Path(config.map_phase.output_map_dir)
    
    # Make sure prompt_config_path is always a Path, not None
    prompt_config_path = Path(config.map_phase.prompt_config_path)
    
    concurrency = config.processing.concurrency
    model_name = config.processing.llm_model
    
    logfire.info('Input directory: {input_dir}', input_dir=str(input_dir))
    logfire.info('Output directory: {output_dir}', output_dir=str(output_dir))
    logfire.info('Prompt config path: {prompt_config_path}', prompt_config_path=str(prompt_config_path))
    logfire.info('Concurrency limit: {concurrency}', concurrency=concurrency)
    logfire.info('Using LLM model: {model}', model=model_name)
    # --- End Configuration Setup ---

    # Load prompt configuration
    prompt_config_model = await load_prompt_config(prompt_config_path)
    system_prompt = prompt_config_model.map_prompt.system_message
    user_template = prompt_config_model.map_prompt.user_message_template

    # Initialize the Agent
    agent = Agent(
        model=model_name,
        instructions=system_prompt,
    )

    # Find transcript files asynchronously
    try:
        transcript_files = [p for p in await input_dir.glob('*.txt')]
        if not transcript_files:
            logfire.warning(
                'No .txt files found in the input directory: {input_dir}',
                input_dir=str(input_dir)
            )
            sys.exit(0)
        logfire.info('Found {count} transcript files to process.', count=len(transcript_files))
    except Exception as e:
        logfire.error('Error scanning input directory {input_dir}: {error}', input_dir=str(input_dir), error=str(e), exc_info=True)
        sys.exit(1)

    # Run the map phase processing
    with logfire.span('run_map_phase'):
        processed_count, failed_count = await run_map_phase(
            transcript_paths=transcript_files,
            output_dir=output_dir,
            agent=agent,
            prompt_template=user_template,
            concurrency=concurrency
        )

    # --- Summary ---
    logfire.info('--- Map Phase Complete ---')
    logfire.info('Successfully processed: {count}', count=processed_count)
    logfire.info('Failed to process: {count}', count=failed_count)
    logfire.info('Map outputs saved to: {output_dir}', output_dir=str(output_dir))

    # ----------------- Reduce Phase -----------------
    logfire.info('--- Starting Reduce Phase ---')

    # Locate all generated map outputs
    try:
        map_output_files = [p for p in await output_dir.glob('*.map.md')]
        if not map_output_files:
            logfire.warning('No map outputs (.map.md) found to feed into Reduce phase inside {dir}', dir=str(output_dir))
        else:
            logfire.info('Found {count} map output files for reduce phase.', count=len(map_output_files))
    except Exception as e:
        logfire.error('Error scanning map output directory {dir}: {error}', dir=str(output_dir), error=str(e), exc_info=True)
        sys.exit(1)

    # Load reduce prompt details
    reduce_system_prompt = prompt_config_model.reduce_prompt.system_message
    reduce_user_template = prompt_config_model.reduce_prompt.user_message_template

    reduce_agent = Agent(
        model=model_name,
        instructions=reduce_system_prompt,
    )

    reduce_output_path = Path(config.reduce_phase.output_file)

    with logfire.span('run_reduce_phase'):
        await run_reduce_phase(
            map_output_paths=map_output_files,
            final_output_path=reduce_output_path,
            agent=reduce_agent,
            user_template=reduce_user_template,
        )

    logfire.info('--- Reduce Phase Complete ---')
    logfire.info('Final consolidated profiles written to: {path}', path=str(reduce_output_path))
    logfire.info('--------------------------')

def run_main():
    """Entry point for the CLI script."""
    trio.run(main)

if __name__ == '__main__':
    trio.run(main)
