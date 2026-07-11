# Census Analytics Platform Engineering Handbook (V1)

## Purpose

This handbook is the single source of truth for building Version 1 of
the Census Analytics Platform. It explains **what technologies are used,
why they were chosen, what alternatives were considered, how each
component interacts with the others, and the complete request/data
flow**.

------------------------------------------------------------------------

# Table of Contents

1.  Vision & Design Principles
2.  High-Level Architecture
3.  Complete Technology Stack
4.  Why Each Technology Was Chosen
5.  Technologies We Rejected (and Why)
6.  Backend Architecture
7.  Database Architecture
8.  Frontend Architecture
9.  Data Flow
10. Folder Structure
11. API Design Philosophy
12. State Management
13. Mapping & Visualization
14. Performance Strategy
15. Background Processing
16. Caching Strategy
17. Security & RBAC
18. Deployment Architecture
19. Development Workflow
20. Coding Standards
21. Future Extension Points (Non-V2 Specific)

------------------------------------------------------------------------

# 1. Vision & Design Principles

The platform is designed to be:

-   Simple rather than over-engineered.
-   Modular and easy to maintain.
-   Highly interactive.
-   Fast enough for analytical workloads.
-   Easy to extend with additional datasets and metrics.

Every technology in this handbook exists because it solves a specific
engineering problem.

------------------------------------------------------------------------

# 2. High-Level Architecture

    Browser
        │
    React + Vite
        │
    Fetch API
        │
    FastAPI
        │
    Business Services
        │
    SQLAlchemy
        │
    PostgreSQL

Supporting services:

-   Redis (cache)
-   Dramatiq (recommended background jobs; Celery is an enterprise
    alternative)
-   Docker
-   Git

------------------------------------------------------------------------

# 3. Complete Technology Stack

## Core

-   Python
-   FastAPI
-   PostgreSQL
-   SQLAlchemy
-   Alembic
-   Pydantic

## Frontend

-   React
-   Vite
-   React Router
-   TanStack Query
-   Native Fetch API
-   Tailwind CSS
-   shadcn/ui

## Visualization

-   React Simple Maps
-   Recharts
-   d3-scale
-   Mapshaper

## Infrastructure

-   Docker
-   Redis
-   Dramatiq
-   WebSockets
-   Git
-   Swagger/OpenAPI

------------------------------------------------------------------------

# 4. Why Each Technology Was Chosen

## Python

Chosen because it has the strongest ecosystem for data processing,
analytics, ETL, and API development.

## FastAPI

Chosen because it provides high performance, automatic OpenAPI
documentation, type validation, and a clean developer experience.

## PostgreSQL

Chosen because Census data is relational and requires filtering,
aggregation, joins, ranking, and analytical SQL.

## SQLAlchemy

Provides a maintainable ORM while still allowing raw SQL for
performance-critical queries.

## Alembic

Tracks schema evolution safely across environments.

## Pydantic

Validates request and response models automatically.

## React

Provides reusable component architecture for highly interactive
dashboards.

## Vite

Fast development server and optimized builds.

## React Router

Enables route-based navigation (/tab1, /tab1/state/:id, /tab2).

## TanStack Query

Handles server-state caching, loading states, retries, and invalidation.

## Native Fetch API (instead of Axios)

No extra dependency, fully supported in modern browsers, integrates
naturally with TanStack Query, reducing bundle size.

## Tailwind CSS

Rapid utility-first styling.

## shadcn/ui

Adds production-ready, accessible UI components (dialogs, comboboxes,
tables, toasts) without locking the project into a third-party design
system.

## React Simple Maps

Provides everything V1 needs (SVG rendering, zoom, pan, click) without
GIS complexity.

### Why not MapLibre?

MapLibre excels at vector tiles, advanced GIS layers, satellite imagery,
and massive datasets. V1 only needs an interactive India choropleth.
React Simple Maps is simpler and easier to maintain.

## Recharts

React-native charting library suitable for dashboards.

## d3-scale

Only D3's colour scaling utilities are required for choropleth
classification.

## Mapshaper

Offline simplification of official boundary data for faster rendering.

## Redis

Caches frequently requested analytics and national aggregates to reduce
PostgreSQL load and improve response time.

## Dramatiq (recommended) / Celery

Runs long-running jobs (dataset imports, preprocessing, recomputations)
outside the request-response cycle.

### Why Dramatiq over Celery?

Dramatiq is simpler to configure and maintain for medium-sized projects.
Celery has a larger ecosystem and is preferable if the platform grows
into a large distributed system.

## WebSockets

Push upload progress and processing status to the frontend in real time.

## Docker

Creates reproducible development and deployment environments.

## Git

Version control, collaboration, rollback, and branching.

## Swagger/OpenAPI

Automatically generated API documentation and testing interface.

------------------------------------------------------------------------

# 5. Technologies We Rejected

  Technology         Reason
  ------------------ -----------------------------------------------------
  Django             Too heavy for an API-first analytics platform.
  MongoDB            Relational analytics fit PostgreSQL better.
  Create React App   Slower than Vite.
  Axios              Native Fetch API is sufficient with TanStack Query.
  MapLibre (V1)      More complexity than current requirements justify.

------------------------------------------------------------------------

# 6. Backend Architecture

Organize by responsibility:

-   routers/
-   services/
-   models/
-   schemas/
-   db/
-   repositories/
-   workers/

Business logic belongs in services, not routers.

------------------------------------------------------------------------

# 7. Database Architecture

Use a normalized schema:

-   locales
-   measures
-   fact_values
-   state_adjacency

Add indexes for common analytical queries.

------------------------------------------------------------------------

# 8. Frontend Architecture

Component-driven design.

Reusable components include:

-   Map
-   MetricSelector
-   Scorecard
-   StateSelector
-   Charts
-   Toasts

------------------------------------------------------------------------

# 9. Data Flow

User Action → Fetch API → FastAPI Router → Service Layer → SQLAlchemy →
PostgreSQL / Redis → JSON Response → TanStack Query Cache → React UI

------------------------------------------------------------------------

# 10. Folder Structure

    backend/
      routers/
      services/
      repositories/
      workers/
      models/
      schemas/
      db/

    frontend/
      components/
      pages/
      hooks/
      services/
      utils/
      types/

------------------------------------------------------------------------

# 11. API Design Philosophy

Prefer small, reusable endpoints over feature-specific APIs.

------------------------------------------------------------------------

# 12. State Management

-   UI state: React state.
-   Server state: TanStack Query.
-   Avoid global state libraries unless genuinely necessary.

------------------------------------------------------------------------

# 13. Mapping & Visualization

-   Simplified geometry nationally.
-   Full-detail geometry for focused state views.
-   Quantile colour scales.
-   Shared colour utilities.

------------------------------------------------------------------------

# 14. Performance Strategy

-   Redis cache.
-   Simplified GeoJSON.
-   TanStack Query caching.
-   Background processing.
-   Lazy loading.

------------------------------------------------------------------------

# 15. Background Processing

Use Dramatiq workers for:

-   CSV imports
-   Validation
-   Derived metrics
-   Heavy computations

------------------------------------------------------------------------

# 16. Caching Strategy

-   Browser cache
-   TanStack Query cache
-   Redis cache
-   PostgreSQL as source of truth

------------------------------------------------------------------------

# 17. Security & RBAC

Public read-only analytics.

RBAC only protects administrative features (uploads, publishing,
management).

------------------------------------------------------------------------

# 18. Deployment

Docker Compose:

-   frontend
-   backend
-   postgres
-   redis
-   dramatiq worker

------------------------------------------------------------------------

# 19. Development Workflow

Feature branch → Pull Request → Review → Merge → Migration → Deployment

------------------------------------------------------------------------

# 20. Coding Standards

-   Type hints everywhere.
-   Service-oriented backend.
-   Reusable frontend components.
-   Avoid duplicated business logic.

------------------------------------------------------------------------

# 21. Future Extension Points

This architecture intentionally leaves room for:

-   Additional census years.
-   New metrics.
-   New visualizations.
-   Additional administrative datasets.

No redesign should be required for these additions.
