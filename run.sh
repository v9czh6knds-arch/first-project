#!/bin/bash

# MASI Sentiment Dashboard - Quick Start
# Combines dataprofessor/dashboard-kit + streamlit/demo-stockpeers

echo "🚀 Starting MASI Sentiment Dashboard..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p data/historical data/cache data/exports
mkdir -p components utils pages assets

# Check Bloomberg connection
echo "🔌 Testing Bloomberg connection..."
python -c "
import blpapi
try:
    session_options = blpapi.SessionOptions()
    session_options.setServerHost('localhost')
    session_options.setServerPort(8194)
    session = blpapi.Session(session_options)
    if session.start():
        print('✅ Bloomberg connection successful')
        session.stop()
    else:
        print('⚠️  Bloomberg connection failed - using synthetic data')
except Exception as e:
    print(f'⚠️  Bloomberg error: {e} - using synthetic data')
"

# Run the dashboard
echo "🌐 Starting Streamlit dashboard..."
echo "📊 Open http://localhost:8501 in your browser"
echo "👈 Use the sidebar to navigate"

streamlit run Main.py