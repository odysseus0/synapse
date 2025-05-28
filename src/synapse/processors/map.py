"""
Map phase processor for analyzing individual transcripts.
"""

from collections.abc import Awaitable, Callable

import logfire
import trio
from rich.progress import Progress
from trio import Path

from synapse.config import settings


async def run_map_phase(
    files: list[Path],
    extract_fn: Callable[[str, str], Awaitable[str]],
) -> tuple[int, int]:
    """
    Processes files concurrently to generate Map phase Markdown outputs.u

    Uses configuration from module-level settings.

    Args:
        files: List of file paths to process.
        extract_fn: Async function that takes (content, filename) and returns extracted text.

    Returns:
        A tuple containing (number_of_files_processed, number_of_files_failed).
    """
    # Use module-level settings
    concurrency = settings.processing.concurrency
    output_dir = Path(settings.map_phase.output_map_dir)

    logfire.info(f'Processing {len(files)} files')
    processed_stats = {'processed': 0, 'failed': 0}
    send_channel, receive_channel = trio.open_memory_channel[Path](0)

    async def map_worker(worker_receive_channel: trio.MemoryReceiveChannel[Path]):
        """Worker task to process one file."""
        async for file_path in worker_receive_channel:
            relative_path_str = str(file_path)
            output_filename = file_path.stem + '.map.md'
            output_path = output_dir / output_filename

            with logfire.span('process_file_map', filepath=relative_path_str):
                try:
                    # Read and check file content
                    file_text = await file_path.read_text(encoding='utf-8')
                    file_text = file_text.strip()

                    if not file_text:
                        logfire.warn('Skipping empty file: {filepath}', filepath=relative_path_str)
                        continue  # Skip empty files

                    # Process with provided extract_fn
                    map_output_content = await extract_fn(file_text, file_path.name)

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
        map_task_id = progress.add_task('[cyan]Mapping files...', total=len(files))

        # Ensure output directory exists (direct approach)
        await output_dir.mkdir(exist_ok=True, parents=True)
        logfire.info('Ensured output directory exists: {dir_path}', dir_path=str(output_dir))

        async with trio.open_nursery() as nursery:
            # Start workers
            for _ in range(concurrency):
                nursery.start_soon(map_worker, receive_channel.clone())

            # Send file paths to workers
            async with send_channel:
                for path in files:
                    await send_channel.send(path)

    return processed_stats['processed'], processed_stats['failed']
