# Census Analytics Platform --- Technology Stack & Rationale

> **Scope:** This document covers the technology stack for **Version 1**
> of the Census Analytics Platform only. It deliberately excludes future
> AI features such as RAG, MCP, chatbots, or vector databases. Every
> technology listed below has been chosen because it directly solves a
> problem in the current platform.

------------------------------------------------------------------------

# Core Design Philosophy

The stack follows four principles:

1.  **Simplicity over unnecessary complexity.**
2.  **Industry-standard technologies with large ecosystems.**
3.  **Clear separation of responsibilities.**
4.  **Easy to maintain and extend.**

------------------------------------------------------------------------

# Backend

## Python

### Why?

Python is one of the strongest languages for analytics applications.

The project revolves around:

-   Data processing
-   Reading Census datasets
-   Analytics
-   Database interaction
-   API development

Python excels in all of these.

### Purpose

-   Backend language
-   Data preprocessing
-   Import scripts
-   Database seeding
-   Analytics calculations
-   API implementation

------------------------------------------------------------------------

## FastAPI

### Why?

The frontend should never directly access the database.

FastAPI acts as the bridge between the frontend and PostgreSQL.

It offers:

-   Very high performance
-   Automatic API documentation
-   Request validation
-   Type safety
-   Simple development experience

### Purpose

-   REST API
-   JSON responses
-   Backend business logic
-   Validation
-   API documentation through Swagger

------------------------------------------------------------------------

## SQLAlchemy

### Why?

Writing raw SQL everywhere quickly becomes difficult to maintain.

SQLAlchemy provides an ORM (Object Relational Mapper).

Instead of manually writing SQL queries for every operation, we work
with Python models.

### Purpose

-   Database abstraction
-   Query building
-   Model definitions
-   Cleaner backend code

------------------------------------------------------------------------

## Alembic

### Why?

Database schemas evolve over time.

Alembic keeps a complete migration history.

Without it, schema changes become difficult to track across different
development environments.

### Purpose

-   Schema versioning
-   Database migrations
-   Rollback support

------------------------------------------------------------------------

## Pydantic

### Why?

Every API request and response should be validated.

Pydantic ensures data types are correct before data reaches business
logic.

### Purpose

-   Input validation
-   Response validation
-   Serialization
-   Automatic API schema generation

------------------------------------------------------------------------

# Database

## PostgreSQL

### Why?

The Census dataset is highly structured.

Relationships between states, metrics and years are naturally
relational.

PostgreSQL is excellent for:

-   Filtering
-   Aggregation
-   Ranking
-   Window functions
-   Complex analytical SQL

### Purpose

-   Primary relational database
-   Stores Census data
-   Stores uploaded datasets
-   Supports analytical queries

------------------------------------------------------------------------

# Containerization

## Docker

### Why?

Installing PostgreSQL manually creates environment inconsistencies.

Docker guarantees every developer uses the exact same environment.

### Purpose

-   Run PostgreSQL
-   Consistent development environment
-   Easier deployment

------------------------------------------------------------------------

# Frontend

## React

### Why?

The platform is highly interactive.

Users will:

-   Navigate
-   Zoom maps
-   Switch metrics
-   Compare states
-   Interact with charts

React's component model keeps these features modular and reusable.

### Purpose

-   User interface
-   Component architecture
-   State-driven rendering

------------------------------------------------------------------------

## Vite

### Why?

React requires a development and build tool.

Vite is significantly faster than older alternatives.

### Purpose

-   Development server
-   Hot reload
-   Production builds

------------------------------------------------------------------------

## React Router

### Why?

The application contains multiple pages.

Examples:

-   /tab1
-   /tab1/state/:id
-   /tab2

React Router enables seamless navigation without full page reloads.

### Purpose

-   Client-side routing
-   Deep linking
-   Browser history support

------------------------------------------------------------------------

## TanStack Query

### Why?

Server data should be cached intelligently.

Instead of repeatedly requesting identical data, TanStack Query caches
responses.

It also automatically manages:

-   Loading states
-   Error states
-   Refetching
-   Cache invalidation

### Purpose

-   API caching
-   Server state management

------------------------------------------------------------------------

## Fetch API (Replacing Axios)

### Previous Choice

Axios

### Replacement

Native Fetch API

### Why Fetch is Better Here

Modern browsers provide a mature built-in Fetch API.

Since TanStack Query already manages retries, caching and request state,
Axios provides relatively little additional value for this project.

Advantages:

-   No additional dependency
-   Native browser support
-   Smaller bundle size
-   Fully compatible with TanStack Query

### Purpose

-   Communication between React and FastAPI

------------------------------------------------------------------------

# Styling

## Tailwind CSS

### Why?

Utility-first styling enables rapid dashboard development.

It avoids maintaining large CSS files while remaining highly
customizable.

### Purpose

-   Responsive layouts
-   Component styling
-   Utility classes

------------------------------------------------------------------------

## shadcn/ui (Addition)

### Why?

Tailwind only provides styling.

It does not provide production-ready UI components.

The application needs:

-   Comboboxes
-   Dialogs
-   Tables
-   Tooltips
-   Sidebars
-   Dropdowns
-   Toasts

shadcn/ui provides accessible, production-quality components built on
top of Tailwind.

### Why it is Better

Instead of building these components from scratch, we customize
well-tested components.

This significantly reduces development time while keeping complete
control over the source code.

### Purpose

-   UI component library
-   Consistent design system
-   Faster frontend development

------------------------------------------------------------------------

# Data Visualization

## Recharts

### Why?

Tab 2 requires:

-   Radar charts
-   Bar charts
-   Responsive dashboards

Recharts provides React-native chart components without requiring manual
SVG programming.

### Purpose

-   Dashboard visualizations
-   Animated charts
-   Responsive graphs

------------------------------------------------------------------------

## React Simple Maps

### Why?

The platform requires an interactive SVG map of India.

React Simple Maps provides:

-   Geographic rendering
-   Zoom
-   Pan
-   Click interactions

without the complexity of lower-level mapping libraries.

### Purpose

-   India map rendering
-   State interaction
-   Geographic visualization

------------------------------------------------------------------------

## d3-scale

### Why?

Only the color scaling portion of D3 is required.

It converts metric values into choropleth color buckets using quantile
or similar scales.

### Purpose

-   Choropleth color calculations
-   Dynamic legends

------------------------------------------------------------------------

# Data Processing

## Mapshaper

### Why?

Official GIS boundary files are extremely detailed.

Rendering the full geometry for every state slows the application
unnecessarily.

Mapshaper preprocesses the boundaries into:

-   Simplified geometry (national view)
-   Full-detail geometry (focused state view)

### Purpose

-   Boundary simplification
-   Performance optimization

------------------------------------------------------------------------

# Version Control

## Git

### Why?

Every software project requires version control.

Git enables:

-   Branching
-   Collaboration
-   Rollbacks
-   Change history

### Purpose

-   Source code management

------------------------------------------------------------------------

# API Testing

## Swagger (Generated by FastAPI)

### Why?

Every API can be tested independently before frontend integration.

Developers can inspect requests, responses and schemas directly.

### Purpose

-   API documentation
-   API testing

------------------------------------------------------------------------

# Final Technology Stack

  Category              Technology
  --------------------- -------------------
  Language              Python
  Backend Framework     FastAPI
  ORM                   SQLAlchemy
  Validation            Pydantic
  Database              PostgreSQL
  Migrations            Alembic
  Containerization      Docker
  Frontend              React
  Build Tool            Vite
  Routing               React Router
  Server State          TanStack Query
  HTTP Client           Native Fetch API
  Styling               Tailwind CSS
  UI Components         shadcn/ui
  Charts                Recharts
  Maps                  React Simple Maps
  Color Scaling         d3-scale
  Boundary Processing   Mapshaper
  Version Control       Git
  API Testing           Swagger

------------------------------------------------------------------------

# Summary

The selected stack is intentionally conservative and industry-proven.
Every technology has a clearly defined responsibility, minimizes
unnecessary complexity, and supports rapid development while remaining
maintainable. The only recommended change from the original plan is
replacing Axios with the native Fetch API and adding shadcn/ui to
complement Tailwind CSS, resulting in fewer dependencies and faster UI
development without sacrificing flexibility.
