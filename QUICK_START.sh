#!/bin/bash
#
# Quick Start Script for PubSub DevTools
#
# This script installs the library and sets up the configuration

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                  PubSub DevTools - Quick Start                           ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Must be run from Python.PubSub.DevTools directory"
    exit 1
fi

# 1. Install the library
echo "📦 Installing PubSub DevTools..."
pip install -e .

if [ $? -ne 0 ]; then
    echo "❌ Installation failed"
    exit 1
fi

echo "✅ Library installed successfully!"
echo ""

# 2. Generate configuration file
echo "📝 Generating configuration file..."
if [ -f "devtools_config.yaml" ]; then
    echo "⚠️  devtools_config.yaml already exists, skipping..."
else
    pubsub-tools config-example -o devtools_config.yaml
    echo "✅ Configuration file created: devtools_config.yaml"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                        Installation Complete!                            ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "🎯 Available Commands:"
echo ""
echo "  pubsub-tools --help                    # Show all commands"
echo "  pubsub-tools event-flow                # Launch Event Flow (port 5555)"
echo "  pubsub-tools event-recorder            # Launch Event Recorder (port 5556)"
echo "  pubsub-tools mock-exchange             # Launch Mock Exchange (port 5557)"
echo "  pubsub-tools scenario-testing          # Launch Scenario Testing (port 5558)"
echo "  pubsub-tools serve-all                 # Launch all services"
echo ""
echo "📋 Next Steps:"
echo ""
echo "  1. Edit devtools_config.yaml to configure your project paths:"
echo "     vim devtools_config.yaml"
echo ""
echo "  2. Adjust agents_dir and events_dir to point to your project"
echo ""
echo "  3. Launch a service:"
echo "     pubsub-tools event-flow"
echo ""
echo "  Or launch all services at once:"
echo "     pubsub-tools serve-all"
echo ""
echo "💡 Makefile shortcuts:"
echo ""
echo "  make install-dev          # Install with dev dependencies"
echo "  make run-servers          # Run all services with example config"
echo ""
echo "🔗 For programmatic usage, see: examples/basic_usage.py"
echo ""
echo "╚══════════════════════════════════════════════════════════════════════════╝"
