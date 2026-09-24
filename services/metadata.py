import re
import logging
from services.types import MetadataType


LOGGER = logging.getLogger(__name__)


# =========================
# REGEX (REAL TAGS)
# =========================
COMBINED_RE = re.compile(
    r'<(?P<field>[a-zA-Z0-9:_@-]+)'
    r'(?:\s+cho="(?P<cho>[^"]+)"|\s+type="(?P<type>memory)")>'
    r'(?P<value>.*?)</\1>',
    re.DOTALL
)

VERBATIM_BLOCK_RE = re.compile(
    r'===\s*MEMORY VERBATIM COPY START\s*===.*?===\s*MEMORY VERBATIM COPY END\s*===\s*',
    re.DOTALL,
)


def without_verbatim_copy(text):
    return VERBATIM_BLOCK_RE.sub('', text or '')


def split_metadata_field(field):
    if "@" in field:
        name, space = field.rsplit("@", 1)
        return name, space
    return field, "EDM"


def _overlapping_tag_matches(text):
    for position, character in enumerate(text or ""):
        if character != "<":
            continue
        match = COMBINED_RE.match(text, position)
        if match:
            yield match


def _clean_metadata_value(value):
    return re.sub(
        r'</?[a-zA-Z][a-zA-Z0-9:_@-]*(?:\s+[^>]*)?>',
        '',
        value or '',
    )


# =========================
# PARSE TEXT + SPANS 
# =========================
def parse_text_and_spans(text, metadata_space=None, recognized_fields=None):
    if not text:
        return "", []

    try:
        text = without_verbatim_copy(text)
        # =========================
        # STEP 1: Extract memory metadata block
        # =========================
        block_pattern = r'===\s*MEMORY METADATA START\s*===(.*?)===\s*MEMORY METADATA END\s*==='
        block_match = re.search(block_pattern, text, re.DOTALL)

        memory_md = []

        if block_match:
            block = block_match.group(1)

            for m in COMBINED_RE.finditer(block):
                field, space = split_metadata_field(m.group("field"))
                if metadata_space and (space != metadata_space or (recognized_fields and field not in recognized_fields)):
                    continue
                if m.group("type") == "memory":
                    memory_md.append({
                        "field": m.group("field"),
                        "value": _clean_metadata_value(m.group("value")),
                        "type": MetadataType.MEMORY.value
                    })

            # remove block from visible text
            text = re.sub(block_pattern, '', text, flags=re.DOTALL)

        # =========================
        # STEP 2: Parse inline tags
        # =========================
        spans = []
        clean = ""
        idx = 0

        for m in COMBINED_RE.finditer(text):
            field, space = split_metadata_field(m.group("field"))
            if metadata_space and (space != metadata_space or (recognized_fields and field not in recognized_fields)):
                clean += text[idx:m.start()] + m.group("value")
                idx = m.end()
                continue
            start, end = m.span()

            clean += text[idx:start]
            inner = m.group("value")

            span_start = len(clean)
            clean += inner
            span_end = len(clean)

            spans.append({
                "start": span_start,
                "end": span_end,
                "field": m.group("field"),
                "metadata_space": space,
                "cho": m.group("cho"),
                "value": inner,
                "type": MetadataType.MEMORY.value
                    if m.group("type") == "memory"
                    else MetadataType.CHO.value
            })

            idx = end

        clean += text[idx:]

        # =========================
        # STEP 3: Map memory metadata into clean text
        # =========================
        for md in memory_md:
            value = md["value"]
            start = clean.find(value)

            span = {
                "field": md["field"],
                "value": value,
                "type": MetadataType.MEMORY.value
            }

            if start != -1:
                span["start"] = start
                span["end"] = start + len(value)

            spans.append(span)

        residual_tag_pattern = r'</?[a-zA-Z][a-zA-Z0-9:_@-]*(?:\s+[^>]*)?>'
        if re.search(residual_tag_pattern, clean):
            clean = re.sub(residual_tag_pattern, '', clean)
            search_from = 0
            for span in sorted(spans, key=lambda s: s.get("start", -1)):
                value = span.get("value", "")
                if not value:
                    continue
                start = clean.find(value, search_from)
                if start == -1:
                    span.pop("start", None)
                    span.pop("end", None)
                    continue
                span["start"] = start
                span["end"] = start + len(value)
                search_from = span["end"]

        if metadata_space:
            existing_span_keys = {(span.get("field"), span.get("value")) for span in spans}
            for match in _overlapping_tag_matches(text):
                field, space = split_metadata_field(match.group("field"))
                if space != metadata_space or (recognized_fields and field not in recognized_fields):
                    continue
                value = re.sub(residual_tag_pattern, '', match.group("value"))
                key = (match.group("field"), value)
                if not value or key in existing_span_keys:
                    continue
                start = clean.find(value)
                if start == -1:
                    continue
                spans.append({
                    "start": start,
                    "end": start + len(value),
                    "field": match.group("field"),
                    "metadata_space": space,
                    "cho": match.group("cho"),
                    "value": value,
                    "type": MetadataType.MEMORY.value if match.group("type") == "memory" else MetadataType.CHO.value,
                })
                existing_span_keys.add(key)

        spans.sort(key=lambda s: s.get("start", -1))

        return clean, spans

    except Exception:
        LOGGER.exception("Metadata span parsing failed")
        return "", []


# =========================
# EXTRACT METADATA 
# =========================
def extract_metadata(text, metadata_space=None, recognized_fields=None):
    if not text:
        return []

    text = without_verbatim_copy(text)

    metadata = []

    # =========================
    # MEMORY BLOCK
    # =========================
    memory_blocks = re.findall(
        r'=== MEMORY METADATA START ===(.*?)=== MEMORY METADATA END ===',
        text,
        flags=re.DOTALL
    )

    for block in memory_blocks:
        for m in COMBINED_RE.finditer(block):
            field, space = split_metadata_field(m.group("field"))
            if metadata_space and (space != metadata_space or (recognized_fields and field not in recognized_fields)):
                continue
            metadata.append({
                "field": m.group("field"),
                "metadata_space": space,
                "cho": None,
                "value": _clean_metadata_value(m.group("value")),
                "type": MetadataType.MEMORY.value
            })

    # =========================
    # REMOVE MEMORY BLOCK
    # =========================
    text_wo_memory = re.sub(
        r'=== MEMORY METADATA START ===.*?=== MEMORY METADATA END ===',
        '',
        text,
        flags=re.DOTALL
    )

    # =========================
    # CHO METADATA
    # =========================
    for m in COMBINED_RE.finditer(text_wo_memory):
        field, space = split_metadata_field(m.group("field"))
        if metadata_space and (space != metadata_space or (recognized_fields and field not in recognized_fields)):
            continue
        metadata.append({
            "field": m.group("field"),
            "metadata_space": space,
            "cho": m.group("cho"),
            "value": _clean_metadata_value(m.group("value")),
            "type": MetadataType.CHO.value
        })

    if metadata_space:
        seen = {(item.get("field"), item.get("value"), item.get("cho")) for item in metadata}
        for m in _overlapping_tag_matches(text_wo_memory):
            field, space = split_metadata_field(m.group("field"))
            if space != metadata_space or (recognized_fields and field not in recognized_fields):
                continue
            value = _clean_metadata_value(m.group("value"))
            item = (m.group("field"), value, m.group("cho"))
            if not value or item in seen:
                continue
            metadata.append({
                "field": m.group("field"),
                "metadata_space": space,
                "cho": m.group("cho"),
                "value": value,
                "type": MetadataType.CHO.value,
            })
            seen.add(item)

    deduplicated = []
    seen = set()
    for item in metadata:
        key = (item.get("field"), item.get("cho"), item.get("value"), item.get("type"))
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(item)
    return deduplicated


# =========================
# MEMORY TITLE
# =========================
def get_memory_title(text, fallback):
    if not text:
        return fallback

    text = text.lstrip("\ufeff \n\t")

    match = re.search(
        r'<(?:web:)?dc:title[^>]*type="memory"[^>]*>(.*?)</(?:web:)?dc:title>',
        text,
        re.DOTALL
    )
    if match:
        return match.group(1).strip()

    match = re.search(
        r'<(?:web:)?dc:title[^>]*>(.*?)</(?:web:)?dc:title>',
        text,
        re.DOTALL
    )
    if match:
        return match.group(1).strip()

    return fallback


# =========================
# REBUILD TEXT FROM SPANS
# =========================
def rebuild_text_from_spans(text, spans):
    offset = 0

    valid_spans = [s for s in spans if "start" in s and "end" in s]

    for span in sorted(valid_spans, key=lambda s: s["start"]):
        start = span["start"] + offset
        end = span["end"] + offset

        if span["type"] == MetadataType.MEMORY.value:
            wrapped = (
                f'<{span["field"]} type="memory">'
                f'{text[start:end]}'
                f'</{span["field"]}>'
            )
        else:
            wrapped = (
                f'<{span["field"]} cho="{span["cho"]}">'
                f'{text[start:end]}'
                f'</{span["field"]}>'
            )

        text = text[:start] + wrapped + text[end:]
        offset += len(wrapped) - (end - start)

    return text