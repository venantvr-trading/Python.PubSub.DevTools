#!/usr/bin/env python3
"""
Scenario Testing Dashboard

Web interface for running and monitoring scenario tests with chaos engineering.

Usage:
    python tools/scenario_testing/serve_testing.py
"""
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from flask import Flask, render_template, request, jsonify

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

# Configure Flask to find templates and static files in parent tools directory
TOOLS_DIR = Path(__file__).parent.parent
app = Flask(__name__,
            template_folder=str(TOOLS_DIR / 'templates'),
            static_folder=str(TOOLS_DIR / 'static'))

# Paths
SCRIPT_DIR = Path(__file__).parent
SCENARIOS_DIR = SCRIPT_DIR / "scenarios"
REPORTS_DIR = SCRIPT_DIR / "reports"

# Ensure directories exist
SCENARIOS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# Common UI colors
GRADIENT_PRIMARY = '#667eea'
GRADIENT_SECONDARY = '#764ba2'

# Global test execution state
test_runs: Dict[str, Dict[str, Any]] = {}
test_runs_lock = threading.Lock()


def load_scenario_metadata(filepath: Path) -> Optional[Dict[str, Any]]:
    """Load metadata from a scenario YAML file"""
    try:
        import yaml

        with open(filepath, 'r') as f:
            scenario = yaml.safe_load(f)

        return {
            'filename': filepath.name,
            'name': scenario.get('name', filepath.stem),
            'description': scenario.get('description', ''),
            'has_chaos': len(scenario.get('chaos', [])) > 0,
            'setup': scenario.get('setup', {})
        }
    except Exception as e:
        print(f"Error loading scenario {filepath}: {e}")
        return None


def load_scenario_content(filename: str) -> Optional[str]:
    """Load raw content of a scenario file"""
    try:
        filepath = SCENARIOS_DIR / filename
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading scenario content {filename}: {e}")
        return None


@app.route('/')
def index():
    """Main page"""
    return render_template('scenario_testing.html')


@app.route('/api/scenarios')
def api_scenarios():
    """List all available scenarios"""
    scenarios = []

    if SCENARIOS_DIR.exists():
        for filepath in SCENARIOS_DIR.glob('*.yaml'):
            metadata = load_scenario_metadata(filepath)
            if metadata:
                scenarios.append(metadata)

    return jsonify(scenarios)


@app.route('/api/scenario/<filename>')
def api_scenario(filename: str):
    """Get scenario details"""
    metadata = load_scenario_metadata(SCENARIOS_DIR / filename)
    if not metadata:
        return jsonify({'error': 'Scenario not found'}), 404

    content = load_scenario_content(filename)
    metadata['content'] = content

    return jsonify(metadata)


@app.route('/api/run', methods=['POST'])
def api_run():
    """Start a test run"""
    global test_runs

    config = request.json
    test_id = datetime.now().strftime('%Y%m%d_%H%M%S')

    with test_runs_lock:
        test_runs[test_id] = {
            'scenario': config['scenario'],
            'verbose': config.get('verbose', False),
            'recording': config.get('recording', True),
            'status': 'running',
            'start_time': datetime.now().isoformat(),
            'log': [
                {'timestamp': datetime.now().strftime('%H:%M:%S'), 'level': 'info', 'message': 'Test execution started'},
                {'timestamp': datetime.now().strftime('%H:%M:%S'), 'level': 'info', 'message': f'Scenario: {config["scenario"]}'},
            ],
            'assertions': [],
            'chaos': {},
            'events_count': 0
        }

    # Start test in background thread
    thread = threading.Thread(target=run_test_thread, args=(test_id,), daemon=True)
    thread.start()

    return jsonify({'test_id': test_id})


def run_test_thread(test_id: str):
    """Background thread to run the test"""
    global test_runs

    try:
        with test_runs_lock:
            test_run = test_runs[test_id]

        # Simulate test execution (in real implementation, would call scenario_runner)
        # For now, just simulate with delays
        time.sleep(1)

        with test_runs_lock:
            test_run['log'].append({
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'level': 'info',
                'message': 'Loading scenario configuration...'
            })

        time.sleep(1)

        with test_runs_lock:
            test_run['log'].append({
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'level': 'info',
                'message': 'Setting up mock exchange...'
            })

        time.sleep(1)

        with test_runs_lock:
            test_run['log'].append({
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'level': 'success',
                'message': 'Test execution completed'
            })

            # Mock results
            test_run['status'] = 'passed'
            test_run['duration_seconds'] = 3.5
            test_run['assertions_passed'] = 5
            test_run['assertions_total'] = 5
            test_run['events_count'] = 127
            test_run['assertions'] = [
                {'name': 'event_count.PositionPurchased.min', 'passed': True, 'message': 'Expected at least 3, got 5'},
                {'name': 'event_count.PositionSold.max', 'passed': True, 'message': 'Expected at most 2, got 1'},
                {'name': 'no_panic_sell', 'passed': True, 'message': 'No panic selling detected during crash'},
                {'name': 'final_capital.min', 'passed': True, 'message': 'Capital above minimum threshold'},
                {'name': 'event_sequence', 'passed': True, 'message': 'Events occurred in correct order'},
            ]
            test_run['chaos'] = {
                'events_delayed': 1,
                'events_dropped': 0,
                'failures_injected': 0,
                'total_delay_ms': 5000
            }

    except Exception as e:
        with test_runs_lock:
            test_run['status'] = 'failed'
            test_run['log'].append({
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'level': 'error',
                'message': f'Test failed: {str(e)}'
            })


@app.route('/api/stop/<test_id>', methods=['POST'])
def api_stop(test_id: str):
    """Stop a running test"""
    global test_runs

    with test_runs_lock:
        if test_id in test_runs:
            test_runs[test_id]['status'] = 'stopped'
            test_runs[test_id]['log'].append({
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'level': 'warning',
                'message': 'Test execution stopped by user'
            })

    return jsonify({'status': 'stopped'})


@app.route('/api/status/<test_id>')
def api_status(test_id: str):
    """Get current test status"""
    global test_runs

    with test_runs_lock:
        if test_id not in test_runs:
            return jsonify({'error': 'Test not found'}), 404

        test_run = test_runs[test_id].copy()

    return jsonify(test_run)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Scenario Testing Dashboard")
    parser.add_argument("--port", type=int, default=5558, help="Port to run server on (default: 5558)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--scenarios-dir", type=str, help="Path to scenarios directory")
    parser.add_argument("--reports-dir", type=str, help="Path to reports directory")
    args = parser.parse_args()

    # Update global directories if provided
    global SCENARIOS_DIR, REPORTS_DIR
    if args.scenarios_dir:
        SCENARIOS_DIR = Path(args.scenarios_dir)
        SCENARIOS_DIR.mkdir(exist_ok=True)
    if args.reports_dir:
        REPORTS_DIR = Path(args.reports_dir)
        REPORTS_DIR.mkdir(exist_ok=True)

    print("=" * 80)
    print("🎯 Scenario Testing Dashboard")
    print("=" * 80)
    print()
    print(f"📁 Scenarios directory: {SCENARIOS_DIR}")
    print(f"📊 Reports directory: {REPORTS_DIR}")
    print()
    print("🌐 Starting web server...")
    print()
    print(f"   📍 Open in browser: http://{args.host}:{args.port}")
    print()
    print("   Press Ctrl+C to stop")
    print("=" * 80)
    print()

    app.run(host=args.host, port=args.port, debug=False, threaded=True)


if __name__ == '__main__':
    main()
