#!/bin/bash

# Setup script for Text2SQL application
# This script will:
#   1. Install PostgreSQL (if not already installed)
#   2. Extract and restore the database backup
#   3. Generate .env file configuration details

set -e

# Get the directory where the script is located and navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Text2SQL Setup Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     OS_TYPE="linux";;
    Darwin*)    OS_TYPE="macos";;
    *)          OS_TYPE="unknown"
esac

echo -e "${BLUE}Detected OS: ${OS_TYPE}${NC}"
echo ""

# Function to check if PostgreSQL is installed
check_postgres_installed() {
    if command -v psql &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to check if PostgreSQL is running
check_postgres_running() {
    if pg_isready -h localhost -p 5432 &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to install PostgreSQL on macOS
install_postgres_macos() {
    echo -e "${YELLOW}PostgreSQL not found. Installing via Homebrew...${NC}"
    
    if ! command -v brew &> /dev/null; then
        echo -e "${RED}Error: Homebrew is not installed.${NC}"
        echo -e "${YELLOW}Please install Homebrew first:${NC}"
        echo -e "${YELLOW}  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}Installing PostgreSQL...${NC}"
    brew install postgresql@17 || brew install postgresql
    
    echo -e "${YELLOW}Starting PostgreSQL service...${NC}"
    brew services start postgresql@17 || brew services start postgresql
    
    # Wait for PostgreSQL to start
    echo -e "${YELLOW}Waiting for PostgreSQL to start...${NC}"
    sleep 5
    
    # Add PostgreSQL to PATH for this session
    if [ -d "/opt/homebrew/opt/postgresql@17/bin" ]; then
        export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
    elif [ -d "/opt/homebrew/opt/postgresql/bin" ]; then
        export PATH="/opt/homebrew/opt/postgresql/bin:$PATH"
    fi
}

# Function to install PostgreSQL on Linux
install_postgres_linux() {
    echo -e "${YELLOW}PostgreSQL not found. Installing...${NC}"
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y postgresql postgresql-contrib
        sudo systemctl start postgresql
        sudo systemctl enable postgresql
    elif command -v yum &> /dev/null; then
        sudo yum install -y postgresql-server postgresql-contrib
        sudo postgresql-setup --initdb
        sudo systemctl start postgresql
        sudo systemctl enable postgresql
    else
        echo -e "${RED}Error: Could not determine package manager. Please install PostgreSQL manually.${NC}"
        exit 1
    fi
    
    # Wait for PostgreSQL to start
    echo -e "${YELLOW}Waiting for PostgreSQL to start...${NC}"
    sleep 5
}

# Step 1: Install PostgreSQL if needed
echo -e "${BLUE}Step 1: Checking PostgreSQL installation...${NC}"
if ! check_postgres_installed; then
    if [ "$OS_TYPE" = "macos" ]; then
        install_postgres_macos
    elif [ "$OS_TYPE" = "linux" ]; then
        install_postgres_linux
    else
        echo -e "${RED}Error: Unsupported OS. Please install PostgreSQL manually.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}PostgreSQL is already installed${NC}"
    # Try to add PostgreSQL to PATH if on macOS
    if [ "$OS_TYPE" = "macos" ]; then
        if [ -d "/opt/homebrew/opt/postgresql@17/bin" ]; then
            export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
        elif [ -d "/opt/homebrew/opt/postgresql/bin" ]; then
            export PATH="/opt/homebrew/opt/postgresql/bin:$PATH"
        fi
    fi
fi

# Check PostgreSQL version
PG_VERSION=$(psql --version 2>/dev/null | head -n1 || echo "unknown")
echo -e "${GREEN}PostgreSQL version: ${PG_VERSION}${NC}"
echo ""

# Step 2: Check if PostgreSQL is running
echo -e "${BLUE}Step 2: Checking if PostgreSQL is running...${NC}"
if ! check_postgres_running; then
    echo -e "${YELLOW}PostgreSQL is not running. Attempting to start...${NC}"
    if [ "$OS_TYPE" = "macos" ]; then
        brew services start postgresql@17 || brew services start postgresql || {
            echo -e "${RED}Failed to start PostgreSQL. Please start it manually.${NC}"
            exit 1
        }
        sleep 3
    elif [ "$OS_TYPE" = "linux" ]; then
        sudo systemctl start postgresql || {
            echo -e "${RED}Failed to start PostgreSQL. Please start it manually.${NC}"
            exit 1
        }
        sleep 3
    fi
fi

if check_postgres_running; then
    echo -e "${GREEN}PostgreSQL is running${NC}"
else
    echo -e "${RED}Error: PostgreSQL is not running. Please start it manually and run this script again.${NC}"
    exit 1
fi
echo ""

# Step 3: Determine PostgreSQL username
echo -e "${BLUE}Step 3: Determining PostgreSQL username...${NC}"
if [ "$OS_TYPE" = "macos" ]; then
    # On macOS, use system username as default
    PG_USER="${USER:-$(whoami)}"
    echo -e "${YELLOW}On macOS, using system username: ${PG_USER}${NC}"
    
    # Try to connect with system username
    if psql -h localhost -U "$PG_USER" -d postgres -c "SELECT 1;" &> /dev/null; then
        echo -e "${GREEN}Successfully connected with username: ${PG_USER}${NC}"
    else
        # Try 'postgres' user
        if psql -h localhost -U postgres -d postgres -c "SELECT 1;" &> /dev/null; then
            PG_USER="postgres"
            echo -e "${GREEN}Using 'postgres' username${NC}"
        else
            echo -e "${YELLOW}Could not auto-detect username. You may need to set up PostgreSQL user.${NC}"
            echo -e "${YELLOW}Using system username: ${PG_USER}${NC}"
        fi
    fi
else
    # On Linux, try 'postgres' user first
    if psql -h localhost -U postgres -d postgres -c "SELECT 1;" &> /dev/null; then
        PG_USER="postgres"
        echo -e "${GREEN}Using 'postgres' username${NC}"
    else
        PG_USER="${USER:-$(whoami)}"
        echo -e "${YELLOW}Using system username: ${PG_USER}${NC}"
    fi
fi

# Ask for password if needed (optional)
echo ""
read -sp "Enter PostgreSQL password (press Enter if no password required): " PG_PASSWORD
echo ""
echo ""

# Step 4: Extract database backup
echo -e "${BLUE}Step 4: Extracting database backup...${NC}"
BACKUP_FILE="$PROJECT_ROOT/db_backup/causal_inference.zip"
RESTORE_DIR="/tmp/causal_restore_$$"

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found at $BACKUP_FILE${NC}"
    exit 1
fi

# Clean up any existing restore directory
rm -rf "$RESTORE_DIR"
mkdir -p "$RESTORE_DIR"

echo -e "${YELLOW}Extracting backup to $RESTORE_DIR...${NC}"
unzip -q "$BACKUP_FILE" -d "$RESTORE_DIR"

if [ ! -f "$RESTORE_DIR/causal_inference" ]; then
    echo -e "${RED}Error: Backup file does not contain expected 'causal_inference' file${NC}"
    exit 1
fi

echo -e "${GREEN}Backup extracted successfully${NC}"
echo ""

# Step 5: Restore database
echo -e "${BLUE}Step 5: Restoring database...${NC}"

# Find pg_restore command
PG_RESTORE_CMD="pg_restore"
if [ "$OS_TYPE" = "macos" ]; then
    if [ -f "/opt/homebrew/opt/postgresql@17/bin/pg_restore" ]; then
        PG_RESTORE_CMD="/opt/homebrew/opt/postgresql@17/bin/pg_restore"
    elif [ -f "/opt/homebrew/opt/postgresql/bin/pg_restore" ]; then
        PG_RESTORE_CMD="/opt/homebrew/opt/postgresql/bin/pg_restore"
    fi
fi

echo -e "${YELLOW}Restoring database using: $PG_RESTORE_CMD${NC}"

# Set PGPASSWORD if password was provided
if [ -n "$PG_PASSWORD" ]; then
    export PGPASSWORD="$PG_PASSWORD"
fi

# Restore the database
if $PG_RESTORE_CMD -h localhost -U "$PG_USER" -d postgres -v "$RESTORE_DIR/causal_inference" 2>&1 | tee /tmp/pg_restore.log; then
    echo -e "${GREEN}Database restored successfully${NC}"
else
    RESTORE_EXIT_CODE=$?
    echo -e "${YELLOW}Restore completed with exit code: $RESTORE_EXIT_CODE${NC}"
    echo -e "${YELLOW}Note: Some warnings (like missing 'treduser' role) are harmless${NC}"
fi

# Verify restore
echo ""
echo -e "${YELLOW}Verifying database restore...${NC}"
if psql -h localhost -U "$PG_USER" -d postgres -c "SELECT COUNT(*) FROM causal_inference.historical_sales;" &> /dev/null; then
    ROW_COUNT=$(psql -h localhost -U "$PG_USER" -d postgres -t -c "SELECT COUNT(*) FROM causal_inference.historical_sales;" 2>/dev/null | xargs)
    if [ -n "$ROW_COUNT" ] && [ "$ROW_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓ Database restore verified: ${ROW_COUNT} rows in historical_sales table${NC}"
    else
        echo -e "${YELLOW}⚠ Database restored but tables may be empty. Check restore logs.${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Could not verify restore. Please check manually.${NC}"
fi

# Clean up restore directory
rm -rf "$RESTORE_DIR"
echo ""

# Step 6: Generate .env file content
echo -e "${BLUE}Step 6: Generating .env file configuration...${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Copy the following into your .env file:${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "# Database Configuration"
echo "POSTGRES_DB_HOST=localhost"
echo "POSTGRES_DB_PORT=5432"
echo "POSTGRES_DB_USERNAME=$PG_USER"
if [ -n "$PG_PASSWORD" ]; then
    echo "POSTGRES_DB_PASSWORD=$PG_PASSWORD"
else
    echo "POSTGRES_DB_PASSWORD="
fi
echo "POSTGRES_DB_NAME=postgres"
echo "POSTGRES_DB_SCHEMA=causal_inference"
echo ""
echo "# OpenAI Configuration (add your API key)"
echo "OPENAI_API_KEY=your-openai-api-key-here"
echo "OPENAI_MODEL=gpt-4o"
echo "OPENAI_EMBEDDING_MODEL=text-embedding-ada-002"
echo ""
echo "# Application Configuration"
echo "PORT=8090"
echo "ENVIRONMENT=Development"
echo "LOG_LEVEL=DEBUG"
echo ""
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Note: Don't forget to add your OPENAI_API_KEY to the .env file!${NC}"
echo ""
echo -e "${GREEN}Setup completed successfully!${NC}"
echo ""
