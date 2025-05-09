"""
Project-wide exceptions.

Synapse uses a structured hierarchy of exceptions to provide meaningful error messages
and appropriate handling of different error conditions.

Raise *only* subclasses of `SynapseError` from library code so that
the outer-most wrapper (e.g. `run_main`) has a single place to decide
how to turn them into process-exit codes or structured logs.
"""

class SynapseError(Exception):
    """Base exception for all Synapse errors."""


class PromptConfigNotFound(SynapseError):
    """
    Raised when the prompt configuration file (prompt.yaml) cannot be found.
    
    This typically occurs when the path specified in the configuration
    does not exist or cannot be accessed.
    """


class PromptConfigInvalid(SynapseError):
    """
    Raised when the prompt configuration file exists but is invalid.
    
    This might occur if the YAML is malformed or doesn't match the 
    expected Pydantic model structure.
    """


class EmptyInputDirectory(SynapseError):
    """
    Raised when the input directory contains no transcript (.txt) files.
    
    This error is raised when the scan for transcript files returns zero results.
    """


class FileProcessingError(SynapseError):
    """
    Raised when an error occurs while processing transcript files.
    
    This is a general error that may occur during file operations,
    such as reading files or scanning directories.
    """


class ReducePhaseError(SynapseError):
    """
    Raised when an unrecoverable error occurs during the Reduce phase.
    
    This might happen if the LLM agent encounters an error, or if there's
    a problem reading/writing the reduce phase output files.
    """