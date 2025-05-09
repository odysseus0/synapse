"""
Synapse: Main execution module.

This module is the entry point for the Synapse application, orchestrating
the map and reduce phases for analyzing meeting transcripts.
"""
import logfire
import trio
from trio import Path

from synapse.config import SynapseSettings
from synapse.exceptions import (
    EmptyInputDirectory,
    FileProcessingError,
    ReducePhaseError,
    SynapseError,
)
from synapse.processors.map import run_map_phase
from synapse.processors.reduce import run_reduce_phase
from synapse.utils.file_io import load_prompt_config
from synapse.utils.logging import configure_logging


async def main():
    """
    Main async execution function for the Synapse processing pipeline.
    
    This coordinates both map and reduce phases of the transcript analysis:
    1. Map phase: Process individual transcripts to identify key people
    2. Reduce phase: Synthesize information across all transcripts
    """
    # Configure logging
    configure_logging()
    
    # Load configuration
    config = SynapseSettings()
    
    logfire.info('--- Starting Project Synapse: Map Phase ---')

    # --- Configuration Setup ---
    input_dir = Path(config.map_phase.input_transcripts_dir)
    output_dir = Path(config.map_phase.output_map_dir)
    prompt_config_path = Path(config.map_phase.prompt_config_path)
    concurrency = config.processing.concurrency
    
    logfire.info('Input directory: {input_dir}', input_dir=str(input_dir))
    logfire.info('Output directory: {output_dir}', output_dir=str(output_dir))
    logfire.info('Prompt config path: {prompt_config_path}', prompt_config_path=str(prompt_config_path))
    logfire.info('Concurrency limit: {concurrency}', concurrency=concurrency)
    logfire.info('Using LLM model: {model}', model=config.map_phase.llm_model)
    # --- End Configuration Setup ---

    # Load prompt configuration
    prompt_config_model = await load_prompt_config(prompt_config_path)

    # Find transcript files
    try:
        # Create output directory if it doesn't exist
        await output_dir.mkdir(exist_ok=True, parents=True)
        logfire.info('Ensured output directory exists: {dir_path}', dir_path=str(output_dir))
        
        # Find transcript files directly
        transcript_files = [p for p in await input_dir.glob('*.txt')]
        logfire.info('Found {count} transcript files to process.', count=len(transcript_files))
        
        if not transcript_files:
            raise EmptyInputDirectory(f'No .txt files in {input_dir}')
    except Exception as e:
        raise FileProcessingError(f'Error scanning input directory {input_dir}: {e}')

    # Run the map phase processing
    with logfire.span('run_map_phase'):
        processed_count, failed_count = await run_map_phase(
            transcript_paths=transcript_files,
            output_dir=output_dir,
            model_name=config.map_phase.llm_model,
            system_prompt=prompt_config_model.map_prompt.system_message,
            user_template=prompt_config_model.map_prompt.user_message_template,
            concurrency=concurrency
        )

    # --- Summary ---
    logfire.info('--- Map Phase Complete ---')
    logfire.info('Successfully processed: {count}', count=processed_count)
    logfire.info('Failed to process: {count}', count=failed_count)
    logfire.info('Map outputs saved to: {output_dir}', output_dir=str(output_dir))
    logfire.info('--------------------------')

    # --- Reduce Phase ---
    try:
        success, processed_files = await run_reduce_phase(
            map_output_dir=output_dir, 
            output_file=Path(config.reduce_phase.output_markdown_file),
            model_name=config.reduce_phase.llm_model,
            system_prompt=prompt_config_model.reduce_prompt.system_message,
            user_template=prompt_config_model.reduce_prompt.user_message_template
        )
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