# Milestone M010-3: Frontend Viewer + Graph UI (Cytoscape.js)

**Status**: DONE
**Completed**: 2026-01-02
**Commit**: 537125c

---

## Goal

정적 HTML viewer로 Graph UI, 리스트/디테일/세션 전환 구현

---

## Deliverables

| File | Description |
|------|-------------|
| `frontend/index.html` | Main HTML page with layout structure |
| `frontend/style.css` | Responsive CSS styling |
| `frontend/app.js` | Application logic (file loading, event handling) |
| `frontend/graph.js` | Cytoscape.js graph module |

---

## How to Run

```bash
# 1. Generate sample session
PYTHONPATH=src python -m expertlens search "배터리 전문가" --lang ko

# 2. Start local server
python -m http.server -d frontend 8080

# 3. Open browser
# http://localhost:8080
# Load session JSON from out/ directory
```

---

## Features Implemented

### Graph UI (Cytoscape.js)

| Feature | Status |
|---------|--------|
| Expert nodes (circle, `#4A90D9`) | Done |
| Node size reflects evidenceCount | Done |
| Company nodes (rectangle, `#7B68EE`) | Done |
| Employment edges with role labels | Done |
| Node click updates Detail Panel | Done |
| Zoom/Pan enabled | Done |
| `cose` layout (force-directed) | Done |

### Detail Panel

| Feature | Status |
|---------|--------|
| Expert name/info display | Done |
| Employment claims list | Done |
| Contact claims list | Done |
| Evidence URL links (new tab) | Done |
| Company info display | Done |
| Connected experts for company | Done |

### Session Management

| Feature | Status |
|---------|--------|
| File input for JSON loading | Done |
| Session info display (expert/evidence count) | Done |
| URL parameter for file path | Skipped (file input sufficient for v1) |

### General

| Feature | Status |
|---------|--------|
| Responsive layout (min-width: 768px) | Done |
| Legend display | Done |
| Error handling for invalid JSON | Done |

---

## Architecture

```
frontend/
├── index.html          # HTML structure
│   ├── Session selector (header)
│   ├── Graph panel (Cytoscape.js container)
│   └── Detail panel (sidebar)
├── style.css           # Responsive styling
├── graph.js            # Cytoscape.js module
│   ├── sessionToElements()    # JSON → Cytoscape elements
│   ├── initGraph()            # Initialize Cytoscape
│   └── loadSessionToGraph()   # Load and layout
└── app.js              # Application controller
    ├── handleFileSelect()     # JSON file loading
    ├── handleNodeClick()      # Node selection
    ├── showExpertDetail()     # Expert panel render
    └── showCompanyDetail()    # Company panel render
```

---

## Node Styling

| Type | Shape | Color | Size |
|------|-------|-------|------|
| Expert | Circle | `#4A90D9` | 30-60px (scales with evidence) |
| Company | Rectangle | `#7B68EE` | 35px fixed |

---

## Done Definition Checklist

**Graph UI (Cytoscape.js)**:
- [x] Expert 노드: 원형, `#4A90D9`, 크기는 evidenceCount에 비례
- [x] Company 노드: 사각형, `#7B68EE`, 고정 크기
- [x] Employment 엣지: Expert ↔ Company 연결
- [x] 노드 클릭 → Detail Panel 업데이트
- [x] Zoom/Pan 활성화
- [x] `cose` 레이아웃 (force-directed)

**Detail Panel**:
- [x] Expert 이름/정보 표시
- [x] Claims 목록 (Employment/Contact)
- [x] Evidence URL 링크 (클릭 시 새 탭)

**Session Management**:
- [x] File input으로 `session-*.json` 로드

**General**:
- [x] `frontend/index.html`을 브라우저에서 열면 UI 표시
- [x] Mobile-friendly 반응형 레이아웃 (min-width: 768px)

---

## Test Results

| Test | Result |
|------|--------|
| File loading | Pass |
| Graph rendering | Pass |
| Node click → Detail update | Pass |
| Employment claims display | Pass |
| Contact claims display | Pass |
| Evidence links | Pass |
| Zoom/Pan | Pass |
| Layout animation | Pass |
| Responsive design | Pass |

---

## Risks / Follow-ups

- CORS issue when opening file directly → Use `python -m http.server`
- Large graphs may have performance issues → Consider pagination in vNext
- No URL parameter support → File input is sufficient for v1

---

## v1 Pilot Complete

With M010-3, the v1 pilot is complete:

| Milestone | Status |
|-----------|--------|
| M010-0: CLI Scaffold | Done |
| M010-1: Mock Search + JSON Schema | Done |
| M010-2: LLM Extraction + Evidence | Done |
| M010-3: Frontend Viewer + Graph | Done |

**v1 delivers**: CLI-based expert discovery with Cytoscape.js graph viewer.
