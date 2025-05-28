"""
Map phase processor for analyzing individual transcripts.
"""

import logfire
import trio
from rich.progress import Progress
from trio import Path

from synapse.agents import MAP_USER_MESSAGE_TEMPLATE, map_agent
from synapse.config import settings


async def run_map_phase() -> tuple[int, int]:
    """
    Processes transcript files concurrently to generate Map phase Markdown outputs.

    Uses configuration from module-level settings.

    Returns:
        A tuple containing (number_of_files_processed, number_of_files_failed).
    """
    # Use module-level settings
    concurrency = settings.processing.concurrency
    output_dir = Path(settings.map_phase.output_map_dir)
    input_dir = Path(settings.map_phase.input_transcripts_dir)

    # Get transcript files from the configured input directory
    transcript_paths = [p for p in await input_dir.glob('*.txt')]
    logfire.info(f'Found {len(transcript_paths)} transcript files in {input_dir}')
    processed_stats = {'processed': 0, 'failed': 0}
    send_channel, receive_channel = trio.open_memory_channel[Path](0)

    async def map_worker(worker_receive_channel: trio.MemoryReceiveChannel[Path]):
        """Worker task to process one transcript file."""
        async for transcript_path in worker_receive_channel:
            relative_path_str = str(transcript_path)
            output_filename = transcript_path.name.replace('.txt', '.map.md')
            output_path = output_dir / output_filename

            with logfire.span('process_transcript_map', filepath=relative_path_str):
                try:
                    # Read and check transcript content
                    transcript_text = await transcript_path.read_text(encoding='utf-8')
                    transcript_text = transcript_text.strip()

                    if not transcript_text:
                        logfire.warn('Skipping empty transcript file: {filepath}', filepath=relative_path_str)
                        continue  # Skip empty files

                    # Process with module-level agent
                    user_prompt = MAP_USER_MESSAGE_TEMPLATE.format(
                        transcript_text=transcript_text, transcript_filename=transcript_path.name
                    )
                    result = await map_agent.run(user_prompt)
                    map_output_content = result.output

                    # Save output if useful
                    if (
                        map_output_content
                        and map_output_content.strip() != 'No key persons identified in this transcript.'
                    ):
                        await output_path.write_text(map_output_content, encoding='utf-8')
                        logfire.info('Map output saved: {output_path}', output_path=str(output_path))
                    else:
                        logfire.info('No key persons identified in: {filepath}', filepath=relative_path_str)

                    processed_stats['processed'] += 1

                except Exception as e:
                    processed_stats['failed'] += 1
                    logfire.error(
                        'Error processing transcript {filepath}: {error}',
                        filepath=relative_path_str,
                        error=str(e),
                        exc_info=True,
                    )
                finally:
                    progress.update(map_task_id, advance=1)

    with Progress() as progress:
        map_task_id = progress.add_task('[cyan]Mapping transcripts...', total=len(transcript_paths))

        # Ensure output directory exists (direct approach)
        await output_dir.mkdir(exist_ok=True, parents=True)
        logfire.info('Ensured output directory exists: {dir_path}', dir_path=str(output_dir))

        async with trio.open_nursery() as nursery:
            # Start workers
            for _ in range(concurrency):
                nursery.start_soon(map_worker, receive_channel.clone())

            # Send transcript paths to workers
            async with send_channel:
                for path in transcript_paths:
                    await send_channel.send(path)

    return processed_stats['processed'], processed_stats['failed']
