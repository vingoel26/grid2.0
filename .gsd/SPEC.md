# SPEC.md — Project Specification

> **Status**: `FINALIZED`

## Vision
A production-grade, AI-powered traffic violation detection system purpose-built for Bengaluru that processes CCTV feeds, detects 8 violation types, generates tamper-proof evidence packages, and provides a real-time dashboard.

## Goals
1. Process CCTV feeds at 30+ FPS on GPU or 5+ FPS on CPU with adaptive hardware selection.
2. Detect 8 violation types fully automatically using 7 specialist models and multi-model GPU parallelism.
3. Generate tamper-proof evidence packages (annotated image + video clip + SHA-256 hash).
4. Provide a real-time Next.js dashboard with live feeds, officer review queue, and analytics heatmap.
5. Support scalable deployment via Docker Compose + horizontal workers.

## Non-Goals (Out of Scope)
- Hardware deployment and physical camera installation.
- Training models from scratch (using pretrained and lightweight fine-tuned models).
- Complex custom user authentication beyond basic JWT for officers/admins.

## Users
- Bengaluru Traffic Police (BTP) Officers (using the dashboard for reviewing violations and monitoring cameras).
- System Administrators (managing cameras, zones, and system health).

## Constraints
- **Technical constraints**: Must run on diverse hardware (from laptops to T4/A100 GPUs); 5+ FPS on CPU, 30+ FPS on GPU. Dockerized deployment.
- **Timeline constraints**: 7-day execution plan for Flipkart Gridlock 2.0 hackathon Phase 2.
- **Accuracy**: Must achieve high confidence (≥0.90 for auto-enforce) to minimize false positives, utilizing a 3-tier confidence system.

## Success Criteria
- [ ] Pipeline processes images/video successfully (CPU/GPU mode).
- [ ] 8 violation types correctly detected and categorized.
- [ ] Evidence packages generated correctly (images, clips, metadata, hashes).
- [ ] Backend API functions (CRUD, stats, WebSocket).
- [ ] Frontend dashboard displays live feed and data.
- [ ] System runs seamlessly via Docker Compose.
