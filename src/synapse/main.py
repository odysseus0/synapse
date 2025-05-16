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
    EmptyInputDirectory,
    FileProcessingError,
    ReducePhaseError,
    SynapseError,
)
from synapse.logging import configure_logging
from synapse.processors.map import run_map_phase
from synapse.processors.reduce import run_reduce_phase


class Phase(str, enum.Enum):
    MAP = 'map'
    REDUCE = 'reduce'
    BOTH = 'both'


async def setup_directories() -> tuple[Path, Path, Path]:
    """Set up directories and return paths needed for processing."""
    input_dir = Path(settings.map_phase.input_transcripts_dir)
    map_output_dir = Path(settings.map_phase.output_map_dir)
    profiles_dir = Path(settings.reduce_phase.output_profiles_dir)

    try:
        await map_output_dir.mkdir(exist_ok=True, parents=True)
        await profiles_dir.mkdir(exist_ok=True, parents=True)
        logfire.info('Ensured map output directory exists: {dir_path}', dir_path=str(map_output_dir))
        logfire.info('Ensured profiles directory exists: {dir_path}', dir_path=str(profiles_dir))

        # Check if input directory has files
        input_files = [p for p in await input_dir.glob('*.txt')]
        if not input_files:
            raise EmptyInputDirectory(f'No .txt files in {input_dir}')
    except Exception as e:
        raise FileProcessingError(f'Error setting up directories: {e}')
    
    return input_dir, map_output_dir, profiles_dir


async def run_map(check_inputs: bool = True) -> tuple[int, int]:
    """Run only the map phase."""
    if check_inputs:
        await setup_directories()
    
    logfire.info('--- Starting Project Synapse: Map Phase ---')
    with logfire.span('run_map_phase'):
        processed_count, failed_count = await run_map_phase()
    
    logfire.info('--- Map Phase Complete ---')
    logfire.info('Successfully processed: {count}', count=processed_count)
    logfire.info('Failed to process: {count}', count=failed_count)
    
    return processed_count, failed_count


async def run_reduce(check_inputs: bool = True) -> tuple[bool, int]:
    """Run only the reduce phase."""
    if check_inputs:
        await setup_directories()
    
    logfire.info('--- Starting Project Synapse: Reduce Phase ---')
    try:
        success, processed_files = await run_reduce_phase()
        logfire.info('Reduce phase success: {success}, processed files: {count}',
                    success=success, count=processed_files)
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
    input_dir, map_output_dir, profiles_dir = await setup_directories()
    
    logfire.info('Input directory: {input_dir}', input_dir=str(input_dir))
    logfire.info('Map output directory: {output_dir}', output_dir=str(map_output_dir))
    logfire.info('Profiles output directory: {profiles_dir}', profiles_dir=str(profiles_dir))
    logfire.info('Concurrency limit: {concurrency}', concurrency=settings.processing.concurrency)
    logfire.info('Using Map LLM model: {model}', model=settings.map_phase.llm_model)
    logfire.info('Using Reduce LLM model: {model}', model=settings.reduce_phase.llm_model)
    logfire.info('Running phase: {phase}', phase=phase)
    # --- End Configuration Setup ---

    if phase in (Phase.MAP, Phase.BOTH):
        await run_map(check_inputs=False)
        logfire.info('Map outputs saved to: {output_dir}', output_dir=str(map_output_dir))
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