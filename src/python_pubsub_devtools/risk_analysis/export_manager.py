"""
Export Manager for Generated Scenarios
Saves scenarios in replay-compatible JSON format
"""

import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class ExportManager:
    """Export generated scenarios to JSON files"""

    def __init__(self, output_dir: str = None):
        """
        Args:
            output_dir: Directory to save generated scenarios
        """
        if output_dir is None:
            # Default to replay_data/generated
            output_dir = Path(__file__).parent.parent.parent.parent.parent / 'replay_data' / 'generated'

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_scenario(
        self,
        candles: List[Dict],
        filename: str = None,
        metadata: Dict = None
    ) -> Dict:
        """
        Save scenario to JSON file

        Args:
            candles: List of candle dicts
            filename: Output filename (auto-generated if None)
            metadata: Optional metadata to include

        Returns:
            Dict with file path and stats
        """
        if filename is None:
            # Auto-generate filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            counter = 1
            while True:
                filename = f'generated_{timestamp}_{counter:03d}.json'
                filepath = self.output_dir / filename
                if not filepath.exists():
                    break
                counter += 1
        else:
            if not filename.endswith('.json'):
                filename += '.json'
            filepath = self.output_dir / filename

        # Build JSON structure (compatible with replay format)
        data = {
            'candles': candles,
            'metadata': {
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'n_candles': len(candles),
                'start_price': candles[0]['close'] if candles else 0,
                'end_price': candles[-1]['close'] if candles else 0,
                'price_change': ((candles[-1]['close'] - candles[0]['close']) / candles[0]['close'] * 100) if candles else 0,
                **(metadata or {})
            }
        }

        # Save to file
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        return {
            'success': True,
            'filepath': str(filepath),
            'filename': filename,
            'n_candles': len(candles),
            'size_bytes': filepath.stat().st_size
        }

    def save_scenarios_batch(
        self,
        scenarios: List[List[Dict]],
        prefix: str = 'batch',
        metadata: Dict = None
    ) -> List[Dict]:
        """
        Save multiple scenarios at once

        Args:
            scenarios: List of scenarios (each is a list of candles)
            prefix: Filename prefix
            metadata: Shared metadata for all scenarios

        Returns:
            List of save results
        """
        results = []
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')

        for i, candles in enumerate(scenarios):
            filename = f'{prefix}_{timestamp}_{i + 1:04d}.json'

            scenario_metadata = {
                'batch_id': timestamp,
                'scenario_index': i + 1,
                'total_scenarios': len(scenarios),
                **(metadata or {})
            }

            result = self.save_scenario(
                candles=candles,
                filename=filename,
                metadata=scenario_metadata
            )
            results.append(result)

        return results

    def list_generated_scenarios(self) -> List[Dict]:
        """
        List all generated scenario files

        Returns:
            List of dicts with file info
        """
        files = []

        for filepath in sorted(self.output_dir.glob('*.json')):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)

                files.append({
                    'filename': filepath.name,
                    'filepath': str(filepath),
                    'n_candles': len(data.get('candles', [])),
                    'metadata': data.get('metadata', {}),
                    'size_bytes': filepath.stat().st_size,
                    'modified': filepath.stat().st_mtime
                })
            except Exception:
                pass  # Skip invalid files

        return files

    def delete_scenario(self, filename: str) -> Dict:
        """Delete a generated scenario file"""
        filepath = self.output_dir / filename

        if not filepath.exists():
            return {'error': f'File not found: {filename}'}

        try:
            filepath.unlink()
            return {'success': True, 'filename': filename}
        except Exception as e:
            return {'error': f'Delete failed: {str(e)}'}

    def clear_all_generated(self) -> Dict:
        """Delete all generated scenarios"""
        count = 0

        for filepath in self.output_dir.glob('*.json'):
            try:
                filepath.unlink()
                count += 1
            except Exception:
                pass

        return {'success': True, 'deleted': count}
