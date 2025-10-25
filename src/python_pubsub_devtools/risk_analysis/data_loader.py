"""
Data Loader for OHLCV CSV files
Validates and extracts features for regime detection
"""

from typing import Dict, List, Optional

import numpy as np
import pandas as pd


class DataLoader:
    """Parse and validate OHLCV CSV data"""

    def __init__(self):
        self.data: Optional[pd.DataFrame] = None
        self.raw_candles: List[Dict] = []

    def parse_csv(self, csv_content: str) -> Dict:
        """
        Parse CSV content with OHLCV data

        Expected format:
        timestamp,open,high,low,close,volume
        2024-01-01 00:00:00,35000,35200,34900,35100,1000

        Returns:
            Dict with stats and parsed data
        """
        try:
            from io import StringIO

            df = pd.read_csv(StringIO(csv_content))

            # Validate columns
            required = ['timestamp', 'open', 'high', 'low', 'close']
            if not all(col in df.columns for col in required):
                return {'error': f'Missing columns. Required: {required}'}

            # Parse timestamps
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Validate OHLC relationships
            invalid = (df['high'] < df['low']) | (df['high'] < df['open']) | (df['high'] < df['close']) | \
                      (df['low'] > df['open']) | (df['low'] > df['close'])

            if invalid.any():
                return {'error': f'Invalid OHLC data at rows: {df[invalid].index.tolist()[:5]}'}

            # Sort by timestamp
            df = df.sort_values('timestamp')

            # Store
            self.data = df
            self.raw_candles = df.to_dict('records')

            # Calculate stats
            stats = {
                'count': len(df),
                'start_date': df['timestamp'].min().isoformat(),
                'end_date': df['timestamp'].max().isoformat(),
                'price_min': float(df['low'].min()),
                'price_max': float(df['high'].max()),
                'price_mean': float(df['close'].mean()),
                'volume_total': float(df['volume'].sum()) if 'volume' in df.columns else 0,
                'preview': df.tail(10).to_dict('records')
            }

            return {'success': True, 'stats': stats}

        except Exception as e:
            return {'error': f'Parse error: {str(e)}'}

    def extract_features(self) -> np.ndarray:
        """
        Extract features for HMM training

        Returns:
            numpy array of shape (n_samples, n_features)
            Features: returns, volatility, volume_change
        """
        if self.data is None:
            raise ValueError("No data loaded. Call parse_csv first.")

        df = self.data.copy()

        # Returns
        df['returns'] = df['close'].pct_change()

        # Volatility (rolling std of returns)
        df['volatility'] = df['returns'].rolling(window=20, min_periods=1).std()

        # Volume change
        if 'volume' in df.columns:
            df['volume_change'] = df['volume'].pct_change()
        else:
            df['volume_change'] = 0

        # Drop NaN
        df = df.dropna()

        # Select features
        features = df[['returns', 'volatility', 'volume_change']].values

        return features

    def get_candles(self, start_idx: int = 0, count: int = None) -> List[Dict]:
        """Get raw candle data as list of dicts"""
        if not self.raw_candles:
            return []

        if count is None:
            return self.raw_candles[start_idx:]
        else:
            return self.raw_candles[start_idx:start_idx + count]
