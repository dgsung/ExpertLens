# Milestone M010-0: CLI Scaffold + File Outputs

## Goal

CLI entrypoint 설정, out/reports 디렉토리 구조 생성.

## Completed Tasks

- [x] `python -m expertlens --help` 실행 시 도움말 출력
- [x] `python -m expertlens search "test" --lang ko` 실행 시 `out/session-<uuid>.json` 생성
- [x] `reports/run-<timestamp>.md` 생성
- [x] CLI 에러 핸들링 (잘못된 인자 시 명확한 에러 메시지)

## How to Run / Demo

```bash
# Show help
PYTHONPATH=src python -m expertlens --help

# Run search (creates session JSON + run report)
PYTHONPATH=src python -m expertlens search "배터리 전문가" --lang ko

# List existing sessions
PYTHONPATH=src python -m expertlens list

# Run tests
PYTHONPATH=src pytest tests/test_writer.py -v
```

## Test Results

```
============================= test session starts ==============================
platform linux -- Python 3.12.1, pytest-9.0.2, pluggy-1.6.0
collected 8 items

tests/test_writer.py::TestSessionWriter::test_create_session_skeleton_creates_file PASSED
tests/test_writer.py::TestSessionWriter::test_create_session_skeleton_returns_valid_uuid PASSED
tests/test_writer.py::TestSessionWriter::test_create_session_skeleton_json_structure PASSED
tests/test_writer.py::TestSessionWriter::test_create_session_skeleton_handles_different_languages PASSED
tests/test_writer.py::TestSessionWriter::test_output_dir_created_if_not_exists PASSED
tests/test_writer.py::TestReportWriter::test_create_run_report_creates_file PASSED
tests/test_writer.py::TestReportWriter::test_create_run_report_content PASSED
tests/test_writer.py::TestReportWriter::test_reports_dir_created_if_not_exists PASSED

============================== 8 passed in 0.05s ===============================
```

**Status**: All 8 tests passed.

## Notable Changes

### Files Created

```
src/
└── expertlens/
    ├── __init__.py           # Package init with version
    ├── __main__.py           # CLI entry point (argparse)
    ├── orchestrator.py       # Pipeline orchestrator skeleton
    └── io/
        ├── __init__.py       # I/O module init
        └── writer.py         # SessionWriter + ReportWriter

out/
└── .gitkeep                  # Output directory placeholder

reports/
└── .gitkeep                  # Reports directory placeholder

tests/
├── __init__.py
└── test_writer.py            # Unit tests for writer.py (8 tests)
```

### Key Components

| Component | Description |
|-----------|-------------|
| `__main__.py` | CLI with `search` and `list` commands |
| `orchestrator.py` | Pipeline coordinator (skeleton) |
| `writer.py` | `SessionWriter` (JSON) + `ReportWriter` (MD) |

## Risks / Follow-ups

- 실제 검색/추출 로직 없음 (M010-1에서 mock 구현 예정)
- `PYTHONPATH=src` 필요 (추후 `pyproject.toml` 설정으로 개선 가능)

## Link to tasks.md

[M010-0: CLI Scaffold + File Outputs](../specs/010-expertlens/tasks.md#m010-0-cli-scaffold--file-outputs)
