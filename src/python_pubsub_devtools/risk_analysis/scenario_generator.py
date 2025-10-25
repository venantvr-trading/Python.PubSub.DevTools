"""
Scenario Generator for Monte Carlo Simulations
Supports two modes:
1. GBM (Geometric Brownian Motion) - Simple, fast
2. GAN - Advanced, realistic patterns
"""

from datetime import datetime, timedelta
from typing import Dict, List

import numpy as np

from .gan_trainer import GANTrainer


class ScenarioGenerator:
    """Generate synthetic market scenarios using GBM or trained GANs"""

    def __init__(self, mode: str = 'gbm'):
        """
        Args:
            mode: 'gbm' for simple generation, 'gan' for GAN-based
        """
        self.mode = mode
        self.gan_models = {}  # regime_id -> GANTrainer

    def load_gan_models(self, regime_ids: List[int], model_dir: str = None):
        """Load trained GAN models for each regime"""
        for regime_id in regime_ids:
            try:
                gan = GANTrainer(regime_id=regime_id, model_dir=model_dir)
                gan.load()
                self.gan_models[regime_id] = gan
            except FileNotFoundError:
                pass  # Model not trained yet

    def generate_gbm_scenario(
            self,
            n_candles: int,
            start_price: float,
            drift: float,
            volatility: float,
            interval_minutes: int = 1
    ) -> List[Dict]:
        """
        Generate scenario using Geometric Brownian Motion

        Args:
            n_candles: Number of candles to generate
            start_price: Starting price
            drift: Expected return per candle (e.g., 0.001 = 0.1%)
            volatility: Volatility per candle (e.g., 0.02 = 2%)
            interval_minutes: Candle interval in minutes

        Returns:
            List of candle dicts
        """
        candles = []
        current_price = start_price
        current_time = datetime.utcnow()

        for i in range(n_candles):
            # Generate OHLC for this candle
            open_price = current_price

            # Random walk with drift
            returns = np.random.normal(drift, volatility)
            close_price = open_price * (1 + returns)

            # High and Low with realistic spread
            intra_volatility = volatility * 0.5
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, intra_volatility)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, intra_volatility)))

            # Ensure OHLC consistency
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)

            # Volume (random but realistic)
            base_volume = 1000 + np.random.exponential(500)
            volume = base_volume * (1 + abs(returns) * 10)  # Higher volume on big moves

            candles.append({
                'timestamp': current_time.isoformat() + 'Z',
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': round(volume, 2)
            })

            current_price = close_price
            current_time += timedelta(minutes=interval_minutes)

        return candles

    def generate_gan_scenario(
            self,
            n_candles: int,
            start_price: float,
            regime_id: int,
            interval_minutes: int = 1
    ) -> List[Dict]:
        """
        Generate scenario using trained GAN

        Args:
            n_candles: Number of candles to generate
            start_price: Starting price
            regime_id: Regime to generate from
            interval_minutes: Candle interval in minutes

        Returns:
            List of candle dicts
        """
        if regime_id not in self.gan_models:
            raise ValueError(f"GAN model for regime {regime_id} not loaded")

        gan = self.gan_models[regime_id]

        # Generate sequences in chunks of 24 candles (GAN window size)
        n_sequences = (n_candles + 23) // 24
        sequences = gan.generate(n_sequences=n_sequences, sequence_length=24, base_price=start_price)

        # Flatten to individual candles
        all_candles = []
        current_time = datetime.utcnow()

        for seq in sequences:
            for ohlc in seq:
                if len(all_candles) >= n_candles:
                    break

                # GAN output is OHLC
                open_price, high_price, low_price, close_price = ohlc

                # Ensure valid OHLC
                high_price = max(high_price, open_price, close_price)
                low_price = min(low_price, open_price, close_price)

                # Generate volume
                volume = 1000 + np.random.exponential(500)

                all_candles.append({
                    'timestamp': current_time.isoformat() + 'Z',
                    'open': round(float(open_price), 2),
                    'high': round(float(high_price), 2),
                    'low': round(float(low_price), 2),
                    'close': round(float(close_price), 2),
                    'volume': round(float(volume), 2)
                })

                current_time += timedelta(minutes=interval_minutes)

            if len(all_candles) >= n_candles:
                break

        return all_candles[:n_candles]

    def generate_scenarios(
            self,
            n_scenarios: int,
            n_candles: int,
            start_price: float,
            regime_params: Dict[int, Dict],
            interval_minutes: int = 1
    ) -> List[List[Dict]]:
        """
        Generate multiple scenarios with regime mixing

        Args:
            n_scenarios: Number of scenarios to generate
            n_candles: Candles per scenario
            start_price: Starting price
            regime_params: Dict of {regime_id: {'drift': float, 'volatility': float, 'prob': float}}
            interval_minutes: Candle interval

        Returns:
            List of scenarios (each scenario is a list of candles)
        """
        scenarios = []

        # Extract regime probabilities
        regime_ids = list(regime_params.keys())
        regime_probs = [regime_params[r]['prob'] for r in regime_ids]

        for _ in range(n_scenarios):
            candles = []
            current_price = start_price
            current_time = datetime.utcnow()
            remaining_candles = n_candles

            while remaining_candles > 0:
                # Choose regime based on probabilities
                regime_id = np.random.choice(regime_ids, p=regime_probs)
                regime = regime_params[regime_id]

                # Generate segment (20-50 candles in this regime)
                segment_length = min(np.random.randint(20, 50), remaining_candles)

                if self.mode == 'gan' and regime_id in self.gan_models:
                    # Use GAN
                    segment = self.generate_gan_scenario(
                        n_candles=segment_length,
                        start_price=current_price,
                        regime_id=regime_id,
                        interval_minutes=interval_minutes
                    )
                else:
                    # Use GBM
                    segment = self.generate_gbm_scenario(
                        n_candles=segment_length,
                        start_price=current_price,
                        drift=regime['drift'],
                        volatility=regime['volatility'],
                        interval_minutes=interval_minutes
                    )

                # Update timestamps to be continuous
                for i, candle in enumerate(segment):
                    candle['timestamp'] = current_time.isoformat() + 'Z'
                    current_time += timedelta(minutes=interval_minutes)

                candles.extend(segment)
                current_price = segment[-1]['close']
                remaining_candles -= segment_length

            scenarios.append(candles)

        return scenarios
