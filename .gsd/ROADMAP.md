# ROADMAP.md

> **Current Phase**: Not started
> **Milestone**: v1.0

## Must-Haves (from SPEC)
- [ ] Working detection pipeline on sample data
- [ ] Backend API with DB and Redis
- [ ] Real-time Frontend Dashboard
- [ ] End-to-end Docker Compose setup

## Phases

### Phase 1: Foundation + First Demo
**Status**: ⬜ Not Started
**Objective**: Setup environments, download models/datasets, and verify UVH-26 vehicle detection works on sample data.

### Phase 2: ML Pipeline Core
**Status**: ⬜ Not Started
**Objective**: Develop the 7-stage ML pipeline orchestrator, model wrappers, BoT-SORT tracking, and scene preprocessing.

### Phase 3: Violations + Fine-Tuning
**Status**: ⬜ Not Started
**Objective**: Fine-tune helmet and scene classifiers, write logic for all 8 violations, and implement evidence generation and confidence scoring.

### Phase 4: Backend API
**Status**: ⬜ Not Started
**Objective**: Setup FastAPI, PostgreSQL, Redis, MinIO via Docker Compose, and write the backend schema, API endpoints, and WebSocket.

### Phase 5: Frontend Dashboard
**Status**: ⬜ Not Started
**Objective**: Develop the Next.js dashboard, including live violations feed, review queue, analytics, and evidence viewer.

### Phase 6: Optimization + Docker
**Status**: ⬜ Not Started
**Objective**: Finalize Docker Compose deployment, optimize latency (ONNX/TensorRT), verify performance, and polish UI.

### Phase 7: Demo + Presentation
**Status**: ⬜ Not Started
**Objective**: Record demo, prepare pitch deck, test edge cases, and finalize hackathon deliverables.
