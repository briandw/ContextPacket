# ContextPacket Agent Guide

## Commands
- **Build**: N/A (pure Python package)
- **Test**: `pytest -q` (all tests), `pytest tests/test_specific.py::TestClass::test_method` (single test)
- **Lint**: `ruff check --fix` (fixes auto-fixable issues)
- **Type check**: `mypy .`
- **Format**: `ruff format`
- **Pre-commit**: `pre-commit run --all-files`

## Architecture
- **Main package**: `context_packet/` - LLM pipeline for document summarization
- **Entry point**: `main.py` - Basic hello world (placeholder)
- **Config**: `config.toml` - Document ingestion settings (file extensions, recursion)
- **Dependencies**: Pydantic
- **Purpose**: Offline pipeline that distills mixed-format docs into topic-focused context units
- **Testing:** Tests in `tests/` mirror source structure

## Code Style
- **Python version**: 3.12+
- **Python:** 3.11 syntax, Black formatting (120 char line), pytest for tests
- **Types:** Always use type hints, `Optional[T]` not `T | None`, `Union[A, B]` not `A | B`, define custom types for complex 
- **Classes:** Use Pydantic BaseModel for data structures, avoid tuples with multiple types - create classes instead

- **Type hints**: Required (mypy strict mode)
- **Import style**: Ruff handles import sorting automatically
- **Async**: Uses pytest-asyncio with auto mode
- **Error Handling:**  Follow Pydantic validation patterns. Prefer assert over exceptions, avoid exceptions "at all costs"
- **File Size:** Keep files under 500 lines, refactor if larger