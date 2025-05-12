"""
Logging configuration and utility functions.
"""
import os

import logfire


def configure_logging():
    """
    Configure logging for the application.
    
    If LOGFIRE_TOKEN is set in the environment, configure Logfire to send data to the cloud.
    Otherwise, use Logfire in local-only mode which doesn't require authentication.
    """
    # Check if we have a Logfire token
    if os.environ.get('LOGFIRE_TOKEN'):
        # Use Logfire with cloud integration
        logfire.configure(scrubbing=False)
    else:
        # Use Logfire in local-only mode (no authentication required)
        logfire.configure(send_to_logfire=False)
    
    # Instrument pydantic_ai in either case
    logfire.instrument_pydantic_ai()