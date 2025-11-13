#!/bin/bash
# Simple installation script for Skill Manager using uv

set -e

echo "=== Skill Manager Installation ==="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo ""
    echo "uv installed! Please restart your shell or run:"
    echo "  source \$HOME/.cargo/env"
    echo ""
    echo "Then run this script again: ./install.sh"
    exit 0
fi

echo "✓ uv found: $(uv --version)"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
uv venv
echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install project
echo "Installing Skill Manager..."
uv pip install -e .
echo "✓ Skill Manager installed"
echo ""

# Verify installation
echo "Verifying installation..."
if command -v skill-manager &> /dev/null; then
    echo "✓ skill-manager command available"
    skill-manager --version
else
    echo "✗ Installation verification failed"
    exit 1
fi
echo ""

echo "=== Installation Complete! ==="
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source .venv/bin/activate"
echo ""
echo "2. Install server dependencies:"
echo "   pip install -r server/requirements.txt"
echo ""
echo "3. Set your API key in server/.env:"
echo "   cp server/.env.example server/.env  # if .env.example exists"
echo "   # Then edit server/.env and add: ANTHROPIC_API_KEY='sk-ant-...'"
echo ""
echo "4. Initialize Skill Manager:"
echo "   skill-manager init"
echo "   (Creates skill-manager.config.json in project root)"
echo ""
echo "5. Start the server:"
echo "   python3 -m server.app_messages_api"
echo ""
echo "6. Or use skill-manager:"
echo "   skill-manager --help"
echo ""
