"""
Phase 3 Module 1: ML Model Trainer
Advanced AI/ML Intelligence Systems - Q-Learning, Actor-Critic, Transformer Ensemble

Implements three complementary ML models:
1. Q-Learning Agent: State/action/reward learning
2. Actor-Critic: Policy gradient optimization
3. Transformer: Temporal pattern recognition

Provides:
- Model training pipeline
- Model persistence (save/load)
- Training metrics tracking
- Ensemble support
- Real-time inference

Target: 88%+ ensemble accuracy with <100ms inference
"""

import os
import json
import pickle
import logging
import asyncio
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import concurrent.futures

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models, optimizers, losses, callbacks
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False

try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class TrainingConfig:
    """Configuration for model training"""
    # Q-Learning
    q_learning_rate: float = 0.01
    q_discount_factor: float = 0.99
    q_exploration_rate: float = 0.1
    q_exploration_decay: float = 0.995
    q_min_exploration: float = 0.01
    
    # Actor-Critic
    actor_learning_rate: float = 0.0001
    critic_learning_rate: float = 0.001
    entropy_coefficient: float = 0.01
    gae_lambda: float = 0.95
    
    # Transformer
    transformer_hidden_dim: int = 256
    transformer_num_heads: int = 8
    transformer_num_layers: int = 3
    transformer_dropout: float = 0.1
    transformer_max_seq_length: int = 60
    
    # Training
    batch_size: int = 32
    epochs: int = 100
    validation_split: float = 0.2
    early_stopping_patience: int = 15
    
    # General
    random_seed: int = 42
    device: str = "cuda" if torch.cuda.is_available() else "cpu" if PYTORCH_AVAILABLE else "cpu"


@dataclass
class ModelMetrics:
    """Metrics for model performance"""
    training_loss: float
    validation_loss: float
    training_accuracy: float
    validation_accuracy: float
    precision: float
    recall: float
    f1_score: float
    epoch: int
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PredictionResult:
    """Result from model prediction"""
    signal: str  # "BUY", "SELL", "HOLD"
    confidence: float  # 0.0 - 1.0
    q_learning_output: Optional[float]
    actor_critic_output: Optional[float]
    transformer_output: Optional[float]
    ensemble_output: float
    timestamp: str
    latency_ms: float


# ============================================================================
# Q-LEARNING AGENT
# ============================================================================

class QLearningAgent:
    """Q-Learning based trading agent
    
    Learns state-action values for optimal trading decisions.
    State: Market conditions, features
    Action: BUY, SELL, HOLD
    Reward: Trade profit/loss
    """
    
    def __init__(self, 
                 state_size: int, 
                 action_size: int = 3,
                 config: Optional[TrainingConfig] = None):
        """Initialize Q-Learning agent
        
        Args:
            state_size: Number of state features
            action_size: Number of possible actions (BUY/SELL/HOLD)
            config: Training configuration
        """
        self.state_size = state_size
        self.action_size = action_size
        self.config = config or TrainingConfig()
        
        # Q-table: state -> action values
        self.q_table = {}
        self.learning_rate = self.config.q_learning_rate
        self.discount_factor = self.config.q_discount_factor
        self.exploration_rate = self.config.q_exploration_rate
        
        self.training_history = []
        
    def get_state_hash(self, state: np.ndarray) -> str:
        """Convert continuous state to discrete hash"""
        # Discretize continuous state into bins
        binned = np.digitize(state, bins=np.linspace(-3, 3, 10))
        return tuple(binned).__str__()
    
    def get_action(self, state: np.ndarray, training: bool = True) -> int:
        """Choose action using epsilon-greedy strategy
        
        Args:
            state: Current state
            training: If True, use exploration; if False, exploit
            
        Returns:
            Action index (0=BUY, 1=SELL, 2=HOLD)
        """
        state_hash = self.get_state_hash(state)
        
        # Exploration vs Exploitation
        if training and np.random.random() < self.exploration_rate:
            return np.random.randint(0, self.action_size)
        
        # Exploit: return best action
        if state_hash not in self.q_table:
            self.q_table[state_hash] = np.zeros(self.action_size)
        
        return np.argmax(self.q_table[state_hash])
    
    def learn(self, state: np.ndarray, action: int, reward: float, 
              next_state: np.ndarray, done: bool):
        """Update Q-values using Q-Learning update rule
        
        Q(s,a) = Q(s,a) + lr * (r + γ*max(Q(s',a')) - Q(s,a))
        """
        state_hash = self.get_state_hash(state)
        next_state_hash = self.get_state_hash(next_state)
        
        # Initialize Q-values if needed
        if state_hash not in self.q_table:
            self.q_table[state_hash] = np.zeros(self.action_size)
        if next_state_hash not in self.q_table:
            self.q_table[next_state_hash] = np.zeros(self.action_size)
        
        # Q-Learning update
        current_q = self.q_table[state_hash][action]
        max_next_q = np.max(self.q_table[next_state_hash]) if not done else 0
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
        
        self.q_table[state_hash][action] = new_q
        
        # Decay exploration rate
        self.exploration_rate = max(
            self.config.q_min_exploration,
            self.exploration_rate * self.config.q_exploration_decay
        )
    
    def predict(self, state: np.ndarray) -> float:
        """Get Q-value prediction for current state"""
        state_hash = self.get_state_hash(state)
        if state_hash not in self.q_table:
            return 0.5
        
        best_action_value = np.max(self.q_table[state_hash])
        # Normalize to 0-1 range
        return (best_action_value + 1) / 2
    
    def save(self, path: str):
        """Save model to disk"""
        with open(path, 'wb') as f:
            pickle.dump(self.q_table, f)
        logger.info(f"Q-Learning model saved to {path}")
    
    def load(self, path: str):
        """Load model from disk"""
        with open(path, 'rb') as f:
            self.q_table = pickle.load(f)
        logger.info(f"Q-Learning model loaded from {path}")


# ============================================================================
# ACTOR-CRITIC NETWORK (PYTORCH)
# ============================================================================

class ActorCriticNetwork(nn.Module):
    """Actor-Critic neural network for policy gradient learning
    
    Actor: Learns policy for action selection
    Critic: Learns value function for advantage estimation
    """
    
    def __init__(self, state_size: int, action_size: int = 3, hidden_dim: int = 128):
        super(ActorCriticNetwork, self).__init__()
        
        self.state_size = state_size
        self.action_size = action_size
        
        # Shared feature extraction
        self.feature_net = nn.Sequential(
            nn.Linear(state_size, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim),
        )
        
        # Actor (policy)
        self.actor = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, action_size),
            nn.Softmax(dim=-1)
        )
        
        # Critic (value function)
        self.critic = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1)
        )
    
    def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass
        
        Returns:
            action_probs: Probability distribution over actions
            value: Estimated state value
        """
        features = self.feature_net(state)
        action_probs = self.actor(features)
        value = self.critic(features)
        return action_probs, value


class ActorCriticAgent:
    """Actor-Critic training agent"""
    
    def __init__(self, state_size: int, action_size: int = 3, 
                 config: Optional[TrainingConfig] = None):
        self.config = config or TrainingConfig()
        self.state_size = state_size
        self.action_size = action_size
        
        if not PYTORCH_AVAILABLE:
            logger.warning("PyTorch not available, Actor-Critic disabled")
            self.network = None
            return
        
        self.device = torch.device(self.config.device)
        self.network = ActorCriticNetwork(state_size, action_size).to(self.device)
        self.optimizer = optim.Adam(
            self.network.parameters(),
            lr=self.config.actor_learning_rate
        )
        self.training_history = []
    
    def train(self, states: np.ndarray, actions: np.ndarray, 
              rewards: np.ndarray, next_states: np.ndarray, dones: np.ndarray):
        """Train actor-critic network"""
        if not PYTORCH_AVAILABLE or self.network is None:
            return
        
        # Convert to tensors
        states_t = torch.FloatTensor(states).to(self.device)
        actions_t = torch.LongTensor(actions).to(self.device)
        rewards_t = torch.FloatTensor(rewards).to(self.device)
        next_states_t = torch.FloatTensor(next_states).to(self.device)
        dones_t = torch.FloatTensor(dones).to(self.device)
        
        # Forward pass
        action_probs, values = self.network(states_t)
        next_action_probs, next_values = self.network(next_states_t)
        
        # Calculate advantages
        advantages = rewards_t + self.config.q_discount_factor * next_values.squeeze() * (1 - dones_t) - values.squeeze()
        
        # Actor loss: negative log probability weighted by advantage
        action_log_probs = torch.log(action_probs.gather(1, actions_t.unsqueeze(1)) + 1e-8)
        actor_loss = -(action_log_probs * advantages.detach()).mean()
        
        # Critic loss: MSE between predicted and actual value
        critic_loss = advantages.pow(2).mean()
        
        # Entropy regularization (encourage exploration)
        entropy = -(action_probs * torch.log(action_probs + 1e-8)).sum(dim=1).mean()
        
        # Total loss
        total_loss = actor_loss + self.config.critic_learning_rate * critic_loss - self.config.entropy_coefficient * entropy
        
        # Backprop
        self.optimizer.zero_grad()
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.network.parameters(), 0.5)
        self.optimizer.step()
        
        return {
            'actor_loss': actor_loss.item(),
            'critic_loss': critic_loss.item(),
            'entropy': entropy.item(),
            'total_loss': total_loss.item()
        }
    
    def predict(self, state: np.ndarray) -> float:
        """Get value prediction for current state"""
        if not PYTORCH_AVAILABLE or self.network is None:
            return 0.5
        
        with torch.no_grad():
            state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            _, value = self.network(state_t)
            # Normalize to 0-1 range
            return (value.item() + 1) / 2
    
    def save(self, path: str):
        """Save model to disk"""
        if self.network is not None:
            torch.save(self.network.state_dict(), path)
            logger.info(f"Actor-Critic model saved to {path}")
    
    def load(self, path: str):
        """Load model from disk"""
        if self.network is not None:
            self.network.load_state_dict(torch.load(path, map_location=self.device))
            logger.info(f"Actor-Critic model loaded from {path}")


# ============================================================================
# TRANSFORMER NETWORK (TENSORFLOW/KERAS)
# ============================================================================

class TransformerBlock(layers.Layer):
    """Transformer encoder block with multi-head attention"""
    
    def __init__(self, embed_dim: int, num_heads: int, ff_dim: int, rate: float = 0.1):
        super(TransformerBlock, self).__init__()
        
        self.att = layers.MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim // num_heads)
        self.ffn = keras.Sequential([
            layers.Dense(ff_dim, activation="relu"),
            layers.Dense(embed_dim),
        ])
        
        self.layernorm1 = layers.LayerNormalization(epsilon=1e-6)
        self.layernorm2 = layers.LayerNormalization(epsilon=1e-6)
        
        self.dropout1 = layers.Dropout(rate)
        self.dropout2 = layers.Dropout(rate)
    
    def call(self, inputs, training):
        # Multi-head attention
        attn_output = self.att(inputs, inputs, training=training)
        attn_output = self.dropout1(attn_output, training=training)
        out1 = self.layernorm1(inputs + attn_output)
        
        # Feed-forward
        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output, training=training)
        out2 = self.layernorm2(out1 + ffn_output)
        
        return out2


class TransformerModel:
    """Transformer-based time series prediction"""
    
    def __init__(self, state_size: int, seq_length: int = 60, 
                 action_size: int = 3, config: Optional[TrainingConfig] = None):
        self.config = config or TrainingConfig()
        self.state_size = state_size
        self.seq_length = seq_length
        self.action_size = action_size
        self.model = None
        
        if TENSORFLOW_AVAILABLE:
            self._build_model()
    
    def _build_model(self):
        """Build transformer model"""
        inputs = keras.Input(shape=(self.seq_length, self.state_size))
        
        # Embedding layer
        x = layers.Dense(self.config.transformer_hidden_dim)(inputs)
        
        # Transformer blocks
        for _ in range(self.config.transformer_num_layers):
            transformer_block = TransformerBlock(
                embed_dim=self.config.transformer_hidden_dim,
                num_heads=self.config.transformer_num_heads,
                ff_dim=self.config.transformer_hidden_dim * 4,
                rate=self.config.transformer_dropout,
            )
            x = transformer_block(x, training=True)
        
        # Global average pooling
        x = layers.GlobalAveragePooling1D(data_format="channels_first")(x)
        
        # Prediction head
        x = layers.Dense(self.config.transformer_hidden_dim // 2, activation="relu")(x)
        x = layers.Dropout(self.config.transformer_dropout)(x)
        outputs = layers.Dense(self.action_size, activation="softmax")(x)
        
        self.model = keras.Model(inputs=inputs, outputs=outputs)
        self.model.compile(
            optimizer=optimizers.Adam(learning_rate=0.001),
            loss="categorical_crossentropy",
            metrics=["accuracy"]
        )
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray, 
              X_val: np.ndarray, y_val: np.ndarray) -> Dict:
        """Train transformer model"""
        if not TENSORFLOW_AVAILABLE or self.model is None:
            return {'loss': 0, 'accuracy': 0}
        
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=self.config.epochs,
            batch_size=self.config.batch_size,
            verbose=0,
            callbacks=[
                callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=self.config.early_stopping_patience,
                    restore_best_weights=True
                )
            ]
        )
        
        return {
            'loss': float(history.history['loss'][-1]),
            'accuracy': float(history.history['accuracy'][-1]),
            'val_loss': float(history.history['val_loss'][-1]),
            'val_accuracy': float(history.history['val_accuracy'][-1]),
        }
    
    def predict(self, state: np.ndarray) -> float:
        """Get prediction for current state"""
        if not TENSORFLOW_AVAILABLE or self.model is None:
            return 0.5
        
        if state.ndim == 2:
            state = np.expand_dims(state, 0)
        
        predictions = self.model.predict(state, verbose=0)
        return float(np.mean(predictions))
    
    def save(self, path: str):
        """Save model to disk"""
        if self.model is not None:
            self.model.save(path)
            logger.info(f"Transformer model saved to {path}")
    
    def load(self, path: str):
        """Load model from disk"""
        if TENSORFLOW_AVAILABLE:
            self.model = keras.models.load_model(path, custom_objects={
                'TransformerBlock': TransformerBlock
            })
            logger.info(f"Transformer model loaded from {path}")


# ============================================================================
# ENSEMBLE TRAINER
# ============================================================================

class MLModelTrainer:
    """Main ML Model Trainer orchestrating all three models"""
    
    def __init__(self, state_size: int, action_size: int = 3,
                 config: Optional[TrainingConfig] = None,
                 model_dir: str = "models"):
        """Initialize trainer with all three models
        
        Args:
            state_size: Number of input features
            action_size: Number of possible actions
            config: Training configuration
            model_dir: Directory to save models
        """
        self.state_size = state_size
        self.action_size = action_size
        self.config = config or TrainingConfig()
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize three models
        self.q_learning = QLearningAgent(state_size, action_size, config)
        self.actor_critic = ActorCriticAgent(state_size, action_size, config)
        self.transformer = TransformerModel(state_size, config.transformer_max_seq_length, action_size, config)
        
        # Model weights for ensemble
        self.q_learning_weight = 0.6  # Conservative (proven)
        self.actor_critic_weight = 0.25  # Optimized
        self.transformer_weight = 0.15  # Temporal patterns
        
        self.metrics_history = []
        
        logger.info(f"ML Model Trainer initialized: {state_size} features, {action_size} actions")
    
    def train(self, states: np.ndarray, actions: np.ndarray,
              rewards: np.ndarray, next_states: np.ndarray,
              dones: np.ndarray, X_transformer: Optional[np.ndarray] = None,
              y_transformer: Optional[np.ndarray] = None) -> Dict:
        """Train all three models
        
        Args:
            states: State observations
            actions: Actions taken
            rewards: Rewards received
            next_states: Next state observations
            dones: Done flags
            X_transformer: Sequences for transformer (optional)
            y_transformer: Labels for transformer (optional)
            
        Returns:
            Training metrics
        """
        results = {'timestamp': datetime.now().isoformat()}
        
        # Train Q-Learning
        logger.info("Training Q-Learning agent...")
        for i in range(len(states)):
            self.q_learning.learn(states[i], actions[i], rewards[i], next_states[i], dones[i])
        results['q_learning'] = {'status': 'trained'}
        
        # Train Actor-Critic
        if PYTORCH_AVAILABLE:
            logger.info("Training Actor-Critic network...")
            try:
                loss_info = self.actor_critic.train(states, actions, rewards, next_states, dones)
                results['actor_critic'] = loss_info or {'status': 'trained'}
            except Exception as e:
                logger.error(f"Actor-Critic training failed: {e}")
                results['actor_critic'] = {'error': str(e)}
        else:
            results['actor_critic'] = {'status': 'skipped', 'reason': 'PyTorch not available'}
        
        # Train Transformer
        if TENSORFLOW_AVAILABLE and X_transformer is not None and y_transformer is not None:
            logger.info("Training Transformer network...")
            try:
                val_split = int(len(X_transformer) * self.config.validation_split)
                X_val = X_transformer[:val_split]
                y_val = y_transformer[:val_split]
                X_train = X_transformer[val_split:]
                y_train = y_transformer[val_split:]
                
                loss_info = self.transformer.train(X_train, y_train, X_val, y_val)
                results['transformer'] = loss_info
            except Exception as e:
                logger.error(f"Transformer training failed: {e}")
                results['transformer'] = {'error': str(e)}
        else:
            results['transformer'] = {'status': 'skipped', 'reason': 'TensorFlow or data not available'}
        
        self.metrics_history.append(results)
        return results
    
    def predict(self, state: np.ndarray, state_sequence: Optional[np.ndarray] = None) -> PredictionResult:
        """Make ensemble prediction
        
        Args:
            state: Current state
            state_sequence: Optional sequence for transformer
            
        Returns:
            Ensemble prediction with individual model outputs
        """
        start_time = datetime.now()
        
        # Get predictions from each model
        q_learning_pred = self.q_learning.predict(state)
        actor_critic_pred = self.actor_critic.predict(state)
        
        transformer_pred = 0.5
        if state_sequence is not None:
            transformer_pred = self.transformer.predict(state_sequence)
        
        # Weighted ensemble
        ensemble_score = (
            self.q_learning_weight * q_learning_pred +
            self.actor_critic_weight * actor_critic_pred +
            self.transformer_weight * transformer_pred
        )
        
        # Convert to trading signal
        if ensemble_score > 0.65:
            signal = "BUY"
            confidence = ensemble_score
        elif ensemble_score < 0.35:
            signal = "SELL"
            confidence = 1 - ensemble_score
        else:
            signal = "HOLD"
            confidence = 0.5
        
        # Calculate latency
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return PredictionResult(
            signal=signal,
            confidence=confidence,
            q_learning_output=q_learning_pred,
            actor_critic_output=actor_critic_pred,
            transformer_output=transformer_pred,
            ensemble_output=ensemble_score,
            timestamp=datetime.now().isoformat(),
            latency_ms=latency_ms
        )
    
    def save_all_models(self, prefix: str = ""):
        """Save all three models"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_prefix = f"{prefix}_{timestamp}" if prefix else timestamp
        
        # Save Q-Learning
        ql_path = self.model_dir / f"q_learning_{save_prefix}.pkl"
        self.q_learning.save(str(ql_path))
        
        # Save Actor-Critic
        if PYTORCH_AVAILABLE:
            ac_path = self.model_dir / f"actor_critic_{save_prefix}.pt"
            self.actor_critic.save(str(ac_path))
        
        # Save Transformer
        if TENSORFLOW_AVAILABLE:
            tf_path = self.model_dir / f"transformer_{save_prefix}"
            self.transformer.save(str(tf_path))
        
        logger.info(f"All models saved with prefix: {save_prefix}")
        return save_prefix
    
    def load_all_models(self, prefix: str):
        """Load all three models"""
        # Load Q-Learning
        ql_path = self.model_dir / f"q_learning_{prefix}.pkl"
        if ql_path.exists():
            self.q_learning.load(str(ql_path))
        
        # Load Actor-Critic
        if PYTORCH_AVAILABLE:
            ac_path = self.model_dir / f"actor_critic_{prefix}.pt"
            if ac_path.exists():
                self.actor_critic.load(str(ac_path))
        
        # Load Transformer
        if TENSORFLOW_AVAILABLE:
            tf_path = self.model_dir / f"transformer_{prefix}"
            if tf_path.exists():
                self.transformer.load(str(tf_path))
        
        logger.info(f"All models loaded with prefix: {prefix}")
    
    def get_training_report(self) -> Dict:
        """Get comprehensive training report"""
        return {
            'total_training_runs': len(self.metrics_history),
            'latest_metrics': self.metrics_history[-1] if self.metrics_history else None,
            'model_weights': {
                'q_learning': self.q_learning_weight,
                'actor_critic': self.actor_critic_weight,
                'transformer': self.transformer_weight,
            },
            'config': asdict(self.config),
        }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def main():
    """Demo/test execution"""
    logging.basicConfig(level=logging.INFO)
    
    # Initialize trainer
    trainer = MLModelTrainer(state_size=200, action_size=3)
    
    # Generate synthetic training data
    n_samples = 1000
    states = np.random.randn(n_samples, 200)
    actions = np.random.randint(0, 3, n_samples)
    rewards = np.random.randn(n_samples)
    next_states = np.random.randn(n_samples, 200)
    dones = np.random.rand(n_samples) > 0.9
    
    # Synthetic transformer data
    X_transformer = np.random.randn(n_samples, 60, 200)
    y_transformer = keras.utils.to_categorical(actions, 3) if TENSORFLOW_AVAILABLE else None
    
    # Train
    logger.info("Starting model training...")
    results = trainer.train(states, actions, rewards, next_states, dones, X_transformer, y_transformer)
    logger.info(f"Training results: {results}")
    
    # Predict
    logger.info("Making predictions...")
    test_state = np.random.randn(200)
    test_sequence = np.random.randn(60, 200)
    
    pred = trainer.predict(test_state, test_sequence)
    logger.info(f"Prediction: {pred}")
    
    # Save models
    trainer.save_all_models("demo")
    
    # Get report
    report = trainer.get_training_report()
    logger.info(f"Training report: {json.dumps(report, indent=2, default=str)}")


if __name__ == "__main__":
    asyncio.run(main())
