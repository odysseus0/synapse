"""
Synapse: Main execution module.

This module is the entry point for the Synapse application, orchestrating
the map and reduce phases for analyzing meeting transcripts.
"""
import logfire
import trio
from trio import Path

from synapse.config import settings
from synapse.exceptions import (
    EmptyInputDirectory,
    FileProcessingError,
    ReducePhaseError,
    SynapseError,
)
from synapse.logging import configure_logging
from synapse.processors.map import run_map_phase
from synapse.processors.reduce import run_reduce_phase


async def main():
    """
    Main async execution function for the Synapse processing pipeline.

    This coordinates both map and reduce phases of the transcript analysis:
    1. Map phase: Process individual transcripts to identify key people
    2. Reduce phase: Synthesize information across all transcripts
    """
    # Configure logging
    configure_logging()

    logfire.info('--- Starting Project Synapse: Map Phase ---')

    # --- Configuration Setup ---
    input_dir = Path(settings.map_phase.input_transcripts_dir)
    output_dir = Path(settings.map_phase.output_map_dir)

    logfire.info('Input directory: {input_dir}', input_dir=str(input_dir))
    logfire.info('Output directory: {output_dir}', output_dir=str(output_dir))
    logfire.info('Concurrency limit: {concurrency}', concurrency=settings.processing.concurrency)
    logfire.info('Using Map LLM model: {model}', model=settings.map_phase.llm_model)
    logfire.info('Using Reduce LLM model: {model}', model=settings.reduce_phase.llm_model)
    # --- End Configuration Setup ---

    # Ensure directories exist
    try:
        await output_dir.mkdir(exist_ok=True, parents=True)
        logfire.info('Ensured output directory exists: {dir_path}', dir_path=str(output_dir))

        # Check if input directory has files
        input_files = [p for p in await input_dir.glob('*.txt')]
        if not input_files:
            raise EmptyInputDirectory(f'No .txt files in {input_dir}')
    except Exception as e:
        raise FileProcessingError(f'Error setting up directories: {e}')

    # Run the map phase processing
    with logfire.span('run_map_phase'):
        processed_count, failed_count = await run_map_phase()

    # --- Summary ---
    logfire.info('--- Map Phase Complete ---')
    logfire.info('Successfully processed: {count}', count=processed_count)
    logfire.info('Failed to process: {count}', count=failed_count)
    logfire.info('Map outputs saved to: {output_dir}', output_dir=str(output_dir))
    logfire.info('--------------------------')

    # --- Reduce Phase ---
    try:
        success, processed_files = await run_reduce_phase()
        logfire.info('Reduce phase success: {success}, processed files: {count}',
                    success=success, count=processed_files)
    except Exception as e:
        raise ReducePhaseError(f'Error during Reduce Phase: {e}')
    # --- End Reduce Phase ---


def run_main():
    """Entry point for the CLI script."""
    try:
        trio.run(main)
    except SynapseError as err:
        logfire.error('Fatal error: {msg}', msg=str(err), exc_info=True)
        raise SystemExit(1) from err


if __name__ == '__main__':
    run_main()