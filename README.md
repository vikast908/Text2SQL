# Text2SQL LangGraph Codebase

This is a Text2SQL codebase that converts natural language questions into SQL queries using OpenAI and LangGraph.

## Recent Updates

- ✅ **Migrated from Azure OpenAI to OpenAI**: Now uses standard OpenAI API instead of Azure OpenAI
- ✅ **Database Configuration**: Updated to support macOS PostgreSQL setup (uses system username by default)
- ✅ **Password Support**: Made database password optional to support passwordless authentication
- ✅ **Database Schema**: Application uses `causal_inference` schema with 16 tables for sales analytics

## Setup Instructions

### Prerequisites

1. Python 3.8+ with virtual environment
2. OpenAI API account with API access
3. PostgreSQL database (for query execution)
4. Database backup file (`db_backup/causal_inference.zip`) - required for initial setup

### Environment Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add your OpenAI API key:
   ```bash
   # Required OpenAI Settings
   OPENAI_API_KEY=your-openai-api-key-here
   OPENAI_MODEL=gpt-4o
   OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
   ```

### Getting OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com)
2. Sign in or create an account
3. Navigate to [API Keys](https://platform.openai.com/api-keys)
4. Click "Create new secret key"
5. Copy the API key and paste it into your `.env` file as `OPENAI_API_KEY`

### Database Configuration

**Important Notes:**
- On macOS, PostgreSQL often uses your system username as the default superuser (not `postgres`)
- The application expects the `causal_inference` schema in your database
- Password can be empty if your PostgreSQL setup doesn't require one

Update the database settings in `.env`:
```bash
POSTGRES_DB_HOST=localhost
POSTGRES_DB_PORT=5432
POSTGRES_DB_USERNAME=balajiv  # Use your system username on macOS, or 'postgres' if that role exists
POSTGRES_DB_PASSWORD=         # Leave empty if no password is required
POSTGRES_DB_NAME=postgres     # Database name
POSTGRES_DB_SCHEMA=public     # Default schema (app uses causal_inference schema)
```

### Database Setup

**⚠️ IMPORTANT: You must restore the database backup before running the application.**

The application requires the `causal_inference` schema with specific tables and data. The backup file `db_backup/causal_inference.zip` contains all the necessary schema and data.

#### Step 1: Extract the Backup

```bash
cd db_backup
unzip -q causal_inference.zip -d /tmp/causal_restore
```

#### Step 2: Restore to Your PostgreSQL Database

Replace `<your_username>` with your PostgreSQL username (e.g., `balajiv` on macOS, or `postgres` if that role exists):

```bash
# If you have PostgreSQL 16+ installed:
pg_restore -h localhost -U <your_username> -d postgres -v /tmp/causal_restore/causal_inference

# If using PostgreSQL 17 (on macOS with Homebrew):
/opt/homebrew/opt/postgresql@17/bin/pg_restore -h localhost -U <your_username> -d postgres -v /tmp/causal_restore/causal_inference
```

**Example (for user 'balajiv'):**
```bash
/opt/homebrew/opt/postgresql@17/bin/pg_restore -h localhost -U balajiv -d postgres -v /tmp/causal_restore/causal_inference
```

#### Step 3: Verify the Restore

Check that the data was imported successfully:

```bash
psql -h localhost -U <your_username> -d postgres -c "SELECT COUNT(*) FROM causal_inference.historical_sales;"
```

**Expected Result:** You should see a count (e.g., `70560`). The restore should create:
- ✅ Schema: `causal_inference`
- ✅ 16 tables including: `historical_sales`, `sales`, `store`, `product`, etc.
- ✅ Data loaded (e.g., ~70,000 rows in `historical_sales`, ~35,000 rows in `sales`)

**Note:** You may see warnings about the `treduser` role not existing during restore - these are harmless and don't affect functionality. The data will be accessible to your user.

**Troubleshooting Restore:**
- If you get "unsupported version" error: Use PostgreSQL 17's pg_restore (see Step 2)
- If restore fails: Ensure PostgreSQL is running and you have proper permissions
- If tables exist but are empty: The restore may have failed silently - check the restore output for errors

### Running the Application

1. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   # or if using uv:
   uv pip install -r requirements.txt
   ```

3. **Ensure PostgreSQL is running:**
   ```bash
   # Check if PostgreSQL is running
   pg_isready -h localhost -p 5432
   ```

4. **Start the application:**
   ```bash
   ./start.sh
   # or
   python -m src
   ```

The API will be available at `http://localhost:8090`

### Troubleshooting

**Database Connection Issues:**
- If you get "role 'postgres' does not exist": Use your system username instead (e.g., `balajiv` on macOS)
- If you get "missing required database configuration: postgres_password": Leave `POSTGRES_DB_PASSWORD` empty in `.env` if your setup doesn't require a password
- If you get "relation 'causal_inference.historical_sales' does not exist": Restore the database backup (see Database Setup section above)

**OpenAI API Issues:**
- Ensure `OPENAI_API_KEY` is set in your `.env` file
- Verify your API key is valid and has sufficient credits

### API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8090/api/docs`
- OpenAPI JSON: `http://localhost:8090/api/openapi.json`

### API Endpoint

**POST** `/api/text2sql_lg_code/text2sql`

Convert natural language to SQL and execute query.

Request body:
```json
{
  "input_text": "How do historical sales compare to current year sales for the Beverages category?",
  "max_iterations": 3
}
```

Response:
```json
{
  "success": true,
  "sql_query": "SELECT ...",
  "data": [...],
  "summary": "...",
  "followup_questions": [...]
}
```

## Database Schema

The application uses the `causal_inference` schema with the following key tables:

- **historical_sales**: Previous year's sales data for year-over-year comparisons
- **sales**: Current year's transaction-level sales data
- **store**: Store location and information
- **product**: Product details and pricing
- **store_footfall**: Store visitor tracking
- **inventory**: Daily inventory levels
- **forecast**: Forecasted sales data
- And 10+ additional tables for promotions, pricing, margins, etc.

All queries are automatically qualified with the `causal_inference` schema (e.g., `causal_inference.historical_sales`).