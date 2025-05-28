"""Parser for Telegram JSON exports to transcript-like markdown format."""

import csv
import json
from collections import defaultdict
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ReactionUser(BaseModel):
    """User who reacted to a message."""

    from_: str = Field(alias='from')
    from_id: str
    date: str

    class Config:
        frozen = True


class Reaction(BaseModel):
    """Telegram reaction data."""

    type: str
    count: int
    emoji: str | None = None  # Custom emojis don't have this field
    recent: list[ReactionUser]

    class Config:
        frozen = True


class TelegramMessage(BaseModel):
    """Represents a parsed Telegram message."""

    id: int
    date: datetime
    author: str = Field(alias='from')
    text: str | list[dict[str, Any]] | None = None
    reply_to_message_id: int | None = None
    photo: str | None = None
    file: str | None = None
    sticker_emoji: str | None = None
    poll: dict[str, Any] | None = None
    reactions: list[Reaction] = []

    class Config:
        frozen = True

    @field_validator('text', mode='before')
    def parse_text(cls, v: str | list[dict[str, Any] | str] | None) -> str:
        """Handle Telegram's mixed text format."""
        if isinstance(v, list):
            parts: list[str] = []
            for part in v:
                if isinstance(part, dict):
                    parts.append(part.get('text', ''))
                else:
                    parts.append(str(part))
            return ''.join(parts)
        return v or ''

    @property
    def channel_id(self) -> int | None:
        """Get the channel ID this message belongs to."""
        return self.reply_to_message_id

    @property
    def formatted_time(self) -> str:
        """Format timestamp as HH:MM."""
        return self.date.strftime('%H:%M')

    @property
    def media_indicators(self) -> list[str]:
        """Get list of media type indicators."""
        indicators: list[str] = []

        if self.photo:
            indicators.append('[Photo]')
        if self.file:
            indicators.append(f'[Document: {self.file}]')
        if self.poll:
            indicators.append('[Poll]')
        if self.sticker_emoji:
            indicators.append(f'[Sticker: {self.sticker_emoji}]')

        return indicators

    @property
    def reaction_emojis(self) -> list[str]:
        """Extract reaction emojis."""
        return [r.emoji for r in self.reactions if r.emoji]

    def to_transcript_line(self) -> str:
        """Convert to transcript-style line."""
        # Build content
        content_parts: list[str] = []

        # Add media indicators
        if self.media_indicators:
            content_parts.extend(self.media_indicators)

        # Add text
        if self.text and isinstance(self.text, str):
            content_parts.append(self.text)

        # Combine content
        content = ' '.join(content_parts) if content_parts else '[Empty message]'

        # Add reactions
        if self.reaction_emojis:
            content += f' [{", ".join(self.reaction_emojis)}]'

        return f'[{self.formatted_time}] {self.author}: {content}'


class Channel(BaseModel):
    """Represents a channel with its messages."""

    name: str
    messages: tuple[TelegramMessage, ...]

    class Config:
        frozen = True

    def to_markdown_section(self) -> str:
        """Convert channel to markdown section."""
        lines = [f'## {self.name}', '']

        # Sort messages by timestamp
        sorted_messages = sorted(self.messages, key=lambda m: m.date)

        # Add each message
        for msg in sorted_messages:
            lines.append(msg.to_transcript_line())

        return '\n'.join(lines)


def load_topic_mapping(mapping_path: Path) -> dict[int, str]:
    """Load topic ID to channel name mapping from CSV."""
    with open(mapping_path) as f:
        return {int(row['topic_id']): row['topic_name'] for row in csv.DictReader(f)}


def extract_messages(data: dict[str, Any]) -> Iterator[TelegramMessage]:
    """Extract and parse non-service messages from Telegram data."""
    # Filter non-service messages
    non_service_messages = [msg for msg in data.get('messages', []) if msg.get('type') != 'service']

    for raw_msg in non_service_messages:
        try:
            yield TelegramMessage.model_validate(raw_msg)
        except Exception as e:
            msg_id = raw_msg.get('id', 'unknown')
            print(f'Warning: Failed to parse message {msg_id}: {e}')
            continue


def group_by_channel(
    messages: Iterator[TelegramMessage], topic_mapping: dict[int, str]
) -> dict[str, list[TelegramMessage]]:
    """Group messages by their channel."""
    channels: defaultdict[str, list[TelegramMessage]] = defaultdict(list)

    for msg in messages:
        if msg.channel_id and msg.channel_id in topic_mapping:
            channel_name = topic_mapping[msg.channel_id]
        else:
            channel_name = 'General'

        channels[channel_name].append(msg)

    return dict(channels)


def build_transcript(channels: dict[str, list[TelegramMessage]], week_date: str = '') -> str:
    """Build the final transcript markdown."""
    sections: list[str] = []

    # Header
    sections.append('# Telegram Export Transcript')
    if not week_date:
        week_date = datetime.now().strftime('%B %d, %Y')
    sections.append(f'\nWeek of {week_date}')
    sections.append('')

    # Process channels in alphabetical order
    for channel_name in sorted(channels.keys()):
        if channels[channel_name]:  # Skip empty channels
            channel = Channel(name=channel_name, messages=tuple(channels[channel_name]))
            sections.append(channel.to_markdown_section())
            sections.append('')  # Empty line between channels

    return '\n'.join(sections).rstrip() + '\n'


def parse_telegram_export(
    telegram_json_path: Path | str, topic_mapping_path: Path | str, output_path: Path | str
) -> None:
    """
    Parse Telegram JSON export and convert to transcript-like markdown format.

    This is the main orchestrator function that handles I/O and delegates
    to pure transformation functions.

    Args:
        telegram_json_path: Path to the Telegram JSON export file
        topic_mapping_path: Path to CSV file mapping topic IDs to channel names
        output_path: Path where the markdown output will be written
    """
    # Convert to Path objects
    telegram_json_path = Path(telegram_json_path)
    topic_mapping_path = Path(topic_mapping_path)
    output_path = Path(output_path)

    # Load inputs
    topic_mapping = load_topic_mapping(topic_mapping_path)

    with open(telegram_json_path) as f:
        telegram_data = json.load(f)

    # Pure transformations
    messages = extract_messages(telegram_data)
    channels = group_by_channel(messages, topic_mapping)

    # Extract week date from filename if possible
    week_date = ''
    if 'week_' in telegram_json_path.name:
        try:
            date_part = telegram_json_path.stem.split('week_')[1]
            week_date = datetime.strptime(date_part, '%Y-%m-%d').strftime('%B %d, %Y')
        except (ValueError, IndexError):
            pass

    transcript = build_transcript(channels, week_date)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(transcript)

    print(f'✓ Telegram export parsed: {len(channels)} channels')
    print(f'✓ Output saved to: {output_path}')


if __name__ == '__main__':
    # Example usage
    parse_telegram_export(
        telegram_json_path='data/telegram_export_week_2025-04-28.json',
        topic_mapping_path='data/telegram_topic_mapping.csv',
        output_path='output/telegram_transcript_week_2025-04-28.md',
    )
