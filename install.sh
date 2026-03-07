#!/bin/bash

echo "🚀 Setting up Oxia: The Metabolic Digital Twin..."

# Check if .venv exists, if not create it
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
else
    echo "✅ Virtual environment already exists."
fi

# Activate and install requirements
echo "⬇️  Installing dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✨ Setup complete! You can now run the app using ./run.sh"
