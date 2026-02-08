# Text2SQL - AI-Powered Natural Language to SQL Converter

An intelligent full-stack application that converts natural language questions into SQL queries using **OpenAI GPT-4o-mini** and **LangGraph** workflow orchestration. Ask questions about your database in plain English and get instant results with AI-generated summaries, visualizations, and follow-up suggestions.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Database Setup](#2-database-setup)
  - [3. Environment Configuration](#3-environment-configuration)
  - [4. Backend Setup](#4-backend-setup)
  - [5. Frontend Setup](#5-frontend-setup)
- [Running the Application](#running-the-application)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [LangGraph Workflow](#langgraph-workflow)
- [Frontend Pages](#frontend-pages)
- [Docker Deployment](#docker-deployment)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Overview

Text2SQL bridges the gap between business users and databases. Instead of writing complex SQL queries, users simply type questions like:

> *"How do historical sales compare to current year sales for the Beverages category?"*

The system then:

1. Loads the database schema metadata
2. Uses an LLM to generate a SQL query from the natural language input
3. Validates the SQL for correctness and safety
4. Executes the query against a PostgreSQL database
5. Summarizes the results in a business-friendly format
6. Suggests relevant follow-up questions
7. Renders data as tables, charts, and exportable formats

---

## Key Features

**AI-Powered Query Generation**
- Converts natural language to schema-aware SQL using OpenAI GPT-4o-mini
- Automatic retry with iterative refinement (up to 3 attempts)
- Handles unanswerable queries gracefully with helpful guidance

**SQL Validation & Safety**
- LLM-based SQL validation against the database schema
- Automatic `LIMIT 1000` enforcement to prevent runaway queries
- Schema qualification (`causal_inference.*`) to prevent cross-schema access

**Rich Results Display**
- Multi-tab results view: Summary, SQL, Chart, and Table
- Auto-generated bar chart visualizations with Recharts
- Business-friendly 4-5 line summaries of query results
- Copy SQL and data export capabilities

**Interactive Chat Interface**
- Ask follow-up questions in a conversational interface
- Context-aware suggested questions based on database schema
- Feedback mechanism (thumbs up/down) for result quality

**Production-Ready Architecture**
- LangGraph-based state machine workflow with parallel node execution
- PostgreSQL connection pooling (1-5 connections)
- Structured logging with Loguru
- Comprehensive error handling with custom exception hierarchy
- Docker multi-stage build for containerized deployment

---

## Architecture

### High-Level Flow

```
User (React Frontend)
    |
    | Natural Language Question
    v
FastAPI Backend (/api/text2sql_lg_code/text2sql)
    |
    v
LangGraph Workflow Orchestrator
    |
    +---> [get_metadata]        Load database schema
    |         |
    |         +---> [get_followup_que]    Generate suggested questions ---> END
    |         |
    |         +---> [generate_sql]        LLM generates SQL
    |                    |
    |                    v
    |              [validate_sql_query]    LLM validates SQL + adds LIMIT
    |                    |
    |                    v
    |              [_check_condition]      Decision logic
    |                /      |        \
    |               /       |         \
    |        valid SQL    invalid    unanswerable
    |        or max       (retry)
    |        retries        |
    |           |           v
    |           |    [generate_sql]  (loop back)
    |           |
    |           v
    |      [execute_sql]          Run query on PostgreSQL
    |         /       \
    |        v         v
    |  [generate_     [generate_
    |   summary]       chart]
    |      |             |
    |      v             v
    |     END           END
    v
Response: { sql_query, data, summary, followup_questions, chart }
```

### Backend Architecture

The backend follows a **service-oriented architecture** with clear separation of concerns:

| Layer | Components | Responsibility |
|-------|-----------|----------------|
| **API** | `view.py`, `router.py` | HTTP endpoints, request/response handling |
| **Service** | `service.py` | Orchestration, business logic |
| **Workflow** | `workflow_orchestrator.py` | LangGraph state machine definition |
| **Components** | `sql_generator.py`, `sql_validator.py`, `sql_executor.py`, `summary_generator.py`, `followup_generator.py` | Individual workflow node implementations |
| **Infrastructure** | `llm_client.py`, `database_client.py`, `metadata_loader.py` | External service integrations |
| **Middleware** | `exception.py` | Global error handling |

### Frontend Architecture

| Layer | Components | Responsibility |
|-------|-----------|----------------|
| **Pages** | `Login.tsx`, `Home.tsx`, `Results.tsx`, `NotFound.tsx` | Route-level views |
| **Services** | `api.ts` | Typed API client with request/response interfaces |
| **Hooks** | `useText2SQL.ts` | TanStack Query integration for server state |
| **Components** | `ui/*` (30+ shadcn/ui components) | Reusable UI primitives |

---

## Tech Stack

### Backend

| Technology | Purpose |
|-----------|---------|
| **Python 3.11+** | Runtime |
| **FastAPI** | Web framework with async support |
| **LangGraph** | Graph-based workflow orchestration |
| **LangChain OpenAI** | LLM integration layer |
| **OpenAI GPT-4o-mini** | SQL generation, validation, and summarization |
| **PostgreSQL** | Data storage and query execution |
| **psycopg2** | PostgreSQL adapter with connection pooling |
| **Pandas** | Result set analysis for summary generation |
| **Pydantic Settings** | Type-safe configuration management |
| **Uvicorn** | ASGI server |
| **Loguru** | Structured logging |

### Frontend

| Technology | Purpose |
|-----------|---------|
| **React 18** | UI framework |
| **TypeScript** | Type-safe development |
| **Vite** | Build tool and dev server |
| **React Router v6** | Client-side routing |
| **TanStack Query** | Server state management and caching |
| **shadcn/ui** | Component library (Radix UI + Tailwind) |
| **Tailwind CSS** | Utility-first styling |
| **Recharts** | Data visualization / charts |
| **React Hook Form + Zod** | Form handling and validation |
| **Lucide React** | Icon library |
| **Sonner** | Toast notifications |

---

## Project Structure

```
text2SQL/
├── src/                                    # Python backend
│   ├── __main__.py                         # Entry point (uvicorn server)
│   ├── settings.py                         # Environment configuration
│   ├── logging.py                          # Logging setup
│   │
│   ├── core/
│   │   ├── application.py                  # FastAPI app factory
│   │   └── lifetime.py                     # Startup/shutdown lifecycle hooks
│   │
│   ├── app/
│   │   ├── api/
│   │   │   ├── router.py                   # Main API router
│   │   │   └── text2sql_lg_code/
│   │   │       └── view.py                 # Text2SQL API endpoints
│   │   │
│   │   └── services/
│   │       └── text2sql_lg_service/
│   │           ├── service.py              # Main Text2SQL service
│   │           ├── workflow_orchestrator.py # LangGraph workflow definition
│   │           ├── models.py               # Pydantic/TypedDict models
│   │           ├── llm_client.py           # OpenAI API client wrapper
│   │           ├── database_client.py      # PostgreSQL connection manager
│   │           ├── metadata_loader.py      # Schema metadata file loader
│   │           ├── sql_generator.py        # LLM-based SQL generation
│   │           ├── sql_validator.py        # LLM-based SQL validation
│   │           ├── sql_executor.py         # Query execution engine
│   │           ├── summary_generator.py    # Result summarization
│   │           ├── followup_generator.py   # Follow-up question generation
│   │           └── exceptions.py           # Custom exception classes
│   │
│   ├── middleware/
│   │   └── exception.py                    # Global exception handler
│   │
│   ├── utils/
│   │   └── logging.py                      # Logging utilities
│   │
│   └── notebook/
│       └── metadata/
│           └── causal_inference_metadata.txt  # Database schema metadata
│
├── frontend/                               # React TypeScript frontend
│   ├── src/
│   │   ├── App.tsx                         # Root component with routing
│   │   ├── main.tsx                        # React entry point
│   │   ├── pages/
│   │   │   ├── Login.tsx                   # Login page (demo auth)
│   │   │   ├── Home.tsx                    # Dashboard with search bar
│   │   │   ├── Results.tsx                 # Query results & chat
│   │   │   └── NotFound.tsx                # 404 page
│   │   ├── services/
│   │   │   └── api.ts                      # Typed API client
│   │   ├── hooks/
│   │   │   └── useText2SQL.ts              # React Query hook
│   │   └── components/
│   │       └── ui/                         # 30+ shadcn/ui components
│   │
│   ├── package.json                        # Node dependencies
│   ├── vite.config.ts                      # Vite + proxy config
│   ├── tailwind.config.ts                  # Tailwind CSS config
│   └── tsconfig.json                       # TypeScript config
│
├── scripts/
│   ├── start.sh                            # Start frontend + backend
│   └── setup.sh                            # Initial setup script
│
├── db_backup/
│   └── causal_inference.zip                # Database backup (required)
│
├── .env.example                            # Environment variable template
├── pyproject.toml                          # Python project & dependencies
├── Dockerfile                              # Multi-stage Docker build
└── README.md
```

---

## Prerequisites

| Requirement | Version | Notes |
|------------|---------|-------|
| **Python** | 3.11+ | Required for backend |
| **Node.js** | 18+ | Required for frontend |
| **npm** | 9+ | Comes with Node.js |
| **PostgreSQL** | 15+ | Database engine |
| **OpenAI API Key** | - | Required for LLM features |
| **Git** | - | For cloning the repository |

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/text2SQL.git
cd text2SQL
```

### 2. Database Setup

The application requires the `causal_inference` schema with 17 pre-populated tables. A database backup is provided.

#### Step 2a: Extract the Backup

```bash
cd db_backup
unzip -q causal_inference.zip -d /tmp/causal_restore
```

On Windows (PowerShell):
```powershell
Expand-Archive -Path .\db_backup\causal_inference.zip -DestinationPath $env:TEMP\causal_restore
```

#### Step 2b: Restore to PostgreSQL

```bash
# Linux / Standard PostgreSQL
pg_restore -h localhost -U <your_username> -d postgres -v /tmp/causal_restore/causal_inference

# macOS with Homebrew (PostgreSQL 17)
/opt/homebrew/opt/postgresql@17/bin/pg_restore -h localhost -U <your_username> -d postgres -v /tmp/causal_restore/causal_inference

# Windows
pg_restore -h localhost -U postgres -d postgres -v %TEMP%\causal_restore\causal_inference
```

> Replace `<your_username>` with your PostgreSQL username. On macOS, this is typically your system username (not `postgres`).

#### Step 2c: Verify the Restore

```bash
psql -h localhost -U <your_username> -d postgres -c "SELECT COUNT(*) FROM causal_inference.historical_sales;"
```

**Expected output:** `70560` rows. The restore creates:
- `causal_inference` schema
- 17 tables with pre-loaded data
- ~70,000 rows in `historical_sales`, ~35,000+ in `sales`

> Warnings about the `treduser` role not existing during restore are harmless and can be ignored.

### 3. Environment Configuration

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```ini
# Application Settings
PORT=8090
ENVIRONMENT=Development
LOG_LEVEL=DEBUG
LOGGING_ENVIRONMENT=dev

# Database Settings
POSTGRES_DB_HOST=localhost
POSTGRES_DB_PORT=5432
POSTGRES_DB_USERNAME=postgres              # Your PostgreSQL username
POSTGRES_DB_PASSWORD=                      # Leave empty if passwordless auth
POSTGRES_DB_NAME=postgres                  # Database name
POSTGRES_DB_SCHEMA=public

# OpenAI Settings (REQUIRED)
OPENAI_API_KEY=your-openai-api-key-here    # Get from https://platform.openai.com/api-keys
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Redis Settings (optional, not currently used)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
```

#### Getting an OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com)
2. Sign in or create an account
3. Navigate to [API Keys](https://platform.openai.com/api-keys)
4. Click **"Create new secret key"**
5. Copy the key and paste it as `OPENAI_API_KEY` in your `.env` file

### 4. Backend Setup

```bash
# Create and activate virtual environment
python -m venv venv

# Activate:
# Linux/macOS:
source venv/bin/activate
# Windows (CMD):
venv\Scripts\activate
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -e .
# or with uv (faster):
uv pip install -e .
```

### 5. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

---

## Running the Application

### Option 1: Start Script (Linux/macOS)

```bash
./scripts/start.sh
```

This starts both servers concurrently:
- **Backend:** http://localhost:8090
- **Frontend:** http://localhost:8080
- **API Docs:** http://localhost:8090/api/docs

Press `Ctrl+C` to stop both servers.

### Option 2: Manual Start (All Platforms)

Open two terminal windows:

**Terminal 1 - Backend:**
```bash
# Activate virtual environment first
python -m src
# Starts on http://localhost:8090
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
# Starts on http://localhost:8080 (proxies /api to backend)
```

### Option 3: Frontend Only (Production Build)

```bash
cd frontend
npm run build    # Outputs to ../static/
cd ..
python -m src    # Serves both API and static frontend
```

### Using the Application

1. Open **http://localhost:8080** in your browser
2. **Login** with any credentials (demo authentication)
3. On the **Home** page, type a question or click a suggested question
4. View results across four tabs:
   - **Summary** - Business-friendly text summary
   - **SQL** - Generated SQL query (with copy button)
   - **Chart** - Auto-generated bar chart visualization
   - **Table** - Full results in a paginated data table
5. Use the **chat interface** to ask follow-up questions
6. Provide **feedback** using thumbs up/down buttons

---

## API Reference

### Health Check

```
GET /api/text2sql_lg_code/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "text2sql_lg_code",
  "version": "1.0",
  "checks": {
    "database": "connected",
    "text2sql_service": "available"
  }
}
```

### Text2SQL Query

```
POST /api/text2sql_lg_code/text2sql
```

**Request Body:**
```json
{
  "input_text": "What are the top 5 performing categories by total sales?",
  "max_iterations": 3,
  "metadata_path": null
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `input_text` | string | Yes | - | Natural language question |
| `max_iterations` | integer | No | 3 | Max SQL generation retry attempts |
| `metadata_path` | string | No | null | Custom metadata file path |

**Response:**
```json
{
  "success": true,
  "sql_query": "SELECT category_name, SUM(transaction_amount) as total_sales FROM causal_inference.sales GROUP BY category_name ORDER BY total_sales DESC LIMIT 5;",
  "data": [
    {"category_name": "Beverages", "total_sales": 125430.50},
    {"category_name": "Dairy and Eggs", "total_sales": 98210.25}
  ],
  "summary": "The top performing categories by total sales are led by Beverages with $125,430 in revenue...",
  "followup_questions": [
    "How do these categories compare to last year?",
    "What are the top products within the Beverages category?",
    "Which stores contribute most to Beverages sales?"
  ],
  "chart": null,
  "metadata": null
}
```

### Interactive API Docs

- **Swagger UI:** http://localhost:8090/api/docs
- **OpenAPI JSON:** http://localhost:8090/api/openapi.json

---

## Database Schema

The application uses the `causal_inference` PostgreSQL schema containing 17 tables designed for retail/CPG sales analytics:

### Core Sales Tables

| Table | Description | Key Columns | Row Count |
|-------|-------------|------------|-----------|
| **sales** | Current year transaction-level sales data | date, item_id, category_name, quantity, transaction_amount, store_id, week_num | ~35,000+ |
| **historical_sales** | Previous year's sales data for YoY comparisons | date, item_id, category_name, quantity, transaction_amount, store_id, week_num | ~70,560 |

### Reference Tables

| Table | Description | Key Columns |
|-------|-------------|------------|
| **store** | Store locations and regions | store_id, region, address, store_code |
| **product** | Product catalog with pricing | item_id, item_name, category, price_per_unit, min_price, max_price, suggested_price |
| **store_footfall** | Daily visitor counts per store | store_id, date, weeknum, footfall |
| **inventory** | Daily inventory levels by item/store | store_id, item_id, on_hand_inventory, max_inventory, date |

### Analytics Tables

| Table | Description | Key Columns |
|-------|-------------|------------|
| **forecast** | Weekly forecasted sales (with/without promotions) | week_num, store_id, item_id, forecast_sales_withoutpromo, forecast_sales_with_promo |
| **margin** | Weekly financial data (sales, COGS, ROI) | week, category, sales, cogs, operating_expense, additional_sales, promobudgetspend |
| **causal_impact** | Driver impact analysis on sales by category | category, feature_name, sales_impact, quantity_impact |
| **feature_importance** | Feature importance scores for sales models | feature_name, importance |
| **syndicated_data** | External market data for benchmarking | item_id, category_name, market_sharely, growthopp, recommendation |

### Promotion Tables

| Table | Description | Key Columns |
|-------|-------------|------------|
| **promotion** | Promotion details and mechanics | promo_id, category_name, promotion_mechanic, promotion_type |
| **historical_promotion_lift** | Past promotion effectiveness data | promo_id, category_name, actual_sales_lift_percent, roi, duration |
| **upcoming_promo** | Planned promotional campaigns | promo_id, promo_name, product_category, discount, start_date, end_date |

### Pricing Tables

| Table | Description | Key Columns |
|-------|-------------|------------|
| **price_recommendation** | Optimal pricing suggestions | item_id, category, current_price, suggested_price |
| **competitor_pricing** | Competitor pricing data | item_id, competitor_name, price_per_unit, start_date, end_date |
| **assortment** | Weekly item availability by store | week_num, store_id, item_id, category_id |

### Product Categories

All tables share a consistent category mapping:

| ID | Category |
|----|----------|
| Cat-01 | Beverages |
| Cat-02 | Dairy and Eggs |
| Cat-03 | Bakery and Bread |
| Cat-04 | Frozen Food |
| Cat-05 | Deli and Prepared Food |
| Cat-06 | Fruits and Vegetables |
| Cat-07 | Pantry |
| Cat-08 | Meat and Seafood |

> **Note:** Dates in the `sales` table are stored as VARCHAR in `MM/DD/YYYY` format and require `TO_DATE()` conversion for date operations. All queries are automatically qualified with the `causal_inference.` schema prefix.

---

## LangGraph Workflow

The backend uses **LangGraph** to orchestrate the text-to-SQL pipeline as a directed acyclic graph (DAG) with conditional edges. This enables parallel execution of independent nodes and automatic retry logic.

### Workflow Nodes

| Node | Function | Description |
|------|----------|-------------|
| `get_metadata` | `MetadataLoader.load_metadata()` | Loads database schema from `causal_inference_metadata.txt` |
| `generate_sql` | `SQLGenerator.generate_sql()` | Sends natural language + schema to GPT-4o-mini to produce SQL |
| `validate_sql_query` | `SQLValidator.validate_sql_query()` | LLM validates SQL syntax, schema compliance, adds LIMIT clause |
| `_check_condition` | Conditional routing | Routes to `execute_sql`, `generate_sql` (retry), or `handle_unanswerable` |
| `execute_sql` | `SQLExecutor.execute_sql()` | Runs the validated query against PostgreSQL |
| `generate_summary` | `SummaryGenerator.generate_summary()` | Creates a 4-5 line business summary using LLM + Pandas analysis |
| `generate_chart` | Placeholder | Reserved for future chart data generation |
| `get_followup_que` | `FollowupQuestionGenerator.generate_followup_questions()` | Generates 3 context-aware follow-up questions |
| `handle_unanswerable` | Fallback handler | Returns helpful message when data doesn't exist in the schema |

### Parallel Execution

After `get_metadata`, two paths execute in parallel:
1. `get_followup_que` -> END (generates suggestions immediately)
2. `generate_sql` -> `validate_sql_query` -> ... (processes the query)

After `execute_sql`, two paths also run in parallel:
1. `generate_summary` -> END
2. `generate_chart` -> END

### Retry Logic

If SQL validation fails, the workflow retries SQL generation up to `max_iterations` (default: 3) times. After exhausting retries, the system proceeds with the best available SQL to avoid infinite loops.

---

## Frontend Pages

### Login Page (`/login`)
- Demo authentication - any credentials are accepted
- Stores authentication state for session management

### Home Page (`/`)
- Central search bar for entering natural language questions
- Pre-populated suggested questions based on the database schema
- Quick-access category badges for common query types

### Results Page (`/results`)
- **Summary Tab:** AI-generated business-friendly text summary
- **SQL Tab:** Generated SQL query with syntax highlighting and copy button
- **Chart Tab:** Auto-generated bar chart using Recharts
- **Table Tab:** Full result set in a paginated, sortable data table
- **Chat Interface:** Ask follow-up questions with conversation history
- **Feedback:** Thumbs up/down for result quality tracking

### 404 Page
- Custom not-found page with navigation back to Home

---

## Docker Deployment

### Build and Run

```bash
# Build the image
docker build -t text2sql .

# Run the container
docker run -p 8000:8000 --env-file .env text2sql
```

### Dockerfile Details

The Dockerfile uses a **multi-stage build**:

1. **Stage 1 (Node 20 Alpine):** Builds the React frontend
   - Installs npm dependencies with `npm ci`
   - Runs `npm run build` to produce optimized static files in `../static/`

2. **Stage 2 (Python 3.14):** Runs the FastAPI backend
   - Installs Python dependencies via Poetry
   - Copies the built frontend static files
   - Creates a non-root `appuser` for security
   - Exposes port 8000
   - Starts the application with `python -m src`

### Docker with External PostgreSQL

```bash
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  -e POSTGRES_DB_HOST=host.docker.internal \
  -e POSTGRES_DB_PORT=5432 \
  -e POSTGRES_DB_USERNAME=postgres \
  -e POSTGRES_DB_NAME=postgres \
  text2sql
```

> Use `host.docker.internal` to connect to PostgreSQL running on the host machine.

---

## Troubleshooting

### Database Issues

| Problem | Solution |
|---------|----------|
| `role 'postgres' does not exist` | Use your system username instead (common on macOS). Update `POSTGRES_DB_USERNAME` in `.env` |
| `causal_inference schema not found` | Restore the database backup - see [Database Setup](#2-database-setup) |
| `relation 'causal_inference.historical_sales' does not exist` | The backup restore may have failed. Check restore output for errors and retry |
| `password authentication failed` | Set the correct password in `POSTGRES_DB_PASSWORD` or leave it empty for passwordless auth |
| `could not connect to server` | Ensure PostgreSQL is running: `pg_isready -h localhost -p 5432` |
| `unsupported version` during restore | Use the PostgreSQL version-matched `pg_restore` binary |

### OpenAI API Issues

| Problem | Solution |
|---------|----------|
| `OPENAI_API_KEY not found` | Ensure it is set in your `.env` file |
| `401 Unauthorized` | Verify your API key is valid at [platform.openai.com](https://platform.openai.com) |
| `429 Rate Limited` | You've exceeded API rate limits. Wait and retry, or upgrade your OpenAI plan |
| `Insufficient quota` | Add billing credits to your OpenAI account |

### Application Issues

| Problem | Solution |
|---------|----------|
| Backend won't start | Check `.env` configuration, ensure all required variables are set |
| Frontend proxy errors | Ensure the backend is running on port 8090 before starting the frontend |
| `Date conversion fails` in SQL | Dates use `MM/DD/YYYY` format - queries should use `TO_DATE(date, 'MM/DD/YYYY')` |
| Query returns empty results | Verify the database has data: `SELECT COUNT(*) FROM causal_inference.sales;` |
| Query timeout | Reduce `max_iterations` or simplify the question |

### Port Conflicts

| Port | Used By | Resolution |
|------|---------|------------|
| 8090 | FastAPI backend | Change `PORT` in `.env` |
| 8080 | Vite dev server | Change in `frontend/vite.config.ts` |
| 5432 | PostgreSQL | Change `POSTGRES_DB_PORT` in `.env` |

---

## Error Handling

The application uses a custom exception hierarchy for precise error reporting:

| Exception | HTTP Status | Description |
|-----------|-------------|-------------|
| `LLMClientException` | 502 | OpenAI API errors (rate limits, auth failures) |
| `DatabaseConnectionException` | 503 | PostgreSQL connection failures |
| `SQLExecutionException` | 400 | Invalid SQL execution errors |
| `SQLValidationException` | 400 | SQL validation failures |
| `MetadataLoadException` | 500 | Schema metadata file loading errors |
| `WorkflowException` | 500 | LangGraph workflow execution errors |

All exceptions are caught by the global exception handler middleware and returned as structured JSON responses with appropriate HTTP status codes.

---

## Example Queries

Here are some sample questions you can ask the application:

**Sales Analysis:**
- "What are my top performing categories?"
- "How did my categories perform last week?"
- "How do historical sales compare to current year sales for the Beverages category?"

**Product Performance:**
- "What are the top performing products in Dairy and Eggs?"
- "What are the worst performing products in Frozen Food?"

**Business Recommendations:**
- "How to improve sales of the Bakery and Bread category?"
- "What would you recommend to improve sales in Meat and Seafood?"

**Pricing & Promotions:**
- "Show me competitor pricing for Beverages products"
- "What promotions have the highest ROI?"
- "What upcoming promotions are planned?"

**Inventory & Operations:**
- "Which items are low on inventory across stores?"
- "What is the store footfall trend over the last 4 weeks?"

---

## License

This project is proprietary. All rights reserved.
