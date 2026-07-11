# Addendum --- Recommended Supporting Technologies (V1)

This section supplements the original technology stack by explaining
additional technologies that are worth adopting **in Version 1** because
they improve robustness, scalability, and developer experience. These
are not included for AI or MCP support---they provide value even for a
purely analytics-focused platform.

------------------------------------------------------------------------

# Redis

## Recommendation

**Add Redis** alongside PostgreSQL.

## Why?

PostgreSQL is the source of truth, but repeatedly executing identical
analytical queries wastes database resources.

Redis is an **in-memory data store** that acts as a high-speed cache.

Example:

1.  User requests literacy statistics for Maharashtra.
2.  Backend computes the result and stores it in Redis.
3.  Subsequent requests return instantly from Redis instead of querying
    PostgreSQL again.

## Benefits

-   Faster dashboard loading
-   Reduced database load
-   Faster preset queries
-   Faster national average calculations
-   Excellent support for temporary application state

## Purpose

-   Query caching
-   Frequently accessed analytics
-   Temporary application data

------------------------------------------------------------------------

# Background Task Queue

## Recommendation

**Add Celery or Dramatiq**.

### Why?

Some operations should not block the user.

Examples include:

-   Importing large Census CSV files
-   Validating uploaded datasets
-   Computing derived metrics
-   Regenerating rankings

Instead of waiting for the request to finish:

User Upload

↓

Background Worker

↓

Database Update

↓

Frontend Notification

The UI remains responsive.

### Celery vs Dramatiq

**Celery**

Advantages

-   Industry standard
-   Huge ecosystem
-   Excellent documentation

Disadvantages

-   More configuration
-   More moving parts

**Dramatiq**

Advantages

-   Simpler configuration
-   Cleaner API
-   Easier for smaller projects

Recommendation:

If this project remains medium-sized, **Dramatiq** is preferable because
it is easier to maintain. If the project grows into a large distributed
system, Celery has a more mature ecosystem.

## Purpose

-   Background jobs
-   Dataset imports
-   Long-running analytics
-   Scheduled processing

------------------------------------------------------------------------

# WebSockets

## Recommendation

Add FastAPI WebSocket support.

## Why?

Without WebSockets the frontend repeatedly polls the server.

With WebSockets the server pushes updates instantly.

Useful for:

-   Upload progress
-   Dataset processing status
-   Real-time analytics refresh

## Purpose

-   Live progress updates
-   Real-time communication

------------------------------------------------------------------------

# Map Library Choice

## Current Choice

React Simple Maps

## Why keep it?

For Version 1, the platform displays an SVG map of India with:

-   Click interactions
-   Zoom
-   Pan
-   Choropleth colouring

React Simple Maps is lightweight and simple.

## Why not MapLibre yet?

MapLibre GL JS is designed for advanced GIS workloads:

-   Vector tiles
-   Multiple map layers
-   Satellite imagery
-   Millions of features
-   High-performance rendering

Your current application does **not** require these capabilities.

Using MapLibre now would increase complexity without providing
meaningful benefits.

## Recommendation

Keep **React Simple Maps** for Version 1.

Re-evaluate MapLibre only if the platform later expands into a full GIS
application with district-level maps or advanced geospatial layers.

------------------------------------------------------------------------

# Object Storage

## Recommendation

If users upload datasets, store the files in object storage (such as
S3-compatible storage like MinIO) instead of PostgreSQL.

## Why?

Databases should store structured data and metadata---not large binary
files.

This improves maintainability and backup strategies.

## Purpose

-   Uploaded CSV storage
-   GeoJSON storage
-   Large file management

------------------------------------------------------------------------

# Final Updated Recommended Stack

## Core

-   Python
-   FastAPI
-   PostgreSQL
-   SQLAlchemy
-   Alembic
-   Pydantic
-   Docker

## Frontend

-   React
-   Vite
-   React Router
-   TanStack Query
-   Native Fetch API
-   Tailwind CSS
-   shadcn/ui

## Visualization

-   Recharts
-   React Simple Maps
-   d3-scale
-   Mapshaper

## Supporting Infrastructure

-   Redis
-   Dramatiq (or Celery if enterprise-scale requirements emerge)
-   WebSockets
-   Git
-   Swagger
