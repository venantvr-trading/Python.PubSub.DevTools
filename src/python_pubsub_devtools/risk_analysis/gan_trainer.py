"""
TimeGAN Trainer for Synthetic OHLCV Generation
Simplified TimeGAN architecture for generating realistic candlestick patterns
"""

from pathlib import Path
from typing import Dict

import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class TimeGANGenerator(nn.Module):
    """Generator network for TimeGAN"""

    def __init__(self, latent_dim: int = 64, hidden_dim: int = 128, output_dim: int = 4):
        super().__init__()
        self.lstm = nn.LSTM(latent_dim, hidden_dim, num_layers=2, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, z):
        """
        Args:
            z: noise tensor (batch_size, seq_len, latent_dim)
        Returns:
            Generated OHLC sequences (batch_size, seq_len, 4)
        """
        out, _ = self.lstm(z)
        out = self.fc(out)
        return out


class TimeGANDiscriminator(nn.Module):
    """Discriminator network for TimeGAN"""

    def __init__(self, input_dim: int = 4, hidden_dim: int = 128):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers=2, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        """
        Args:
            x: OHLC sequences (batch_size, seq_len, 4)
        Returns:
            Probability of being real (batch_size, 1)
        """
        out, _ = self.lstm(x)
        out = out[:, -1, :]  # Take last timestep
        out = self.fc(out)
        out = self.sigmoid(out)
        return out


class GANTrainer:
    """Train TimeGAN for regime-specific synthetic data generation"""

    def __init__(self, regime_id: int, model_dir: str = None):
        """
        Args:
            regime_id: ID of the regime to train for
            model_dir: Directory to save trained models
        """
        self.regime_id = regime_id
        self.generator = None
        self.discriminator = None
        self.latent_dim = 64
        self.device = 'cuda' if TORCH_AVAILABLE and torch.cuda.is_available() else 'cpu'

        if model_dir is None:
            model_dir = Path(__file__).parent / 'models'
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def prepare_training_data(self, candles: list, window_size: int = 24) -> np.ndarray:
        """
        Convert candles to training sequences

        Args:
            candles: List of candle dicts
            window_size: Sequence length

        Returns:
            numpy array of normalized OHLC sequences
        """
        ohlc = np.array([[c['open'], c['high'], c['low'], c['close']] for c in candles])

        # Normalize to returns (percentage change)
        sequences = []
        for i in range(len(ohlc) - window_size):
            window = ohlc[i:i + window_size]
            base_price = window[0, 3]  # First close price
            normalized = (window - base_price) / base_price
            sequences.append(normalized)

        return np.array(sequences)

    def train(self, candles: list, epochs: int = 100, batch_size: int = 32) -> Dict:
        """
        Train GAN on regime-specific candle data

        Args:
            candles: List of candle dicts for this regime
            epochs: Number of training epochs
            batch_size: Batch size

        Returns:
            Training statistics
        """
        if not TORCH_AVAILABLE:
            return {'error': 'PyTorch not installed. Run: pip install torch'}

        if len(candles) < 100:
            return {'error': f'Insufficient data. Need at least 100 candles, got {len(candles)}'}

        try:
            # Prepare data
            sequences = self.prepare_training_data(candles)

            if len(sequences) < 10:
                return {'error': 'Insufficient sequences after windowing'}

            # Initialize models
            self.generator = TimeGANGenerator(
                latent_dim=self.latent_dim,
                hidden_dim=128,
                output_dim=4
            ).to(self.device)

            self.discriminator = TimeGANDiscriminator(
                input_dim=4,
                hidden_dim=128
            ).to(self.device)

            # Optimizers
            g_optimizer = optim.Adam(self.generator.parameters(), lr=0.0002)
            d_optimizer = optim.Adam(self.discriminator.parameters(), lr=0.0002)

            criterion = nn.BCELoss()

            # Convert to tensor
            real_data = torch.FloatTensor(sequences).to(self.device)

            # Training loop
            g_losses = []
            d_losses = []

            for epoch in range(epochs):
                # Sample batch
                idx = np.random.choice(len(sequences), min(batch_size, len(sequences)), replace=False)
                real_batch = real_data[idx]

                # Train Discriminator
                d_optimizer.zero_grad()

                # Real data
                real_labels = torch.ones(len(real_batch), 1).to(self.device)
                real_output = self.discriminator(real_batch)
                d_real_loss = criterion(real_output, real_labels)

                # Fake data
                noise = torch.randn(len(real_batch), 24, self.latent_dim).to(self.device)
                fake_data = self.generator(noise)
                fake_labels = torch.zeros(len(real_batch), 1).to(self.device)
                fake_output = self.discriminator(fake_data.detach())
                d_fake_loss = criterion(fake_output, fake_labels)

                d_loss = d_real_loss + d_fake_loss
                d_loss.backward()
                d_optimizer.step()

                # Train Generator
                g_optimizer.zero_grad()

                noise = torch.randn(len(real_batch), 24, self.latent_dim).to(self.device)
                fake_data = self.generator(noise)
                fake_output = self.discriminator(fake_data)
                g_loss = criterion(fake_output, real_labels)

                g_loss.backward()
                g_optimizer.step()

                g_losses.append(g_loss.item())
                d_losses.append(d_loss.item())

            # Save model
            self.save()

            return {
                'success': True,
                'regime_id': self.regime_id,
                'epochs': epochs,
                'final_g_loss': float(np.mean(g_losses[-10:])),
                'final_d_loss': float(np.mean(d_losses[-10:])),
                'training_samples': len(sequences)
            }

        except Exception as e:
            return {'error': f'Training error: {str(e)}'}

    def generate(self, n_sequences: int = 1, sequence_length: int = 24, base_price: float = 35000.0) -> np.ndarray:
        """
        Generate synthetic OHLC sequences

        Args:
            n_sequences: Number of sequences to generate
            sequence_length: Length of each sequence
            base_price: Starting price

        Returns:
            numpy array of shape (n_sequences, sequence_length, 4)
        """
        if self.generator is None:
            raise ValueError("Model not trained. Call train() first.")

        self.generator.eval()

        with torch.no_grad():
            noise = torch.randn(n_sequences, sequence_length, self.latent_dim).to(self.device)
            fake_data = self.generator(noise)
            fake_data = fake_data.cpu().numpy()

        # Denormalize (convert from returns back to prices)
        prices = np.zeros_like(fake_data)
        for i in range(n_sequences):
            prices[i] = (fake_data[i] * base_price) + base_price

        return prices

    def save(self):
        """Save trained models to disk"""
        if self.generator is None or self.discriminator is None:
            return

        model_path = self.model_dir / f'gan_regime_{self.regime_id}.pth'

        torch.save({
            'generator': self.generator.state_dict(),
            'discriminator': self.discriminator.state_dict(),
            'latent_dim': self.latent_dim,
            'device': self.device
        }, model_path)

    def load(self):
        """Load trained models from disk"""
        model_path = self.model_dir / f'gan_regime_{self.regime_id}.pth'

        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        checkpoint = torch.load(model_path, map_location=self.device)

        self.generator = TimeGANGenerator(
            latent_dim=checkpoint['latent_dim'],
            hidden_dim=128,
            output_dim=4
        ).to(self.device)

        self.discriminator = TimeGANDiscriminator(
            input_dim=4,
            hidden_dim=128
        ).to(self.device)

        self.generator.load_state_dict(checkpoint['generator'])
        self.discriminator.load_state_dict(checkpoint['discriminator'])
        self.latent_dim = checkpoint['latent_dim']
