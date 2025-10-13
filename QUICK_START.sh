#!/bin/bash
#
# Quick Start Script for PubSub Dev Tools
#
# This script installs the library and provides test commands

set -e  # Exit on error

echo "======================================================================"
echo "  PubSub Dev Tools - Quick Start"
echo "======================================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Must be run from Python.PubSub.DevTools directory"
    exit 1
fi

# 1. Install the library
echo "📦 Installing PubSub Dev Tools..."
pip install -e .

if [ $? -eq 0 ]; then
    echo "✅ Library installed successfully!"
else
    echo "❌ Installation failed"
    exit 1
fi

echo ""
echo "======================================================================"
echo "  Installation Complete!"
echo "======================================================================"
echo ""
echo "You can now use the 'pubsub-tools' command:"
echo ""
echo "  pubsub-tools --help"
echo "  pubsub-tools event-flow --config PATH_TO_CONFIG"
echo "  pubsub-tools event-recorder --config PATH_TO_CONFIG"
echo "  pubsub-tools mock-exchange --config PATH_TO_CONFIG"
echo "  pubsub-tools test-scenarios --config PATH_TO_CONFIG"
echo ""
echo "======================================================================"
echo "  Next Steps"
echo "======================================================================"
echo ""
echo "1. Create your configuration file:"
echo "   cp examples/config.example.yaml /path/to/your/project/devtools_config.yaml"
echo ""
echo "2. Edit the configuration to match your project paths"
echo ""
echo "3. Launch a tool:"
echo "   cd /path/to/your/project"
echo "   pubsub-tools event-flow"
echo ""
echo "For Python.PubSub.Risk project:"
echo "   cd ../Python.PubSub.Risk"
echo "   pubsub-tools event-flow --config devtools_config.yaml"
echo ""
echo "Or use the provided launch script:"
echo "   python tools/launch_event_flow.py"
echo ""
echo "======================================================================"
