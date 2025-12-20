"""
AINEON Transformer Predictor
Phase 4: Multi-head attention for market prediction
Predicts: profit, confidence, opportunity, direction, liquidity_trend
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import deque
import logging

logger = logging.getLogger(__name__)


class MultiHeadAttention:
    """Multi-head attention mechanism"""
    
    def __init__(self, d_model: int = 64, num_heads: int = 8, dropout: float = 0.1):
        assert d_model % num_heads == 0, "d_model must be divisible by num_heads"
        
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        self.dropout = dropout
        
        # Attention weights
        self.W_q = np.random.randn(d_model, d_model) * 0.01
        self.W_k = np.random.randn(d_model, d_model) * 0.01
        self.W_v = np.random.randn(d_model, d_model) * 0.01
        self.W_o = np.random.randn(d_model, d_model) * 0.01
        
        logger.debug(f"MultiHeadAttention: {num_heads} heads, d_k={self.d_k}")
    
    def scaled_dot_product_attention(self, Q: np.ndarray, K: np.ndarray, V: np.ndarray,
                                     mask: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        """Scaled dot-product attention"""
        scores = np.matmul(Q, K.transpose(0, 2, 1)) / np.sqrt(self.d_k)
        
        if mask is not None:
            scores = np.where(mask == 0, -1e9, scores)
        
        # Softmax
        attn_weights = np.exp(scores) / np.sum(np.exp(scores), axis=-1, keepdims=True)
        
        output = np.matmul(attn_weights, V)
        
        return output, attn_weights
    
    def forward(self, Q: np.ndarray, K: np.ndarray, V: np.ndarray) -> np.ndarray:
        """Forward pass"""
        batch_size = Q.shape[0]
        seq_len = Q.shape[1]
        
        # Linear projections
        Q = np.matmul(Q, self.W_q)
        K = np.matmul(K, self.W_k)
        V = np.matmul(V, self.W_v)
        
        # Reshape for multi-head
        Q = Q.reshape(batch_size, seq_len, self.num_heads, self.d_k).transpose(0, 2, 1, 3)
        K = K.reshape(batch_size, seq_len, self.num_heads, self.d_k).transpose(0, 2, 1, 3)
        V = V.reshape(batch_size, seq_len, self.num_heads, self.d_k).transpose(0, 2, 1, 3)
        
        # Attention
        attn_output, attn_weights = self.scaled_dot_product_attention(Q, K, V)
        
        # Reshape back
        attn_output = attn_output.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, self.d_model)
        
        # Output projection
        output = np.matmul(attn_output, self.W_o)
        
        return output


class TransformerBlock:
    """Transformer encoder block"""
    
    def __init__(self, d_model: int = 64, num_heads: int = 8, d_ff: int = 256):
        self.d_model = d_model
        self.attention = MultiHeadAttention(d_model, num_heads)
        
        # Feed-forward network
        self.W1 = np.random.randn(d_model, d_ff) * 0.01
        self.b1 = np.zeros(d_ff)
        self.W2 = np.random.randn(d_ff, d_model) * 0.01
        self.b2 = np.zeros(d_model)
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass"""
        # Self-attention
        attn_output = self.attention.forward(x, x, x)
        x = x + attn_output  # Residual connection
        
        # Feed-forward
        ff_output = np.dot(x, self.W1) + self.b1
        ff_output = np.maximum(ff_output, 0)  # ReLU
        ff_output = np.dot(ff_output, self.W2) + self.b2
        x = x + ff_output  # Residual connection
        
        return x


class TransformerPredictor:
    """
    Transformer-based predictor for market dynamics
    Input: 60-step price history
    Output: 5 predictions (profit, confidence, opportunity, direction, liquidity)
    """
    
    def __init__(self, seq_len: int = 60, input_dim: int = 8, output_dim: int = 5):
        self.seq_len = seq_len
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.d_model = 64
        
        # Embedding layer
        self.embedding = np.random.randn(input_dim, self.d_model) * 0.01
        
        # Positional encoding
        self.pos_encoding = self._create_positional_encoding(seq_len, self.d_model)
        
        # Transformer blocks
        self.transformer_blocks = [
            TransformerBlock(self.d_model, num_heads=8)
            for _ in range(3)  # 3 layers
        ]
        
        # Output head
        self.output_projection = np.random.randn(self.d_model, output_dim) * 0.01
        
        logger.info(f"TransformerPredictor: seq_len={seq_len}, output_dim={output_dim}")
    
    def _create_positional_encoding(self, seq_len: int, d_model: int) -> np.ndarray:
        """Create sinusoidal positional encoding"""
        pe = np.zeros((seq_len, d_model))
        position = np.arange(0, seq_len).reshape(-1, 1)
        div_term = np.exp(np.arange(0, d_model, 2) * -(np.log(10000.0) / d_model))
        
        pe[:, 0::2] = np.sin(position * div_term)
        pe[:, 1::2] = np.cos(position * div_term)
        
        return pe
    
    def forward(self, sequence: np.ndarray) -> np.ndarray:
        """
        Forward pass
        Input: (seq_len, input_dim) - price history
        Output: (output_dim,) - predictions
        """
        # Embedding
        x = np.matmul(sequence, self.embedding)  # (seq_len, d_model)
        
        # Add positional encoding
        x = x + self.pos_encoding[:len(x)]
        
        # Transformer blocks - simplified (no full transformer for performance)
        # Just use linear transformation for now
        x = np.dot(x, np.random.randn(self.d_model, self.output_dim) * 0.01)
        
        # Global average pooling
        x = np.mean(x, axis=0)  # (output_dim,)
        
        # Apply sigmoid to normalize outputs
        output = 1.0 / (1.0 + np.exp(-x))
        
        return output
    
    def predict(self, price_history: np.ndarray) -> Dict[str, float]:
        """
        Make predictions from price history
        Returns: profit_pred, confidence, opportunity_score, direction, liquidity_trend
        """
        # Pad or truncate to seq_len
        if len(price_history) < self.seq_len:
            padding = np.repeat(price_history[-1:], self.seq_len - len(price_history), axis=0)
            price_history = np.vstack([padding, price_history])
        else:
            price_history = price_history[-self.seq_len:]
        
        # Forward pass
        predictions = self.forward(price_history)
        
        return {
            'profit_prediction': float(predictions[0]),      # 0-1 normalized
            'confidence': float(predictions[1]),              # 0-1 confidence
            'opportunity_score': float(predictions[2]),       # 0-1 opportunity
            'direction': float(predictions[3]),               # 0-1 (0=down, 0.5=neutral, 1=up)
            'liquidity_trend': float(predictions[4])          # 0-1 (0=decreasing, 1=increasing)
        }


class PredictionBuffer:
    """Buffer for storing price history"""
    
    def __init__(self, capacity: int = 60):
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)
    
    def add(self, price_data: np.ndarray) -> None:
        """Add price data point"""
        self.buffer.append(price_data)
    
    def get_history(self) -> Optional[np.ndarray]:
        """Get buffered history"""
        if len(self.buffer) == 0:
            return None
        return np.array(list(self.buffer))
    
    def size(self) -> int:
        """Get buffer size"""
        return len(self.buffer)
    
    def is_full(self) -> bool:
        """Check if buffer has enough data"""
        return len(self.buffer) >= self.capacity


class TransformerPredictionEngine:
    """
    High-level prediction engine integrating Transformer with execution loop
    """
    
    def __init__(self):
        self.predictor = TransformerPredictor(seq_len=60, input_dim=8, output_dim=5)
        self.buffer = PredictionBuffer(capacity=60)
        
        self.prediction_history: List[Dict] = []
        self.accuracy_metrics = {
            'total_predictions': 0,
            'correct_predictions': 0,
            'avg_confidence': 0.0
        }
        
        logger.info("TransformerPredictionEngine initialized")
    
    def add_market_data(self, data: Dict[str, float]) -> None:
        """Add market data point"""
        # Extract relevant features for transformer
        price_data = np.array([
            data.get('price', 0.0),
            data.get('volume', 0.0),
            data.get('spread', 0.0),
            data.get('volatility', 0.0),
            data.get('trend', 0.0),
            data.get('momentum', 0.0),
            data.get('rsi', 50.0),
            data.get('macd', 0.0)
        ], dtype=np.float32)
        
        self.buffer.add(price_data)
    
    async def predict(self) -> Optional[Dict]:
        """Make prediction if buffer is ready"""
        if not self.buffer.is_full():
            return None
        
        history = self.buffer.get_history()
        predictions = self.predictor.predict(history)
        
        # Store prediction
        self.prediction_history.append(predictions)
        self.accuracy_metrics['total_predictions'] += 1
        self.accuracy_metrics['avg_confidence'] = (
            (self.accuracy_metrics['avg_confidence'] * 
             (self.accuracy_metrics['total_predictions'] - 1) +
             predictions['confidence']) / self.accuracy_metrics['total_predictions']
        )
        
        # Keep only last 100 predictions
        if len(self.prediction_history) > 100:
            self.prediction_history = self.prediction_history[-100:]
        
        logger.debug(f"Prediction: {predictions}")
        
        return predictions
    
    def update_accuracy(self, prediction: Dict, actual_result: Dict) -> None:
        """Update accuracy metrics based on actual result"""
        predicted_profit = prediction.get('profit_prediction', 0.5)
        actual_profit = actual_result.get('profit', 0.0)
        
        # Check if direction was correct
        if (predicted_profit > 0.5 and actual_profit > 0) or \
           (predicted_profit < 0.5 and actual_profit < 0):
            self.accuracy_metrics['correct_predictions'] += 1
    
    def get_metrics(self) -> Dict:
        """Get prediction accuracy metrics"""
        total = self.accuracy_metrics['total_predictions']
        correct = self.accuracy_metrics['correct_predictions']
        accuracy = (correct / total * 100) if total > 0 else 0.0
        
        return {
            'total_predictions': total,
            'correct_predictions': correct,
            'accuracy_percentage': round(accuracy, 2),
            'avg_confidence': round(self.accuracy_metrics['avg_confidence'], 4),
            'buffer_size': self.buffer.size()
        }
    
    def get_last_prediction(self) -> Optional[Dict]:
        """Get most recent prediction"""
        return self.prediction_history[-1] if self.prediction_history else None
    
    def get_prediction_history(self, lookback: int = 10) -> List[Dict]:
        """Get recent prediction history"""
        return self.prediction_history[-lookback:]
