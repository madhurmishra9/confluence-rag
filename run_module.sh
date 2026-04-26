#!/bin/bash
# SO Intelligence Module Runner
# Convenience script for running SO Intelligence CLI with Python module syntax

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if we're in the right directory
if [ ! -f "$SCRIPT_DIR/so_intelligence/main.py" ]; then
    echo -e "${RED}Error: so_intelligence/main.py not found${NC}"
    echo -e "${YELLOW}Make sure you're running this script from the project root directory${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating one...${NC}"
    python3 -m venv "$SCRIPT_DIR/venv"
fi

# Activate virtual environment
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
elif [ -f "$SCRIPT_DIR/venv/Scripts/activate" ]; then
    source "$SCRIPT_DIR/venv/Scripts/activate"
else
    echo -e "${RED}Error: Could not find virtual environment activation script${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo -e "${YELLOW}Warning: .env file not found. Using environment variables or defaults.${NC}"
    echo -e "${CYAN}Tip: Copy .env.example to .env and fill in your values:${NC}"
    echo "    cp .env.example .env"
fi

# Change to project directory
cd "$SCRIPT_DIR"

# Print header
echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════╗"
echo "║       SO Intelligence Module CLI Runner           ║"
echo "╚═══════════════════════════════════════════════════╝"
echo -e "${NC}"

# Run the SO Intelligence module with passed arguments
python -m so_intelligence "$@"
