# Census Analytics Platform

This project is a Census 2011 analytics platform for Indian state/UT-level exploration and comparison.

The backend seeds state/UT-level facts by aggregating the primary district-level CSV. Counts are summed; rates are recomputed from summed counts.

Read `AGENTS.md` first before making changes. It lists the non-negotiable architecture and build order.

## Current Project Shape

```text
Census Analytics Platform/
|-- Backend/       Python FastAPI backend
|-- Frontend/      React frontend
|-- Database/      CSV data and SQL schema/migrations
|-- AGENTS.md      Agent/human implementation rules
|-- DATABASE.md    Schema and ETL rules
|-- API.md         Endpoint contracts
`-- ROADMAP.md     Phase-by-phase build order
```

## Current Phase

Phase 0/1 setup is being prepared:

1. Docker Postgres
2. FastAPI health endpoint
3. Vite React skeleton
4. Alembic initial schema
5. Seed script for real Census 2011 district data
