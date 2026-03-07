def recursive_split(
    text: str,
    chunk_size: int = 1500,
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


def _handle_section(
    heading: str | None,
    body: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    """Return one or more chunks for a Markdown section.

    If the whole section fits in chunk_size, return it as a single chunk.
    Otherwise split the body with recursive_split and prepend the heading to
    each sub-chunk so retrieval context is preserved.
    """
    full = (f"{heading}\n\n{body}" if heading else body).strip()
    if not full:
        return []

    if len(full) <= chunk_size:
        return [full]

    sub_chunks = recursive_split(body, chunk_size=chunk_size, chunk_overlap=0)
    if heading:
        return [f"{heading}\n\n{sub}".strip() for sub in sub_chunks if sub.strip()]
    return [sub for sub in sub_chunks if sub.strip()]


def _apply_paragraph_aware_overlap(
    chunks: list[str],
    chunk_overlap: int,
) -> list[str]:
    """Prepend a paragraph-aware overlap snippet from the previous chunk.

    Priority: last paragraph boundary (\\n\\n) → last word boundary (space) →
    raw character slice (original behaviour).
    """
    if chunk_overlap <= 0 or len(chunks) <= 1:
        return chunks

    result = [chunks[0]]
    for i in range(1, len(chunks)):
        prev = chunks[i - 1]
        tail = prev[-chunk_overlap:] if len(prev) > chunk_overlap else prev

        # Prefer paragraph boundary
        para_idx = tail.rfind("\n\n")
        if para_idx != -1:
            overlap = tail[para_idx + 2:]
        else:
            # Fall back to word boundary
            word_idx = tail.rfind(" ")
            overlap = tail[word_idx + 1:] if word_idx != -1 else tail

        result.append((overlap + "\n\n" + chunks[i]).strip() if overlap.strip() else chunks[i])

    return result


def markdown_split(
    text: str,
    chunk_size: int = 1500,
    chunk_overlap: int = 200,
    min_chunk_size: int = 100,
) -> list[str]:
    """Split Markdown text on ## headings, then fall back to recursive_split.

    Produces structure-aware chunks where each chunk begins with its section
    heading, improving retrieval relevance for structured documents.

    Falls back gracefully when no ## headings are present (e.g. plain .txt).
    """
    # Split on "\n## " so we don't falsely split inside fenced code blocks
    # that lack a leading newline before the heading marker.
    parts = text.split("\n## ")
    preamble = parts[0]
    sections = parts[1:]

    chunks: list[str] = []

    # Process preamble (content before first ## heading)
    chunks.extend(_handle_section(None, preamble, chunk_size, chunk_overlap))

    # Process each ## section
    for section in sections:
        lines = section.split("\n", 1)
        heading = "## " + lines[0].strip()
        body = lines[1] if len(lines) > 1 else ""
        chunks.extend(_handle_section(heading, body, chunk_size, chunk_overlap))

    # Apply paragraph-aware overlap between all chunks
    chunks = _apply_paragraph_aware_overlap(chunks, chunk_overlap)

    # Remove undersized orphan chunks
    return [c for c in chunks if len(c.strip()) >= min_chunk_size]
