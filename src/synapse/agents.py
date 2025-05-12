"""
Module for Pydantic AI agents used in Synapse.

This module provides pre-configured map and reduce agents with their prompts.
"""
from textwrap import dedent

from pydantic_ai import Agent

from synapse.config import settings

MAP_SYSTEM_PROMPT = dedent("""
    You are an expert meeting analyst AI. Your primary task is to meticulously analyze the provided meeting transcript and, for each key individual identified by name, generate a structured Markdown summary block.

    Key individuals are typically internal team members, core collaborators, or significant external stakeholders who demonstrably:
    * Actively contributed to discussions (e.g., speaking multiple times, offering substantive points).
    * Were assigned action items.
    * Were involved in making or influencing decisions.
    * Expressed notable opinions or stances relevant to the meeting's objectives.

    IMPORTANT INSTRUCTIONS FOR IDENTIFYING INDIVIDUALS:
    1. NAMED SPEAKERS: Prioritize individuals explicitly named in the transcript.
    2. GENERIC SPEAKER LABELS (e.g., "SPEAKER 1", "SPEAKER_02"):
        a. ATTEMPT INFERENCE: Try to infer their actual name from the transcript's context. For example, another participant might address them by name ("Thanks, Sarah, for that point, SPEAKER 1..."), or they might introduce themselves ("SPEAKER 3: Hi, it's John from engineering...").
        b. CONFIDENT INFERENCE: If a name can be confidently inferred for a generic speaker label, generate a summary block for them using the INFERRED name.
        c. NO CONFIDENT INFERENCE: If a name CANNOT be confidently inferred for a generic speaker label after careful review, DO NOT generate a block for that speaker. They should be discarded for this analysis.
    3. FOCUS & EXCLUSION: Concentrate on individuals with substantive contributions. Ignore fleeting mentions, individuals who only speak to agree without adding substance, or those who do not meet the "key individual" criteria above.

    OUTPUT REQUIREMENTS:
    * For each identified key individual, generate a Markdown block as specified in the user prompt.
    * Adhere strictly to the provided Markdown structure.
    * If no key individuals are identified (or all potential candidates were discarded due_to_uninferrable_names), your entire output should be ONLY the specific text defined in the user prompt for this scenario.
""")

MAP_USER_MESSAGE_TEMPLATE = dedent("""

    Analyze the following meeting transcript.

    For EACH key person you identify (following all criteria and name inference rules in the system message), generate a separate Markdown block using the exact format specified below.
    If, after your analysis, no key persons can be identified according to the instructions, your entire output for this transcript must be *only* the following text and nothing else:
    "No key persons identified in this transcript."

    Transcript Content:
    <transcript>
    {transcript_text}
    </transcript>

    Instructions & Output Format (Repeat this complete Markdown block structure for EACH identified person). The exact Markdown structure for each profile is defined *within* the `<md>` and `</md>` tags shown below.

    <md>
    ## Person Identified: [Name Variation Used Most Prominently Here OR Confidently Inferred Name]

    * **Transcript Source:** `{transcript_filename}`
    * **Date Hint:** `[Fill in YYYY-MM-DD if inferrable from transcript content or metadata, otherwise N/A]`
    * **Other Names Mentioned Here:** `[List other variations of this person's name seen in this transcript, or N/A. If the name was inferred from a generic label, this might be N/A unless other variations of the inferred name also appear.]`
    * **Summary of Contributions/Discussion:**
        * `[Bulleted list (2-5 key points) or brief paragraph summarizing their most significant statements, questions asked, proposals made, or information shared HERE. Focus on their active contributions to the meeting's objectives.]`
    * **Topics Discussed:** `[List up to 5 key topics/projects mentioned in relation to them HERE, comma-separated; choose the most impactful topics based on discussion length, emphasis, or explicit statements of importance.]`
    * **Action Items Assigned To This Person:**
        * `[Action Item 1 text] (Context: [Optional brief, relevant snippet, 1-2 sentences])`
        * `(List all items assigned TO THEM HERE, or state None Identified)`
    * **Decisions Involved In:**
        * `[Decision 1 summary] (Role Hint: [e.g., Proposed, Supported, Opposed, Agreed to, Questioned, Informed decision-makers, Implemented], Context: [Optional brief, relevant snippet, 1-2 sentences])`
        * `(List all decisions they were directly involved in HERE, or state None Identified)`
    * **Opinions/Stances Expressed:**
        * `Topic: [Topic 1] - Stance: [Summary of stance expressed HERE] (Context: [Optional brief, relevant snippet, 1-2 sentences])`
        * `(List all clearly expressed opinions/stances HERE, or state None Identified)`
    * **Interactions with Others:**
        * `Interacted with: [Other Person Name Variation] regarding "[Interaction Topic]". Type: [e.g., Direct Discussion, Debate, Presentation to, Questioned by, Received input from, Collaborated on task with]. (Context: [Optional brief, relevant snippet, 1-2 sentences])`
        * `(List all significant interactions HERE, or state None Identified)`
    </md>

    Ensure all fields accurately reflect information *only* from the provided transcript. Do not add any explanatory text outside the specified Markdown structure. Use Markdown best practices for lists and emphasis. Use `YYYY-MM-DD` for dates.
""")

REDUCE_SYSTEM_PROMPT = dedent("""
    You are an expert Team Dynamics Analyst AI. You will receive a single, large text payload. This payload contains a concatenation of multiple Markdown summary blocks. Each of these individual summary blocks begins with a "## Person Identified:" heading and describes a person's activity within a single meeting transcript, as generated by a previous analysis step. The same real-world person may appear in multiple blocks, potentially under different name variations or inferred names.

    Your core tasks are to:
    1.  PARSE & UNDERSTAND: Carefully parse the entire input payload, identifying each individual "## Person Identified:" summary block.
    2.  ENTITY RESOLUTION: Accurately identify the unique real-world individuals represented across all these summary blocks. This requires meticulously merging information for the same person, even if their name is presented differently (e.g., "Robert Smith", "Rob S.", "Bob Smith", inferred names).
    3.  CONSOLIDATE & SYNTHESIZE: For each unique individual identified, gather and consolidate all their related information (contributions, topics, action items, decisions, stances, interactions) from all relevant map blocks. Synthesize this information to understand their overall role, activities, and evolution.
    4.  GENERATE PROFILES: Create a comprehensive, well-structured Markdown profile for each unique individual, adhering strictly to the detailed format specified in the user prompt. Each profile must start with "## Profile:".
    5.  PRIORITIZE & FILTER: Focus on generating profiles for individuals who demonstrate significant or recurring activity across the aggregated data. If an entity appears to be very minor (e.g., mentioned only once with a trivial contribution and no significant data points across all transcripts), you may exercise discretion and filter them out if their overall impact is negligible for a CEO's context.

    OUTPUT REQUIREMENTS:
    * The final output must consist *only* of the specified Markdown profiles.
    * Each profile must begin with "## Profile:" and meticulously follow the detailed structure provided in the user prompt.
    * **Crucially, do not include any extraneous text, explanations, apologies, or any instructional artifacts or delimiters (like XML-style tags such as `<md>` or any other tags used to structure this prompt) from the prompt in your actual response. Your output should be clean, valid Markdown content as specified.**
    * If, after analysis and filtering, no individuals warrant a consolidated profile, your entire output should be ONLY the specific text defined in the user prompt for this scenario.
""")

REDUCE_USER_MESSAGE_TEMPLATE = dedent("""
    Analyze the following text payload. This payload is a concatenation of Markdown summary blocks, each detailing a person's activities from various meeting transcripts (each block starts with "## Person Identified:").

    Perform entity resolution and synthesis on this aggregated data. Your goal is to generate a final output consisting of one complete Markdown profile for each unique key individual identified, following the criteria and instructions in the system message.

    If, after your analysis, no individuals meet the criteria for a full consolidated profile, your entire output must be *only* the following text and nothing else:
    "No consolidated profiles generated based on the provided input."

    Text Payload (Concatenated Map Phase Outputs):
    <md_payload_input>
    {{CONCATENATED_MARKDOWN_BLOCKS_HERE}}
    </md_payload_input>

    Instructions & Final Profile Format:
    For each unique person deemed significant, generate one profile. The exact Markdown structure for each profile is defined *within* the `<md>` and `</md>` tags shown below.

    <md>
    ## Profile: [Canonical Name - Choose the best, most complete, and formal full name found or synthesized across all provided map outputs and interactions for this individual]

    * **Aliases:** `[List all unique name variations observed for this person across map outputs, including any inferred names that were resolved to this canonical name, comma-separated]`
    * **Inferred Role/Focus:** `[Synthesize their primary organizational role and/or focus area based on overall activity, topics consistently discussed, nature of contributions, and decisions involved in across all relevant map outputs. Be specific if possible, e.g., "Technical Lead for Project X," "Primary Sales contact for Y account," "Voice of customer support in planning meetings." If role seems to have changed, note the most current or prominent one.]`
    * **Interaction Frequency with Group/Meetings:** `[Estimate High, Medium, or Low based on the number of map blocks this person appears in and the stated significance of their participation within those blocks.]`
    * **Period Active (based on transcripts):** `[Estimate based on the earliest and latest Date Hints from map outputs associated with this person, e.g., From<y_bin_46>-MM-DD to<y_bin_46>-MM-DD]`

    ### Overall Summary & Activity:

    `[Write a narrative paragraph (approx. 150-250 words) summarizing their key contributions, activities, prevalent stances, and overall involvement across all relevant map outputs. Crucially, include any significant changes or evolution in their role, focus, contributions, or opinions over the active period. If identifiable from dates, highlight their 1-2 most impactful recent activities or contributions.]`

    ### Key Topics & Projects Involved:

    * `[Synthesize and list the main topics/projects they consistently engage with, drawing from "Topics Discussed" in map outputs. Prioritize topics with repeated engagement or significant contributions.]`
    * `... (add more topics as needed)`

    ### Consolidated Action Items:

    * `[Action Item text] (Assigned: [Date Hint from map output -<y_bin_46>-MM-DD], Source: [Source Transcript from map output], Status Hint: [Infer status, e.g., Assigned, In Progress (if later mentioned as ongoing), Completed (if later mentioned as done/closed), Overdue (if date has passed with no completion update), Blocked. Default to 'Assigned' if no other information. Note if status changes across transcripts, e.g., 'Initially Assigned (SourceA, DateA), later marked Completed in (SourceB, DateB)'.])`
    * `(List all unique consolidated action items assigned to this person. State if 'None outstanding' or 'All appear completed' based on available information.)`

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

    ### Mentioned In Sources:

    * `[List all unique Transcript Source filenames where this person was identified or significantly mentioned, drawing from the relevant map outputs.]`
    * `...`
    </md>

    Ensure the output strictly follows the Markdown structure defined *within* the `<md>` tags above for each person's profile. Each profile must begin with "## Profile:". Do not include any horizontal rule separators, or any other explanatory text outside of the structured profiles themselves. Use `YYYY-MM-DD` for dates.
""")

# Initialize the map agent with defaults from settings
map_agent = Agent(
    model=settings.map_phase.llm_model,
    instructions=MAP_SYSTEM_PROMPT,
)

# Initialize the reduce agent with defaults from settings
reduce_agent = Agent(
    model=settings.reduce_phase.llm_model,
    instructions=REDUCE_SYSTEM_PROMPT,
)
