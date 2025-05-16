import pytest
from trio import Path

from synapse.processors.reduce import sanitize_filename, sort_map_files


def test_sanitize_filename_basic():
    assert sanitize_filename('John Doe') == 'john_doe'


def test_sanitize_filename_illegal_chars():
    input_name = "Jane O'Connor/Smith"
    assert sanitize_filename(input_name) == 'jane_o_connor_smith'


def test_sanitize_filename_whitespace():
    assert sanitize_filename('  Alice  ') == 'alice'


@pytest.mark.trio
async def test_sort_map_files_chronological_and_alphabetical():
    paths = [
        Path('2024-01-02 10_00.map.md'),
        Path('notes.map.md'),
        Path('2023-12-31 08_00.map.md'),
        Path('alpha.map.md'),
        Path('2024-01-01 09_00.map.md'),
    ]

    sorted_paths = await sort_map_files(paths)
    expected_order = [
        Path('2023-12-31 08_00.map.md'),
        Path('2024-01-01 09_00.map.md'),
        Path('2024-01-02 10_00.map.md'),
        Path('alpha.map.md'),
        Path('notes.map.md'),
    ]

    assert sorted_paths == expected_order

