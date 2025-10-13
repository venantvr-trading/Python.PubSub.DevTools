"""
Scenario Testing Dashboard Server

Web interface for running and monitoring scenario tests.
"""
from pathlib import Path

from flask import Flask, render_template, jsonify

from ..config import ScenarioTestingConfig


class ScenarioTestingServer:
    """Flask server for scenario testing dashboard"""

    def __init__(self, config: ScenarioTestingConfig):
        self.config = config
        self.app = self._create_app()

    def _create_app(self) -> Flask:
        package_root = Path(__file__).parent.parent
        app = Flask(__name__,
                    template_folder=str(package_root / 'web' / 'templates'),
                    static_folder=str(package_root / 'web' / 'static'))

        @app.route('/')
        def index():
            return self._index()

        @app.route('/api/scenarios')
        def api_scenarios():
            return jsonify(self._get_scenarios())

        @app.route('/api/reports')
        def api_reports():
            return jsonify(self._get_reports())

        return app

    def _get_scenarios(self):
        """Get list of available scenario files"""
        scenarios = []
        if self.config.scenarios_dir.exists():
            for file in self.config.scenarios_dir.glob('*.yaml'):
                scenarios.append({
                    'name': file.stem,
                    'file': file.name,
                    'path': str(file)
                })
        return scenarios

    def _get_reports(self):
        """Get list of test reports"""
        reports = []
        if self.config.reports_dir.exists():
            for file in self.config.reports_dir.glob('*.html'):
                reports.append({
                    'name': file.stem,
                    'file': file.name,
                    'path': str(file)
                })
        return reports

    def _index(self):
        scenarios = self._get_scenarios()
        reports = self._get_reports()

        return render_template(
            'scenario_testing.html',
            scenarios=scenarios,
            reports=reports,
            total_scenarios=len(scenarios),
            total_reports=len(reports)
        )

    def run(self, host: str = '0.0.0.0', debug: bool = True):
        print("=" * 80)
        print("🧪 Scenario Testing Dashboard")
        print("=" * 80)
        print(f"📁 Scenarios directory: {self.config.scenarios_dir}")
        print(f"📁 Reports directory: {self.config.reports_dir}")
        print(f"   Found {len(list(self.config.scenarios_dir.glob('*.yaml')))} scenarios")
        print(f"   Found {len(list(self.config.reports_dir.glob('*.html')))} reports")
        print()
        print("🌐 Starting web server...")
        print(f"   📍 Open in browser: http://localhost:{self.config.port}")
        print("   Press Ctrl+C to stop")
        print("=" * 80)
        print()

        self.app.run(host=host, port=self.config.port, debug=debug)
        return 0
