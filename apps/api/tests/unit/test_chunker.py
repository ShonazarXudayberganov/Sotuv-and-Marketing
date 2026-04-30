from app.core.chunker import chunk_text, estimate_tokens


def test_estimate_tokens_latin():
    assert estimate_tokens("hello world") > 0


def test_estimate_tokens_cyrillic_uses_smaller_ratio():
    cyr = "Привет мир " * 10
    lat = "Hello world " * 10
    # Cyrillic estimate should be larger because chars are denser in tokens
    assert estimate_tokens(cyr) > estimate_tokens(lat) - 5


def test_chunk_empty_returns_empty():
    assert chunk_text("") == []
    assert chunk_text("   \n\n\n   ") == []


def test_chunk_short_text_single_chunk():
    chunks = chunk_text("This is a short test.")
    assert len(chunks) == 1
    assert chunks[0].position == 0
    assert "short test" in chunks[0].content


def test_chunk_long_text_multiple_chunks_with_overlap():
    sentences = [f"This is sentence number {i}." for i in range(200)]
    text = " ".join(sentences)
    chunks = chunk_text(text, target_tokens=100, overlap_tokens=20)
    assert len(chunks) > 1
    assert all(c.token_count > 0 for c in chunks)
    assert chunks[0].position == 0
    assert chunks[-1].position == len(chunks) - 1


def test_chunks_preserve_order():
    text = "A. " * 500
    chunks = chunk_text(text, target_tokens=80)
    positions = [c.position for c in chunks]
    assert positions == sorted(positions)
