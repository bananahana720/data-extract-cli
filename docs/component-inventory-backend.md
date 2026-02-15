# Component Inventory - Backend

The backend part is service/pipeline oriented and does not expose frontend UI components.

## Primary Backend Components

- API routers (`src/data_extract/api/routers/`)
- Runtime and queue (`src/data_extract/api/state.py`, `src/data_extract/runtime/queue.py`)
- Service layer (`src/data_extract/services/`)
- Pipeline stages (`src/data_extract/{extract,normalize,chunk,semantic,output}/`)
- CLI command surfaces (`src/data_extract/cli/`)
