"""
Module for Pydantic AI agents used in Synapse.

This module provides pre-configured map and reduce agents with their prompts.
"""

from textwrap import dedent

from pydantic_ai import Agent

from synapse.config import settings
from synapse.models import Profile

MAP_SYSTEM_PROMPT = dedent("""
    You are an expert meeting analyst AI. Your primary task is to meticulously analyze the provided meeting transcript and, for each key individual identified by name, generate structured summary.

    Key individuals are typically internal team members, core collaborators, or significant external stakeholders who demonstrably:
    * Actively contributed to discussions (e.g., speaking multiple times, offering substantive points).
    * Were involved in making or influencing decisions.
    * Expressed notable opinions or stances relevant to the meeting's objectives.

    IMPORTANT INSTRUCTIONS FOR IDENTIFYING INDIVIDUALS:
    1. NAMED SPEAKERS: Prioritize individuals explicitly named in the transcript.
    2. GENERIC SPEAKER LABELS (e.g., "SPEAKER 1", "SPEAKER_02"):
        a. ATTEMPT INFERENCE: Try to infer their actual name from the transcript's context. For example, another participant might address them by name ("Thanks, Sarah, for that point, SPEAKER 1..."), or they might introduce themselves ("SPEAKER 3: Hi, it's John from engineering...").
        b. CONFIDENT INFERENCE: If a name can be confidently inferred for a generic speaker label, generate a summary block for them using the INFERRED name.
        c. NO CONFIDENT INFERENCE: If a name CANNOT be confidently inferred for a generic speaker label after careful review, DO NOT generate a block for that speaker. They should be discarded for this analysis.
    3. FOCUS & EXCLUSION: Concentrate on individuals with substantive contributions. Ignore fleeting mentions, individuals who only speak to agree without adding substance, or those who do not meet the "key individual" criteria above.
""")

MAP_USER_MESSAGE_TEMPLATE = dedent("""
    Analyze the following meeting transcript.

    For EACH key person you identify (following all criteria and name inference rules in the system message), generate a separate section using the exact format specified below.
    If, after your analysis, no key persons can be identified according to the instructions, your entire output for this transcript must be *only* the following text and nothing else:
    "No key persons identified in this transcript."

    Transcript Content:
    <transcript>
    {transcript_text}
    </transcript>

    Instructions & Output Format (Repeat this complete structure for EACH identified person):

    <structure>
    ## Person Identified: [Name Variation Used Most Prominently Here OR Confidently Inferred Name]

    * **Transcript Source:** `{transcript_filename}`
    * **Date Hint:** `[Fill in YYYY-MM-DD if inferrable from transcript content or metadata, otherwise N/A]`
    * **Other Names Mentioned Here:** `[List other variations of this person's name seen in this transcript, or N/A. If the name was inferred from a generic label, this might be N/A unless other variations of the inferred name also appear.]`
    * **Summary of Contributions/Discussion:**
        * `[Bulleted list (2-5 key points) or brief paragraph summarizing their most significant statements, questions asked, proposals made, or information shared HERE. Focus on their active contributions to the meeting's objectives.]`
    * **Topics Discussed:** `[List up to 5 key topics/projects mentioned in relation to them HERE, comma-separated; choose the most impactful topics based on discussion length, emphasis, or explicit statements of importance.]`
    * **Decisions Involved In:**
        * `[Decision 1 summary] (Role Hint: [e.g., Proposed, Supported, Opposed, Agreed to, Questioned, Informed decision-makers, Implemented], Context: [Optional brief, relevant snippet, 1-2 sentences])`
        * `(List all decisions they were directly involved in HERE, or state None Identified)`
    * **Opinions/Stances Expressed:**
        * `Topic: [Topic 1] - Stance: [Summary of stance expressed HERE] (Context: [Optional brief, relevant snippet, 1-2 sentences])`
        * `(List all clearly expressed opinions/stances HERE, or state None Identified)`
    * **Interactions with Others:**
        * `Interacted with: [Other Person Name Variation] regarding "[Interaction Topic]". Type: [e.g., Direct Discussion, Debate, Presentation to, Questioned by, Received input from, Collaborated on task with]. (Context: [Optional brief, relevant snippet, 1-2 sentences])`
        * `(List all significant interactions HERE, or state None Identified)`
    </structure>

    Ensure all fields accurately reflect information *only* from the provided transcript. Do not add any explanatory text. Do not include triple backticks code blocks in your output. Use Markdown best practices for lists and emphasis. Use `YYYY-MM-DD` for dates.
""")

REDUCE_SYSTEM_PROMPT = dedent("""
    You are an expert Team Dynamics Analyst AI. You will receive a large text payload containing multiple summaries. Each summary describes a person's activity within a single meeting transcript. The same real-world person may appear in multiple summaries with potentially different name variations.

    Your core tasks are to:
    1. Identify each unique person across all summary blocks
    2. Consolidate information for each person (even when their name varies)
    3. Generate a comprehensive profile for each significant person
    4. Include metadata about each person and detailed content sections

    Focus on individuals with significant or recurring activity and filter out minor mentions.

    Each profile should consist of:
    - Structured metadata about the person
    - Markdown content with comprehensive information including their activity, topics, decisions, stances, and interactions
""")

REDUCE_USER_MESSAGE_TEMPLATE = dedent("""
    Analyze the following text payload. This payload is a concatenation of summaries, each detailing a person's activities from various meeting transcripts.

    Perform entity resolution and synthesis on this aggregated data. Your goal is to generate a detailed profile for each unique key individual identified.

    Text Payload:
    <payload>
    {{CONCATENATED_MARKDOWN_BLOCKS_HERE}}
    </payload>

    Generate a list of profiles of unique persons deemed significant. The Markdown structure for the content field of each profile is defined *within* the `<md>` and `</md>` tags shown below.

    <md>
    ## Profile: [Canonical Name - Choose the best, most complete, and formal full name found or synthesized across all provided map outputs and interactions for this individual]

    ### Overall Summary & Activity:

    `[Write a narrative paragraph (approx. 150-250 words) summarizing their key contributions, activities, prevalent stances, and overall involvement across all relevant map outputs. Crucially, include any significant changes or evolution in their role, focus, contributions, or opinions over the active period. If identifiable from dates, highlight their 1-2 most impactful recent activities or contributions.]`

    ### Key Topics & Projects Involved:

    * `[Synthesize and list the main topics/projects they consistently engage with, drawing from "Topics Discussed" in map outputs. Prioritize topics with repeated engagement or significant contributions.]`
    * `... (add more topics as needed)`

    ### Consolidated Decisions Involved:

    * `[Decision Summary] (Role: [Synthesize their most common or impactful role in this decision based on "Role Hint" from map outputs, e.g., Primary Decision Maker, Key Influencer, Proposed Solution, Implemented Decision, Critical Contributor], Date: [Date Hint -<y_bin_46>-MM-DD], Source: [Source Transcript])`
    * `(List all consolidated decisions they were significantly involved in. State if 'None significant'.)`

    ### Key Stances & Opinions:

    * **Topic:** `[Topic Name]`
        * **Stance:** `[Synthesize their stance on this topic across map outputs. If the stance evolves or if there are nuances, describe this, e.g., 'Initially expressed skepticism regarding X (Source: [Source Transcript A], Date:<y_bin_46>-MM-DD), but later supported the revised proposal Y (Source: [Source Transcript B], Date:<y_bin_46>-MM-DD)'. If stance is consistent, state it directly.]` (Key Supporting Source(s): `[e.g., Source Transcript A,<y_bin_46>-MM-DD; Source Transcript C,<y_bin_46>-MM-DD]`)
    * `(List key stances identified on distinct topics.)`

    ### Key Collaborators & Communication:

    * **Frequent Collaborators:**
        * `[Collaborator Name - Use canonical name if possible by resolving variations from interaction data] (Topics: [List shared topics of discussion/collaboration], Frequency: [Estimate High/Medium/Low based on number of distinct meeting interactions documented in map outputs for this pair])`
    * **Communication Flow Hints (Optional):**
        * `[Synthesize observed communication patterns if evident, e.g., "Often discusses technical specifications for Project X with [Collaborator Name]," "Frequently seeks input from [Collaborator Name] on budget matters." State None Observed if not clear.]`

    ### Potential Blockers/Risks Raised by This Person:

    * `[List any significant, recurring, or impactful risks, concerns, or blockers this person raised regarding key projects, strategies, or topics. Note the concern, topic, source transcript, and date (YYYY-MM-DD). State None Identified if applicable.]`
    * `...`

    ### Key Questions Asked by This Person:

    * `[List 1-3 recurring or particularly insightful/impactful questions this person asked that drove significant discussion, clarification, or re-evaluation on important topics. Note the question or its summary, the topic, source transcript, and date (YYYY-MM-DD). State None Identified if applicable.]`
    * `...`

    ### Observed Strengths/Expertise Areas (Optional):

    * `[Based on their contributions, decisions, and how others interact with them across transcripts, synthesize any apparent areas of strength, expertise, or particularly positive influence. E.g., "Demonstrates strong analytical skills in financial discussions," "Effective at mediating disagreements on Topic Z," "Consistently provides practical solutions to engineering challenges." State if not clearly inferable or None Identified.]`

    </md>

    Ensure the output strictly follows the Markdown structure defined *within* the `<md>` XML tags above for each person's profile. 
""")

# Initialize the map agent with defaults from settings
map_agent = Agent(
    model=settings.map_phase.llm_model,
    instructions=MAP_SYSTEM_PROMPT,
)

# Initialize the reduce agent with defaults from settings and output type
reduce_agent = Agent(
    model=settings.reduce_phase.llm_model, instructions=REDUCE_SYSTEM_PROMPT, output_type=list[Profile]
)

# Newsletter-specific prompts and agents
NEWSLETTER_MAP_SYSTEM_PROMPT = dedent("""
    You are an expert content extractor identifying newsletter-worthy information from team communications.
    Your task is to comprehensively extract all potentially valuable content that could be used in a weekly newsletter.
    
    The goal is to capture information that helps team members:
    - Stay informed about important decisions and changes
    - Learn about technical breakthroughs and solutions
    - Track progress across different projects
    - Understand cross-team dependencies and collaborations
    - Maintain awareness of team culture and energy
    
    Be inclusive in extraction - it's better to capture too much context than too little.
    The synthesis phase will handle final curation and presentation.
    
    Focus on extracting:
    - Strategic decisions, pivots, or direction changes
    - Technical insights, solutions, and breakthroughs
    - Progress updates that show momentum
    - Action items with clear owners
    - Important discussions and debates
    - Shared resources with context
    - Team dynamics and culture moments
    - Emerging concerns or blockers
""")

NEWSLETTER_MEETING_MAP_TEMPLATE = dedent("""
    Extract newsletter-worthy content from this meeting transcript.
    
    Meeting: {transcript_filename}
    
    <transcript>
    {transcript_text}
    </transcript>
    
    Extract and structure the following information:
    
    ## Meeting: {transcript_filename}
    
    ### Meeting Context
    * Date: [Extract if available]
    * Type: [All-hands, Engineering, Product, etc. if identifiable]
    * Key Attendees: [List main participants]
    
    ### Decisions Made
    * Decision: [What was decided]
      - Context: [Why this decision was needed]
      - Made by: [Who made or championed this decision]
      - Impact: [Who/what this affects]
      - Related Discussion: [Key points from the debate if any]
    
    ### Technical Insights & Solutions
    * Insight: [Technical discovery or solution]
      - Problem Solved: [What challenge this addresses]
      - Discovered by: [Who shared this insight]
      - Technical Details: [Enough detail to understand the breakthrough]
      - Potential Applications: [How this might be used]
    
    ### Progress & Achievements
    * Achievement: [What was completed or demonstrated]
      - Owner: [Who accomplished this]
      - Significance: [Why this matters]
      - Next Steps: [What comes after this]
    
    ### Action Items
    * Task: [Specific action to be taken]
      - Owner: [Person responsible]
      - Due Date: [If mentioned]
      - Dependencies: [What/who this depends on]
      - Context: [Why this is needed]
    
    ### Important Discussions
    * Topic: [What was discussed]
      - Participants: [Key people in discussion]
      - Main Points: [Key arguments or perspectives]
      - Outcome: [Consensus, decision, or next steps]
      - Open Questions: [Unresolved aspects]
    
    ### Resources & Links Mentioned
    * Resource: [What was shared]
      - URL: [If provided]
      - Shared by: [Who mentioned it]
      - Purpose: [Why this was relevant]
    
    ### Concerns & Blockers Raised
    * Issue: [Problem or concern raised]
      - Raised by: [Who brought this up]
      - Impact: [What this blocks or affects]
      - Proposed Solutions: [If any were discussed]
    
    ### Notable Quotes
    * "[Exact quote]" - [Speaker]
      - Context: [Why this quote is significant]
    
    ### Team Dynamics
    * [Any notable team interactions, culture moments, or energy indicators]
    
    Only include sections where relevant content exists. Preserve specific names, technical terms, and enough context for someone who wasn't present to understand the significance.
""")

NEWSLETTER_TELEGRAM_MAP_TEMPLATE = dedent("""
    Extract newsletter-worthy content from this Telegram discussion.
    
    Source: {transcript_filename}
    
    <telegram_threads>
    {transcript_text}
    </telegram_threads>
    
    Extract and structure the following information:
    
    ## Telegram Activity: {transcript_filename}
    
    ### Period Context
    * Date Range: [Extract if identifiable]
    * Active Participants: [Most engaged members]
    * Thread Count: [Approximate number of distinct discussions]
    
    ### Significant Discussions
    * Thread Topic: [Main subject of discussion]
      - Participants: [Key contributors]
      - Problem/Question: [What initiated the discussion]
      - Key Points: [Main arguments or insights shared]
      - Resolution: [How it concluded, if at all]
      - Thread Length: [Rough indicator of engagement]
    
    ### Problems & Solutions
    * Problem Raised: [Technical or process challenge]
      - Asked by: [Who needed help]
      - Solutions Offered: [Different approaches suggested]
        - By: [Who suggested each]
        - Selected Approach: [If one was chosen]
      - Outcome: [Whether it was resolved]
    
    ### Resources Shared
    * Resource: [What was shared]
      - Type: [Link, document, tool, article, etc.]
      - URL: [If provided]
      - Shared by: [Who posted it]
      - Context: [Why it was shared]
      - Reactions: [How others responded]
    
    ### Decisions & Consensus
    * Decision Point: [What needed to be decided]
      - Options Discussed: [Different possibilities]
      - Participants: [Who weighed in]
      - Final Direction: [What was agreed upon]
      - Dissenting Views: [If any]
    
    ### Announcements & Updates
    * Announcement: [What was announced]
      - From: [Who announced it]
      - Impact: [Who/what this affects]
      - Reactions: [How team responded]
    
    ### Emerging Patterns
    * Pattern: [Recurring theme or concern]
      - Frequency: [How often it came up]
      - Different Contexts: [Various discussions where it appeared]
      - Key Voices: [Who consistently engaged with this topic]
    
    ### Technical Discoveries
    * Discovery: [New tool, approach, or insight]
      - Discovered by: [Who found/shared it]
      - What it Solves: [Problem it addresses]
      - Team Interest: [How others reacted]
    
    ### Notable Interactions
    * "[Memorable quote or exchange]"
      - Participants: [Who was involved]
      - Context: [What made this notable]
      - Team Reaction: [Emojis, responses]
    
    ### Concerns Raised
    * Concern: [Issue brought up]
      - Raised by: [Who flagged it]
      - Severity: [How urgent/important]
      - Discussion: [How team responded]
    
    Include all sections with relevant content. Preserve thread structure and relationships between messages where important. Keep enough context to understand the flow of conversations.
""")

# Initialize newsletter map agents
newsletter_meeting_map_agent = Agent(
    model=settings.map_phase.llm_model,
    instructions=NEWSLETTER_MAP_SYSTEM_PROMPT,
)

newsletter_telegram_map_agent = Agent(
    model=settings.map_phase.llm_model,
    instructions=NEWSLETTER_MAP_SYSTEM_PROMPT,
)

# Newsletter reduce agent and prompts
NEWSLETTER_REDUCE_SYSTEM_PROMPT = dedent("""
    You are an expert newsletter editor who synthesizes team communications into engaging, informative weekly newsletters.
    Your task is to create a cohesive, readable newsletter that helps team members stay informed and connected.
    
    Key principles:
    - Be concise but comprehensive - aim for a 5-10 minute read
    - Highlight what matters most to the team
    - Maintain a professional yet friendly tone
    - Connect related topics across different sources
    - Preserve important technical details while remaining accessible
    - Include enough context for team members who may have missed discussions
    
    Structure the newsletter according to the defined template, focusing on:
    - Major achievements and breakthroughs
    - Key decisions and their impact
    - Technical discoveries and solutions
    - Team dynamics and culture
    - Important resources and links
    
    Synthesize information from multiple sources (meetings and Telegram) to tell cohesive stories.
    When similar topics appear in different contexts, combine them into unified narratives.
""")

NEWSLETTER_REDUCE_USER_MESSAGE_TEMPLATE = dedent("""
    Create a comprehensive weekly newsletter from the following extracted content from meetings and Telegram discussions.
    
    <extracted_content>
    {{CONCATENATED_NEWSLETTER_EXTRACTS}}
    </extracted_content>
    
    Generate a newsletter following this exact structure:
    
    # FlashbotsX Weekly Newsletter
    
    *Week of [Date Range]*
    
    ---
    
    ## 📍 The Week's Highlights
    
    [2-4 bullet points covering the most important wins, breakthroughs, and strategic decisions. Focus on what will have lasting impact.]
    
    ## 🎯 Progress & Momentum
    
    ### What Shipped
    [List completed features, demos, or milestones achieved this week]
    
    ### Key Achievements
    [Notable accomplishments by team members or projects]
    
    ## 💡 Technical Insights & Solutions
    
    [2-3 subsections covering the most interesting technical discoveries, solutions to problems, or implementation breakthroughs. Include enough technical detail to be useful but keep it accessible.]
    
    ## 🎪 Team Spotlight
    
    ### Shoutouts
    [Recognize team members who made notable contributions]
    
    ### Notable Moments
    [Interesting interactions, funny quotes, or team culture highlights]
    
    ## 🚧 Important Updates
    
    ### Decisions & Changes
    [Strategic decisions or process changes that affect the team]
    
    ### Heads Up
    [Upcoming migrations, tool changes, or other things team members should prepare for]
    
    ### Open Questions & Blockers
    [Unresolved issues that need team attention]
    
    ## 💬 Key Discussions
    
    [2-3 of the most significant discussions from the week, including the core question, different perspectives, and outcomes]
    
    ## 🔗 Resources & Links
    
    [Curated list of the most useful resources shared this week, organized by category with context for why each is valuable]
    
    ---
    
    *Generated from [X] meetings and [Y] days of Telegram activity*
    
    Ensure the newsletter:
    - Flows naturally between sections
    - Balances technical depth with readability
    - Includes specific names and attributions where relevant
    - Provides enough context for those who missed the original discussions
    - Maintains an engaging, professional tone throughout
""")

# Initialize newsletter reduce agent
newsletter_reduce_agent = Agent(
    model=settings.reduce_phase.llm_model,
    instructions=NEWSLETTER_REDUCE_SYSTEM_PROMPT,
)
