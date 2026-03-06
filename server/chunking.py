def recursive_split(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    separators: list[str] | None = None,
) -> list[str]:
    """
    Recursively split text using a hierarchy of separators.
    Tries structural separators first (\\n\\n), then progressively finer ones.

    No external dependencies — pure Python.
    """
    if separators is None:
        separators = ["\n\n", "\n", ". ", " ", ""]

    chunks = _split_recursive(text, separators, 0, chunk_size)

    # Apply overlap between consecutive chunks
    if chunk_overlap > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev = chunks[i - 1]
            overlap_text = prev[-chunk_overlap:] if len(prev) > chunk_overlap else prev
            overlapped.append(overlap_text + chunks[i])
        chunks = overlapped

    return [c for c in chunks if c.strip()]


def _split_recursive(
    text: str,
    separators: list[str],
    sep_idx: int,
    chunk_size: int,
) -> list[str]:
    """Recursively split text, trying coarser separators first."""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    # No more separators — force character split
    if sep_idx >= len(separators):
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i : i + chunk_size])
        return chunks

    separator = separators[sep_idx]
    splits = text.split(separator) if separator else list(text)

    merged: list[str] = []
    current = ""

    for i, part in enumerate(splits):
        # Re-attach separator (except after the last split)
        segment = part + (separator if i < len(splits) - 1 else "")

        if len(current) + len(segment) <= chunk_size:
            current += segment
        else:
            if current.strip():
                merged.append(current)

            # Segment itself too large — recurse with next separator
            if len(segment) > chunk_size:
                merged.extend(
                    _split_recursive(segment, separators, sep_idx + 1, chunk_size)
                )
                current = ""
            else:
                current = segment

    if current.strip():
        merged.append(current)

    return merged
