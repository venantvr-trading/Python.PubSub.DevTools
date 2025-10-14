# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2024-10-14

### Added

- **CLI Interface**: New `pubsub-devtools` command-line interface for launching web services
  - `pubsub-devtools event-flow`: Launch Event Flow Visualization service
  - `pubsub-devtools event-recorder`: Launch Event Recorder Dashboard service
  - `pubsub-devtools serve-all`: Launch all services simultaneously
  - `pubsub-devtools config-example`: Display configuration examples

- **Configuration Module**: New `config.py` with configuration dataclasses
  - `EventFlowConfig`: Configuration for Event Flow service
  - `EventRecorderConfig`: Configuration for Event Recorder service
  - `DevToolsConfig`: Main configuration for all services

- **Dark Mode Improvements**: Enhanced dark mode support in Event Flow
  - SVG polygon backgrounds now properly adapt to dark mode (#1a1a1a)
  - SVG text elements are light colored in dark mode for better visibility
  - React Flow nodes dynamically update colors based on theme
  - Background colors properly adjust when toggling dark mode

- **Documentation**:
  - Comprehensive CLI usage guide (`docs/CLI_USAGE.md`)
  - Quick start script with example project (`examples/quick_start.sh`)
  - Updated README with CLI examples and architecture

### Changed

- **Web Assets Organization**: Consolidated templates and static files into `/web/` directory
  - Moved from `/event_flow/web/` and `/event_recorder/web/` to shared `/web/`
  - Both services now use the same template and static asset locations

- **README Updates**: Updated documentation to reflect:
  - New CLI command structure
  - Generic scenario engine instead of domain-specific tools
  - Correct service ports (5555, 5556)
  - Simplified feature descriptions

### Fixed

- Dark mode SVG rendering issues in Event Flow visualization
- Package data paths in `pyproject.toml` to match new web assets location

### Dependencies

- Added: `click>=8.0.0` for CLI functionality

## [0.1.0] - Initial Release

### Added

- Event Flow Visualization
- Event Recorder & Dashboard
- Generic Scenario Testing Framework
- Web-based interfaces for all tools
