"""
Synapse: Main execution module.

This module is the entry point for the Synapse application, orchestrating
the map and reduce phases for analyzing meeting transcripts.
"""

import enum

import logfire
import trio
import typer
from trio import Path

from synapse.config import settings
from synapse.exceptions import (
    FileProcessingError,
    ReducePhaseError,
    SynapseError,
)
from synapse.logging import configure_logging
from synapse.processors.extractors import get_extraction_function
from synapse.processors.map import run_map_phase
from synapse.processors.reduce import run_reduce_phase


class Phase(str, enum.Enum):
    MAP = 'map'
    REDUCE = 'reduce'
    BOTH = 'both'


async def setup_directories() -> None:
    """Set up output directories."""
    map_output_dir = Path(settings.map_phase.output_map_dir)
    profiles_dir = Path(settings.reduce_phase.output_profiles_dir)

    try:
        await map_output_dir.mkdir(exist_ok=True, parents=True)
        await profiles_dir.mkdir(exist_ok=True, parents=True)
        logfire.info('Ensured map output directory exists: {dir_path}', dir_path=str(map_output_dir))
        logfire.info('Ensured profiles directory exists: {dir_path}', dir_path=str(profiles_dir))
    except Exception as e:
        raise FileProcessingError(f'Error setting up directories: {e}')


async def run_map(check_inputs: bool = True) -> tuple[int, int]:
    """Run only the map phase."""
    if check_inputs:
        await setup_directories()

    logfire.info('--- Starting Project Synapse: Map Phase ---')
    extraction_type = settings.map_phase.extraction_type
    logfire.info('Using extraction type: {type}', type=extraction_type)
    
    # Define directories and their file types
    directories = [
        (settings.map_phase.meetings_dir, 'meeting'),
        (settings.map_phase.telegram_dir, 'telegram'),
    ]
    
    total_processed = 0
    total_failed = 0
    
    # Process each directory with its specific file type
    for dir_path, file_type in directories:
        directory = trio.Path(dir_path)
        if not await directory.exists():
            continue
            
        files = [p for p in await directory.glob('*.txt')]
        if not files:
            continue
            
        logfire.info('Processing {count} {type} files', count=len(files), type=file_type)
        extraction_func = get_extraction_function(extraction_type, file_type)
        
        with logfire.span(f'process_{file_type}'):
            processed, failed = await run_map_phase(files, extraction_func)
            total_processed += processed
            total_failed += failed

    logfire.info('--- Map Phase Complete ---')
    logfire.info('Successfully processed: {count}', count=total_processed)
    logfire.info('Failed to process: {count}', count=total_failed)

    return total_processed, total_failed


async def run_reduce(check_inputs: bool = True) -> tuple[bool, int]:
    """Run only the reduce phase."""
    if check_inputs:
        await setup_directories()

    logfire.info('--- Starting Project Synapse: Reduce Phase ---')
    try:
        success, processed_files = await run_reduce_phase()
        logfire.info(
            'Reduce phase success: {success}, processed files: {count}', success=success, count=processed_files
        )
        return success, processed_files
    except Exception as e:
        raise ReducePhaseError(f'Error during Reduce Phase: {e}')


async def main(phase: Phase = Phase.BOTH):
    """
    Main async execution function for the Synapse processing pipeline.

    This coordinates the selected phase(s) of the transcript analysis:
    1. Map phase: Process individual transcripts to identify key people
    2. Reduce phase: Synthesize information across all transcripts
    """
    # Configure logging
    configure_logging()

    # --- Configuration Setup ---
    await setup_directories()

    logfire.info('Extraction type: {type}', type=settings.map_phase.extraction_type)
    logfire.info('Meetings directory: {dir}', dir=settings.map_phase.meetings_dir)
    logfire.info('Telegram directory: {dir}', dir=settings.map_phase.telegram_dir)
    logfire.info('Map output directory: {output_dir}', output_dir=settings.map_phase.output_map_dir)
    logfire.info('Concurrency limit: {concurrency}', concurrency=settings.processing.concurrency)
    logfire.info('Using Map LLM model: {model}', model=settings.map_phase.llm_model)
    logfire.info('Using Reduce LLM model: {model}', model=settings.reduce_phase.llm_model)
    logfire.info('Running phase: {phase}', phase=phase)
    # --- End Configuration Setup ---

    if phase in (Phase.MAP, Phase.BOTH):
        await run_map(check_inputs=False)
        logfire.info('Map outputs saved to: {output_dir}', output_dir=settings.map_phase.output_map_dir)
        logfire.info('--------------------------')

    if phase in (Phase.REDUCE, Phase.BOTH):
        await run_reduce(check_inputs=False)


app = typer.Typer(help='Synapse: A tool for analyzing meeting transcripts')


@app.command()
def run(phase: Phase = typer.Option(Phase.BOTH, help='Which phase to run: map, reduce, or both')):
    """Run Synapse with the specified phase(s)."""
    try:
        trio.run(main, phase)
    except SynapseError as err:
        logfire.error('Fatal error: {msg}', msg=str(err), exc_info=True)
        raise SystemExit(1) from err


if __name__ == '__main__':
    app()
