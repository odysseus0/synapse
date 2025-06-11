"""
Module for Pydantic AI agents used in Synapse for newsletter generation.

This module provides pre-configured agents with their prompts for newsletter extraction and synthesis.
"""

from textwrap import dedent

from pydantic_ai import Agent

from synapse.config import settings

# Newsletter Map Prompts for Meetings
NEWSLETTER_MEETING_MAP_SYSTEM_PROMPT = dedent("""
    You are an expert meeting analyst tasked with extracting key information from meeting transcripts for a weekly newsletter.
    
    Your goal is to identify and extract:
    1. Key decisions and outcomes
    2. Important discussions and debates
    3. Project updates and progress
    4. Blockers and challenges raised
    5. Action items and next steps
    6. Interesting technical insights
    7. Notable quotes or moments
    
    Focus on information that would be valuable for team members who weren't present at the meeting.
    Be concise but comprehensive in your extraction.
""")

NEWSLETTER_MEETING_MAP_TEMPLATE = dedent("""
    Extract newsletter-worthy content from the following meeting transcript.
    
    Meeting: {transcript_filename}
    
    <transcript>
    {transcript_text}
    </transcript>
    
    Extract the following sections (use "None identified" if a section has no relevant content):
    
    ## Key Decisions & Outcomes
    - [List major decisions made and their implications]
    
    ## Project Updates
    - [Progress on ongoing projects, new initiatives]
    
    ## Technical Discussions
    - [Interesting technical insights, architectural decisions, tool evaluations]
    
    ## Challenges & Blockers
    - [Issues raised, blockers identified, help needed]
    
    ## Action Items
    - [Specific tasks assigned or volunteered for]
    
    ## Notable Moments
    - [Interesting quotes, funny moments, team shoutouts]
    
    Focus on extracting concrete, actionable information that would be valuable for the weekly newsletter.
""")

# Newsletter Map Prompts for Telegram
NEWSLETTER_TELEGRAM_MAP_SYSTEM_PROMPT = dedent("""
    You are an expert analyst tasked with extracting key information from Telegram chat discussions for a weekly newsletter.
    
    Your goal is to identify and extract:
    1. Important announcements and updates
    2. Technical discussions and solutions
    3. Questions asked and answers provided
    4. Resource sharing (tools, articles, docs)
    5. Ongoing debates or discussions
    6. Community highlights and interactions
    
    Focus on substantive discussions rather than casual chat.
    Extract information that provides value to team members who may have missed the conversations.
""")

NEWSLETTER_TELEGRAM_MAP_TEMPLATE = dedent("""
    Extract newsletter-worthy content from the following Telegram chat transcript.
    
    Source: {transcript_filename}
    
    <transcript>
    {transcript_text}
    </transcript>
    
    Extract the following sections (use "None identified" if a section has no relevant content):
    
    ## Announcements & Updates
    - [Important announcements, status updates, releases]
    
    ## Technical Discussions
    - [Problem-solving discussions, technical Q&A, architectural debates]
    
    ## Resources Shared
    - [Useful links, tools, articles, documentation with context]
    
    ## Questions & Answers
    - [Key questions raised and their resolutions]
    
    ## Community Highlights
    - [Interesting discussions, helpful contributions, collaborative moments]
    
    Focus on extracting substantive content that would be valuable for the weekly newsletter.
""")

# Newsletter Reduce Prompts
NEWSLETTER_REDUCE_SYSTEM_PROMPT = dedent("""
    You are an expert newsletter editor tasked with synthesizing extracted content from multiple sources into a cohesive, engaging weekly newsletter.
    
    Your goal is to create a well-structured newsletter that:
    1. Highlights the most important developments of the week
    2. Provides clear, actionable information
    3. Maintains an engaging, professional tone
    4. Organizes information logically by importance and topic
    5. Keeps the reading time to 5-10 minutes
    
    Structure the newsletter with clear sections and use formatting to make it scannable.
    Prioritize information based on impact and relevance to the broader team.
""")

NEWSLETTER_REDUCE_USER_MESSAGE_TEMPLATE = dedent("""
    Synthesize the following extracted content into a comprehensive weekly newsletter.
    
    <extracted_content>
    {{CONCATENATED_NEWSLETTER_EXTRACTS}}
    </extracted_content>
    
    Create a newsletter following this structure:
    
    # Weekly Team Newsletter
    
    ## 📍 The Week's Highlights
    - Major wins and breakthroughs
    - Key decisions that affect multiple people
    - Important pivots or strategy changes
    
    ## 🎯 Progress & Momentum
    - What shipped or got completed
    - Demos and cool stuff people built
    - Metrics/results if available
    
    ## 💡 Interesting Discussions
    - Technical insights or "aha" moments
    - Creative solutions to problems
    - Good questions that sparked useful debates
    
    ## 🚧 Heads Up
    - Upcoming changes or migrations
    - Things that might affect people's work
    - New tools or processes being adopted
    
    ## 🎪 The Human Side
    - Funny moments or quotes
    - Team member shoutouts
    - Interesting side conversations
    
    ## 🔗 Resources to Check Out
    - Useful links shared with context
    - New docs or tools
    - External articles/research mentioned
    
    Keep each section concise but informative. Use bullet points for easy scanning.
    Aim for a 5-10 minute read. Make it engaging and valuable for team members.
""")

# Initialize agents
newsletter_meeting_map_agent = Agent(
    model=settings.map_phase.llm_model,
    instructions=NEWSLETTER_MEETING_MAP_SYSTEM_PROMPT,
)

newsletter_telegram_map_agent = Agent(
    model=settings.map_phase.llm_model,
    instructions=NEWSLETTER_TELEGRAM_MAP_SYSTEM_PROMPT,
)

newsletter_reduce_agent = Agent(
    model=settings.reduce_phase.llm_model,
    instructions=NEWSLETTER_REDUCE_SYSTEM_PROMPT,
)