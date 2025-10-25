"""
HMM Trainer for Market Regime Detection
Uses Gaussian HMM to identify Bull/Bear/Sideways regimes
"""

import pickle
from pathlib import Path
from typing import Dict, Optional

import numpy as np

try:
    from hmmlearn import hmm

    HMM_AVAILABLE = True
except ImportError:
    HMM_AVAILABLE = False


class HMMTrainer:
    """Train Gaussian HMM for regime detection"""

    REGIME_NAMES = {
        0: 'Bull Run',
        1: 'Bear Market',
        2: 'Sideways'
    }

    REGIME_COLORS = {
        0: '#26a69a',  # Green
        1: '#ef5350',  # Red
        2: '#ffc107'  # Yellow
    }

    def __init__(self, n_regimes: int = 3, model_dir: str = None):
        """
        Args:
            n_regimes: Number of hidden states (default 3: Bull/Bear/Sideways)
            model_dir: Directory to save trained models
        """
        self.n_regimes = n_regimes
        self.model = None
        self.regime_stats = {}

        if model_dir is None:
            model_dir = Path(__file__).parent / 'models'
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def train(self, features: np.ndarray) -> Dict:
        """
        Train HMM on feature data

        Args:
            features: numpy array of shape (n_samples, n_features)

        Returns:
            Dict with regime statistics
        """
        if not HMM_AVAILABLE:
            return {'error': 'hmmlearn not installed. Run: pip install hmmlearn'}

        try:
            # Train Gaussian HMM
            self.model = hmm.GaussianHMM(
                n_components=self.n_regimes,
                covariance_type='full',
                n_iter=100,
                random_state=42
            )

            self.model.fit(features)

            # Predict regimes for entire sequence
            hidden_states = self.model.predict(features)

            # Calculate regime statistics
            regime_stats = []
            for regime_id in range(self.n_regimes):
                mask = hidden_states == regime_id
                regime_features = features[mask]

                if len(regime_features) > 0:
                    avg_return = float(np.mean(regime_features[:, 0]))
                    avg_volatility = float(np.mean(regime_features[:, 1]))
                    probability = float(np.sum(mask) / len(hidden_states))

                    # Classify regime based on avg return
                    if avg_return > 0.002:
                        name = 'Bull Run'
                        color = '#26a69a'
                    elif avg_return < -0.002:
                        name = 'Bear Market'
                        color = '#ef5350'
                    else:
                        name = 'Sideways'
                        color = '#ffc107'

                    regime_stats.append({
                        'id': regime_id,
                        'name': name,
                        'prob': probability,
                        'color': color,
                        'avg_return': avg_return,
                        'avg_volatility': avg_volatility,
                        'count': int(np.sum(mask))
                    })

            # Sort by probability descending
            regime_stats = sorted(regime_stats, key=lambda x: x['prob'], reverse=True)

            # Reassign IDs based on sorted order
            for i, regime in enumerate(regime_stats):
                regime['id'] = i

            self.regime_stats = {r['id']: r for r in regime_stats}

            # Save model
            self.save()

            return {
                'success': True,
                'regimes': regime_stats,
                'model_score': float(self.model.score(features))
            }

        except Exception as e:
            return {'error': f'Training error: {str(e)}'}

    def predict_regime(self, features: np.ndarray) -> int:
        """
        Predict regime for new data

        Args:
            features: numpy array of recent features

        Returns:
            regime_id
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        return int(self.model.predict(features)[-1])

    def save(self, filename: str = 'hmm_model.pkl'):
        """Save trained model to disk"""
        if self.model is None:
            return

        model_path = self.model_dir / filename
        with open(model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'regime_stats': self.regime_stats,
                'n_regimes': self.n_regimes
            }, f)

    def load(self, filename: str = 'hmm_model.pkl'):
        """Load trained model from disk"""
        model_path = self.model_dir / filename

        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        with open(model_path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.regime_stats = data['regime_stats']
            self.n_regimes = data['n_regimes']

    def get_regime_info(self, regime_id: int) -> Optional[Dict]:
        """Get information about a specific regime"""
        return self.regime_stats.get(regime_id)
