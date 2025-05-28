# Engineering Sprint: Weekly Newsletter MVP

**Due:** Tomorrow's meeting  
**Goal:** Ship first newsletter covering last week's activity

## Technical Requirements

### Input Data Sources

1. **Telegram Export** (JSON format)
   - Single group with multiple topic channels
   - Messages clustered by `reply_to_message_id` field (channels mapped via CSV)
   - Already filtered to week of April 28, 2025

2. **Meeting Transcripts** (Text files)
   - All hands meeting transcript
   - Engineering meeting transcript
   - Plain text format

### Data Processing Pipeline

**Step 1: Data Ingestion**

- Parse Telegram JSON export
- Cluster messages into channels using reply_to_message_id with topic mapping CSV
- Load meeting transcripts as text

**Step 2: Content Synthesis**
Generate newsletter with these sections:

- Key Decisions & Outcomes
- Active Discussions  
- Project Updates
- Blockers & Open Questions
- Next Week's Focus

**Step 3: Output**

- Markdown format
- 5-10 minute read length
- Include source references where possible

## 📰 Newsletter Template

The agreed-upon structure for the weekly newsletter:

📍 **The Week's Highlights**

- Major wins and breakthroughs
- Key decisions that affect multiple people
- Important pivots or strategy changes

🎯 **Progress & Momentum**

- What shipped or got completed
- Demos and cool stuff people built
- Metrics/results if available

💡 **Interesting Discussions**

- Technical insights or "aha" moments
- Creative solutions to problems
- Good questions that sparked useful debates

🚧 **Heads Up**

- Upcoming changes or migrations
- Things that might affect people's work
- New tools or processes being adopted

🎪 **The Human Side**

- Funny moments or quotes
- Team member shoutouts
- Interesting side conversations

🔗 **Resources to Check Out**

- Useful links shared with context
- New docs or tools
- External articles/research mentioned

### Technical Implementation

**Required Functions:**

1. `parse_telegram_export(json_file)` → clustered messages by channel
2. `process_meeting_transcripts(transcript_files)` → structured content
3. `synthesize_newsletter(telegram_data, meeting_data)` → final markdown

**LLM Integration:**

- Use structured prompts for each newsletter section
- Include source attribution in outputs
- Keep synthesis concise and actionable

### Deliverables for Tomorrow

1. Working script that processes provided data files
2. Generated newsletter for last week
3. Simple README for running the process

### Data Available

- `data/telegram_export_week_2025-04-28.json` (filtered for week of April 28, 2025)
- `data/2025-04-28 flashbotsX all-hands.txt`
- `data/2025-04-30 14_30 flashbotsX engineering.txt`
- `data/telegram_topic_mapping.csv` (maps topic IDs to channel names)

**Success Criteria:** Newsletter is readable, covers key points, and takes <10 minutes to generate from provided files.

## Progress Tracking

### ✅ Completed

- [x] Created filtering script for Telegram export data
- [x] Filtered Telegram data to week of April 28, 2025 (97 messages)
- [x] Updated sprint document with correct file references
- [x] Implemented `parse_telegram_export()` function with full type safety
- [x] Created telegram parser module with Pydantic models
- [x] Successfully parsed Telegram export to transcript markdown format
- [x] Fixed development environment issues (ruff formatter consistency, pyright version)
- [x] Implemented newsletter extraction functions (`extract_newsletter_meeting()`, `extract_newsletter_telegram()`)
- [x] Created newsletter-specific agents with tailored prompts for meetings and Telegram
- [x] Extended MapReduce infrastructure to support multiple extraction types
- [x] Generated Telegram transcript from filtered export (output/telegram_transcript_week_2025-04-28.md)

### 🔄 In Progress

- [ ] Integrate newsletter extraction functions into main.py pipeline
- [ ] Run map phase on meeting transcripts with newsletter extraction
- [ ] Implement newsletter reduce phase for synthesis

### 📋 To Do

- [ ] Test complete pipeline with all data files (meetings + Telegram)
- [ ] Create README for running the newsletter generation process
- [ ] Generate final newsletter output
- [ ] Verify newsletter covers all required sections per spec

### 🚧 Blockers

- None currently

### 📝 Notes

- Telegram export has 97 messages after filtering
- Messages clustered by `reply_to_message_id` field (channels mapped via CSV)
- Using existing MapReduce infrastructure from synapse for newsletter synthesis
- Telegram parser outputs transcript-style markdown ready for processing
- Newsletter extraction functions and agents created but not yet integrated into main pipeline
- Map phase refactored to accept generic extraction functions

### 🏗️ Architecture Decision: Directory-Based File Type Detection (MVP)

**Goal:** Support multiple file types (meetings, Telegram) for newsletter extraction without implicit filename pattern matching.

**Agreed Design:**

Use directory structure to explicitly indicate file types:
```
data/
  meetings/      # All meeting transcripts go here
  telegram/      # All Telegram exports go here
```

**Benefits:**
- User intent is explicit through folder organization
- No hidden filename conventions
- Naturally supports multiple Telegram groups in future (e.g., `telegram/main-group/`)
- Zero configuration needed - just put files in the right folder

**Implementation:**
- Add directory paths to config (meetings_dir, telegram_dir)
- Process each directory separately with known file type
- Route to appropriate extraction function based on directory source
