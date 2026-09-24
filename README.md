# CORDHISK App v3.0

CORDHISK is a browser-based application for annotating textual memories and connecting their passages to Cultural Heritage Objects (CHOs) through structured metadata.

For a complete functional and technical description suitable for project documentation or a thesis appendix, see [Design, Operation, and Capabilities](ARCHITECTURE.md).

## Run locally

Requires Python 3.10 or later.

```bash
git clone https://github.com/r-eudave/cordhisk_app.git
cd cordhisk_app
python3 -m pip install -r requirements.txt
python3 cordhisk.py
```

The development server uses port 5000 by default. Set `CORDHISK_PORT` to use another port when 5000 is occupied, for example `CORDHISK_PORT=5001 python3 cordhisk.py`. `CORDHISK_HOST` and `CORDHISK_DEBUG` can also be set for local deployment control.

Open http://127.0.0.1:5000/ in a browser. The application runs with Flask's development server.

## Capabilities

- Create, edit, delete, and browse memories and CHOs.
- Import `.txt` memories while preserving or completing embedded memory metadata.
- Annotate selected memory text with metadata from the active Metadata Space. EDM remains the default space and preserves its legacy tag format.
- Create, edit, import, export, and select persistent Metadata Spaces without coupling memories to one scheme.
- Use `Field@Space` tags for non-EDM schemes, allowing metadata from multiple schemes to coexist in one memory.
- Edit memory metadata, including identifiers and usage licences, and manage individual CHO tags.
- Navigate relationships in interactive Memory and CHO views, including a relationship graph.
- Filter the CHO tags displayed for a selected memory.
- Add Memory metadata from the field menu, including licence selection and WGS84 coordinates entered manually or selected on a map, then explore geocoded memories on an interactive map.
- Search memory text with paginated results.
- Compare one CHO across its related memories in a field-by-memory matrix.
- Generate a CHO report grouped by metadata field and instance frequency, with links to related memories and CSV download.
- View a Memory/CHO matrix showing, for every memory and CHO, the number of annotation tags between them, with total annotation counts per memory and per CHO.
- View a Memory/Field matrix showing, for every memory and metadata field (e.g. title, description), how many times that field appears within the memory, regardless of CHO.
- Export Memory and CHO metadata as downloadable RDF/XML.
- Switch between Memories, CHO records, and Metadata views while retaining the active Metadata Space.
- Compare, report, and build Memory/CHO and Memory/Field matrices using only the active Metadata Space.
- Start from an instruction summary, with fixed viewport-height workspace panels and internal scrolling for long memories and graphs.
- Hover graph metadata nodes to locate their highlighted text and click them to select the matching left-panel tag.

## Data storage

CORDHISK stores its SQLite database and memory text files in `memory_files/`. Back up this directory to preserve application data.

Metadata Space definitions are stored in the `metadata_spaces` SQLite table in `memory_files/000_cordhisk.db`. Each definition contains its name, creator, update date, description, and field descriptions. Memory files imported after v3.0 also contain a protected verbatim-copy section recording the original imported text; this section is hidden from editing and metadata interpretation.

Metadata Spaces can be exchanged using CSV files with this structure:

```csv
Metadata Scheme Name,W7
Creator,John Smith
Last Update,2026-09-22
Description,Metadata scheme for W7 memories
Field,Description
Creator,Person responsible for creating the memory
Date,Date associated with the memory
```

The interface uses a solid, warm, colour-blind-friendly palette. The sidebar, central graph, and right memory panel adapt to the browser viewport; long content scrolls inside its panel instead of expanding the whole page.

## Development

Run the automated web application tests with:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Portable desktop builds

The application can be packaged as a portable desktop build with PyInstaller. Build on the target operating system because PyInstaller does not cross-compile executables.

On macOS:

```bash
chmod +x build_macos.sh
./build_macos.sh
open dist/CORDHISK-App-v3.0.app
```

On Windows PowerShell:

```powershell
.\build_windows.ps1
.\executable_win\CORDHISK-App-v3.0.exe
```

The generated onedir bundle includes a writable `memory_files/` directory beside the executable. On macOS, keep `CORDHISK-App-v3.0.app` and the adjacent `memory_files/` directory together inside `dist/`. On Windows, the files are placed directly inside `executable_win/`. This keeps the SQLite database and memory files persistent and portable with the application folder. The launcher opens the application in the default browser. Set `CORDHISK_PORT` if port 5000 is already in use.

Keep the complete Windows `executable_win/` folder together when moving the application; do not copy only the `.exe`. If the browser shows an internal server error, close the application and inspect `executable_win/cordhisk.log`, then share that traceback when reporting the problem.

## Project structure

- `cordhisk.py`: Flask application and HTTP routes.
- `services/`: metadata parsing, schema definitions, data types, memory rebuilding, and HTML templates.
- `services/metadata_spaces.py`: persistent Metadata Space definitions and CSV import/export.
- `memory_files/`: application-managed memory text files and SQLite database.
- `tests/`: automated Flask application tests.

## About

Copyright (c) 2026 Rafael Ramírez Eudave. See [LICENSE](LICENSE).

This code was produced at Delft University of Technology with support from Microsoft Copilot. It builds on: Ramírez Eudave, R., Ferreira, T.M. & Giardina, G. Communities co-creating metadata: a new paradigm towards FAIR everyday heritage. *npj Heritage Science* (2026). https://doi.org/10.1038/s40494-026-02706-1

This project received funding from the European Union's Horizon Europe 2023 research and innovation programme under Marie Sklodowska-Curie grant agreement No. 101149833 for the project Community-driven Digitisation for Heritage at Risk (CORDHISK).
