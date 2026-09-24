import csv
import io
from datetime import date

from db import MetadataSpace, session
from services.metadata_schema import METADATA_FIELDS

DEFAULT_SPACE_NAME = "EDM"
DEFAULT_SPACE_LABEL = "EDM — Europeana Data Model"


def _default_fields():
    fields = []
    seen = set()
    for group in METADATA_FIELDS.values():
        for name, details in group.get("fields", {}).items():
            if name in seen:
                continue
            seen.add(name)
            fields.append({"name": name, "description": details.get("description", "")})
    return fields


def ensure_default_space():
    space = session.query(MetadataSpace).filter_by(name=DEFAULT_SPACE_NAME).first()
    if space is None:
        space = MetadataSpace(
            name=DEFAULT_SPACE_NAME,
            author="CORDHISK",
            updated_at=str(date.today()),
            description=DEFAULT_SPACE_LABEL,
        )
        space.fields = _default_fields()
        session.add(space)
        session.commit()
    return space


def list_spaces():
    ensure_default_space()
    return session.query(MetadataSpace).order_by(MetadataSpace.name).all()


def get_space(name):
    if not name:
        return ensure_default_space()
    return session.query(MetadataSpace).filter_by(name=name).first()


def parse_space_csv(content):
    rows = list(csv.reader(io.StringIO(content or "")))
    if len(rows) >= 6 and all(len(row) == 2 for row in rows[:5]):
        property_labels = [row[0].strip().casefold() for row in rows[:4]]
        expected_labels = ["metadata scheme name", "creator", "last update", "description"]
        if property_labels != expected_labels:
            raise ValueError("The first four CSV rows must define name, creator, last update, and description.")
        values = [row[1].strip() for row in rows[:4]]
        if not all(values):
            raise ValueError("Metadata Space name, creator, date, and description are required.")
        field_header_index = 4
    elif len(rows) >= 3 and len(rows[0]) == 4:
        # Accept files exported by the previous four-values-on-one-row format.
        values = [cell.strip() for cell in rows[0]]
        if not all(values):
            raise ValueError("Metadata Space name, author, date, and description are required.")
        field_header_index = 1
    else:
        raise ValueError("CSV must define Metadata Space properties and fields.")

    if len(rows) <= field_header_index or len(rows[field_header_index]) != 2 or [cell.strip() for cell in rows[field_header_index]] != ["Field", "Description"]:
        raise ValueError("CSV must contain a Field,Description header after the Metadata Space properties.")

    fields = []
    seen = set()
    for row in rows[field_header_index + 1:]:
        if len(row) != 2 or not row[0].strip() or not row[1].strip() or row[0].strip() in seen:
            raise ValueError("Each metadata field must have a unique name and description.")
        seen.add(row[0].strip())
        fields.append({"name": row[0].strip(), "description": row[1].strip()})
    if not fields:
        raise ValueError("The Metadata Space must define at least one field.")
    return {"name": values[0], "author": values[1], "updated_at": values[2], "description": values[3], "fields": fields}


def save_space(definition, replace=False):
    existing = session.query(MetadataSpace).filter_by(name=definition["name"]).first()
    if existing is not None and not replace:
        raise ValueError(f"Metadata Space '{definition['name']}' already exists.")
    space = existing or MetadataSpace()
    space.name = definition["name"]
    space.author = definition["author"]
    space.updated_at = definition["updated_at"]
    space.description = definition["description"]
    space.fields = definition["fields"]
    session.add(space)
    session.commit()
    return space


def space_csv(space):
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["Metadata Scheme Name", space.name])
    writer.writerow(["Creator", space.author])
    writer.writerow(["Last Update", space.updated_at])
    writer.writerow(["Description", space.description])
    writer.writerow(["Field", "Description"])
    for field in space.fields:
        writer.writerow([field.get("name", ""), field.get("description", "")])
    return output.getvalue()