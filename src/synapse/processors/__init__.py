"""
Processing modules for map and reduce operations.

This package contains the core processing logic for Synapse's MapReduce approach:

- map.py: Handles the first phase of processing, analyzing individual text files
  (meeting transcripts or Telegram exports) to extract newsletter-worthy content.

- reduce.py: Handles the second phase, combining and synthesizing extracted content
  from all sources to generate a comprehensive weekly newsletter.

- extractors.py: Contains extraction functions for different content types and sources.
"""
