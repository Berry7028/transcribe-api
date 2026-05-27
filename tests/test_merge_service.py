import pytest

from app.services.merge_service import ChunkTranscription, merge_chunk_transcriptions, normalize_text


def test_normalize_text_strips_and_collapses_whitespace():
    assert normalize_text("  hello\n\n  world\t ") == "hello world"
    assert normalize_text("   ") == ""


def test_merge_chunk_transcriptions_orders_chunks_and_builds_response_chunks():
    result = merge_chunk_transcriptions(
        [
            ChunkTranscription(index=1, start_seconds=1.0, end_seconds=2.5, text=" second "),
            ChunkTranscription(index=0, start_seconds=0.0, end_seconds=1.0, text="first\npart"),
        ]
    )

    assert result.text == "first part second"
    assert result.duration_seconds == 2.5
    assert [chunk.index for chunk in result.chunks] == [0, 1]
    assert [chunk.text for chunk in result.chunks] == ["first part", "second"]


def test_merge_chunk_transcriptions_rejects_empty_input():
    with pytest.raises(ValueError, match="結合するチャンク"):
        merge_chunk_transcriptions([])
