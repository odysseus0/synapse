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

### 🔄 In Progress
- [ ] Implement `process_meeting_transcripts()` function
- [ ] Implement `synthesize_newsletter()` function using MapReduce infrastructure

### 📋 To Do
- [ ] Test complete pipeline with all data files
- [ ] Create README for running the newsletter generation process
- [ ] Generate final newsletter output

### 🚧 Blockers
- None currently

### 📝 Notes
- Telegram export has 97 messages after filtering
- Messages clustered by `reply_to_message_id` field (channels mapped via CSV)
- Using existing MapReduce infrastructure from synapse for newsletter synthesis
- Telegram parser outputs transcript-style markdown ready for processing
