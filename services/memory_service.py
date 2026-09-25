import re
import html
from services.metadata import (
    extract_metadata,
    parse_text_and_spans,
    rebuild_text_from_spans
)
from services.types import MetadataType
from services.metadata import without_verbatim_copy, VERBATIM_BLOCK_RE


# =========================
# CLEAN TEXT
# =========================
def clean_text(text):
    if not text:
        return ""

    text = without_verbatim_copy(text)
    text = html.unescape(text)
    text = text.replace("\r\n", "\n").strip()

    # remove RDF
    text = re.sub(r'<rdf:RDF.*?</rdf:RDF>', '', text, flags=re.DOTALL)

    return text


# =========================
# REMOVE MEMORY BLOCK
# =========================
def remove_memory_block(text):
    return re.sub(
        r'===\s*MEMORY METADATA START\s*===.*?===\s*MEMORY METADATA END\s*===',
        '',
        text,
        flags=re.DOTALL
    )


# =========================
# BUILD MEMORY BLOCK 
# =========================
def build_memory_block(metadata):
    ordered_items = []
    for preferred_key in ("dc:identifier", "dc:license"):
        value = metadata.get(preferred_key)
        if value and value.strip():
            ordered_items.append((preferred_key, value))

    for key, value in metadata.items():
        if key in {"dc:identifier", "dc:license"}:
            continue
        if value and value.strip():
            ordered_items.append((key, value))

    lines = [f'<{key} type="memory">{value}</{key}>' for key, value in ordered_items]

    return (
        "=== MEMORY METADATA START ===\n"
        + "\n".join(lines)
        + "\n=== MEMORY METADATA END ===\n\n"
    )


# =========================
# BUILD SPANS FROM METADATA
# =========================
def build_spans(clean_text, memory_md, cho_md):
    spans = []

    # CHO
    for md in cho_md:
        start = clean_text.find(md["value"])
        if start == -1:
            continue

        spans.append({
            "start": start,
            "end": start + len(md["value"]),
            "field": md["field"],
            "value": md["value"],
            "cho": md.get("cho"),
            "type": MetadataType.CHO.value
        })

    # MEMORY
    for field, value in memory_md.items():
        start = clean_text.find(value)

        if start == -1:
            spans.append({
                "field": field,
                "value": value,
                "type": MetadataType.MEMORY.value
            })
            continue

        spans.append({
            "start": start,
            "end": start + len(value),
            "field": field,
            "value": value,
            "type": MetadataType.MEMORY.value
        })

    return spans

# =========================
# FULL REBUILD PIPELINE 
# =========================
def rebuild_memory_text(original_text, new_metadata, memory_id=None):

    metadata = dict(new_metadata or {})
    if memory_id is not None:
        metadata["dc:identifier"] = str(memory_id)

    protected = VERBATIM_BLOCK_RE.search(original_text or "")
    txt = clean_text(original_text)

    # remove existing memory block
    txt = remove_memory_block(txt)

    # parse clean content
    clean, _ = parse_text_and_spans(txt)

    # preserve CHO metadata
    cho_md = [
        md for md in extract_metadata(original_text)
        if md.get("type") == MetadataType.CHO.value
    ]

    # rebuild spans
    spans = build_spans(clean, metadata, cho_md)

    # rebuild block
    block = build_memory_block(metadata)

    # rebuild text
    content = rebuild_text_from_spans(clean, spans).lstrip("\n")

    rebuilt = block + content
    if protected:
        rebuilt = rebuilt.rstrip("\n") + "\n\n" + protected.group(0).rstrip("\n") + "\n"
    return rebuilt


def append_verbatim_copy(text, original_text):
    if VERBATIM_BLOCK_RE.search(text or ""):
        return text
    clean_original = re.sub(
        r'</?[a-zA-Z][a-zA-Z0-9:_@-]*(?:\s+[^>]*)?>',
        '',
        without_verbatim_copy(original_text),
    )
    return (
        (text or "").rstrip("\n")
        + "\n\n=== MEMORY VERBATIM COPY START ===\n"
        + clean_original
        + "\n=== MEMORY VERBATIM COPY END ===\n"
    )


def preserve_verbatim_copy(editable_text, original_text):
    original_match = VERBATIM_BLOCK_RE.search(original_text or "")
    editable = without_verbatim_copy(editable_text)
    if not original_match:
        return editable
    return editable.rstrip("\n") + "\n\n" + original_match.group(0).rstrip("\n") + "\n"
