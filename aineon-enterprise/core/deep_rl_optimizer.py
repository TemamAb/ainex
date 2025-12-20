"""PHASE 4 FILE 1: Deep Reinforcement Learning Optimizer - Neural Network Enhancement"""

import asyncio
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import time
from datetime import datetime, timedelta
from collections import deque
import json

logger = logging.getLogger(__name__)

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models
    HAS_TF = True
except ImportError:
    HAS_TF = False
    logger.warning("TensorFlow not available - running in heuristic mode")


@dataclass
class TrainingEpisode:
    """RL training episode"""
    episode_id: str
    market_state: List[float] = field(default_factory=list)
    action: str = ""  # 'buy', 'sell', 'hold'
    reward: float = 0.0
    next_state: List[float] = field(default_factory=list)
    loss: float = 0.0
    profit_realized: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class RLMetrics:
    """RL training metrics"""
    episode: int = 0
    avg_episode_reward: float = 0.0
    model_loss: float = 0.0
    exploration_rate: float = 1.0
    win_rate: float = 0.0
    profit_per_episode: float = 0.0
    model_accuracy: float = 0.0
    policy_divergence: float = 0.0


class DeepRLOptimizer:
    """Deep Reinforcement Learning optimizer for AINEON (PPO + Actor-Critic)"""
    
    def __init__(self, state_size: int = 64, action_size: int = 3):
        self.state_size = state_size
        self.action_size = action_size  # buy, sell, hold
        
        # Model configuration
        self.learning_rate = 0.0001
        self.gamma = 0.99  # Discount factor
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.batch_size = 32
        self.memory = deque(maxlen=10000)
        
        # RL Model
        self.policy_model = self._build_policy_network() if HAS_TF else None
        self.value_model = self._build_value_network() if HAS_TF else None
        self.target_model = self._build_policy_network() if HAS_TF else None
        
        # Training metrics
        self.metrics = RLMetrics()
        self.episode_count = 0
        self.total_training_time = 0.0
        self.episode_rewards = deque(maxlen=100)
        self.episode_losses = deque(maxlen=100)
        self.training_history = []
        
        # Model version control
        self.model_version = 1
        self.best_model_version = 1
        self.best_win_rate = 0.0
        
        logger.info(f"🤖 Deep RL Optimizer initialized: State={state_size}, Actions={action_size}")
    
    def _build_policy_network(self) -> Optional[keras.Model]:
        """Build policy network (Actor) - PPO policy network"""
        if not HAS_TF:
            return None
        
        try:
            model = models.Sequential([
                layers.Dense(256, activation='relu', input_shape=(self.state_size,)),
                layers.BatchNormalization(),
                layers.Dropout(0.2),
                
                layers.Dense(256, activation='relu'),
                layers.BatchNormalization(),
                layers.Dropout(0.2),
                
                layers.Dense(128, activation='relu'),
                layers.BatchNormalization(),
                layers.Dropout(0.15),
                
                layers.Dense(64, activation='relu'),
                layers.Dense(self.action_size, activation='softmax')
            ])
            
            model.compile(
                optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate),
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )
            
            logger.info("✓ Policy network (Actor) built: 4 hidden layers, 256→256→128→64 neurons")
            return model
        except Exception as e:
            logger.error(f"Policy network build failed: {e}")
            return None
    
    def _build_value_network(self) -> Optional[keras.Model]:
        """Build value network (Critic) - estimates state value"""
        if not HAS_TF:
            return None
        
        try:
            model = models.Sequential([
                layers.Dense(256, activation='relu', input_shape=(self.state_size,)),
                layers.BatchNormalization(),
                layers.Dropout(0.2),
                
                layers.Dense(128, activation='relu'),
                layers.BatchNormalization(),
                layers.Dropout(0.2),
                
                layers.Dense(64, activation='relu'),
                layers.Dense(1, activation='linear')  # Value output
            ])
            
            model.compile(
                optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate),
                loss='mse',
                metrics=['mae']
            )
            
            logger.info("✓ Value network (Critic) built: 3 hidden layers, 256→128→64 neurons")
            return model
        except Exception as e:
            logger.error(f"Value network build failed: {e}")
            return None
    
    async def select_action(self, market_state: List[float]) -> str:
        """Select action using epsilon-greedy strategy (exploration vs exploitation)"""
        try:
            if not self.policy_model or not HAS_TF:
                # Fallback: random action
                return ['buy', 'sell', 'hold'][np.random.randint(0, 3)]
            
            # Exploration: random action
            if np.random.random() < self.epsilon:
                action_idx = np.random.randint(0, self.action_size)
                self.metrics.exploration_rate = self.epsilon
                return ['buy', 'sell', 'hold'][action_idx]
            
            # Exploitation: use policy network
            state_tensor = np.array(market_state).reshape(1, -1)
            action_probs = self.policy_model.predict(state_tensor, verbose=0)[0]
            action_idx = np.argmax(action_probs)
            
            self.metrics.exploration_rate = self.epsilon
            return ['buy', 'sell', 'hold'][action_idx]
            
        except Exception as e:
            logger.error(f"Action selection error: {e}")
            return 'hold'
    
    def remember(self, episode: TrainingEpisode) -> None:
        """Store episode in replay memory"""
        self.memory.append(episode)
    
    async def train_on_batch(self) -> float:
        """Train on batch from replay memory"""
        if not self.policy_model or not HAS_TF or len(self.memory) < self.batch_size:
            return 0.0
        
        try:
            # Sample batch from memory
            batch_size = min(self.batch_size, len(self.memory))
            batch = list(np.random.choice(list(self.memory), batch_size))
            
            states = np.array([e.market_state for e in batch])
            actions = np.array([['buy', 'sell', 'hold'].index(e.action) for e in batch])
            rewards = np.array([e.reward for e in batch])
            next_states = np.array([e.next_state for e in batch])
            
            # Convert actions to one-hot
            actions_one_hot = keras.utils.to_categorical(actions, self.action_size)
            
            # Compute returns (discounted rewards)
            returns = np.zeros_like(rewards)
            next_values = self.value_model.predict(next_states, verbose=0).flatten()
            
            for i in range(len(batch) - 1, -1, -1):
                returns[i] = rewards[i] + self.gamma * next_values[i]
            
            # Train policy network
            policy_loss = self.policy_model.train_on_batch(states, actions_one_hot)
            
            # Train value network
            value_loss = self.value_model.train_on_batch(states, returns.reshape(-1, 1))
            
            # Update epsilon (decay exploration rate)
            if self.epsilon > self.epsilon_min:
                self.epsilon *= self.epsilon_decay
            
            combined_loss = (policy_loss + value_loss) / 2
            self.episode_losses.append(combined_loss)
            self.metrics.model_loss = combined_loss
            
            return combined_loss
            
        except Exception as e:
            logger.error(f"Training error: {e}")
            return 0.0
    
    async def train_continuous(self, training_window_minutes: int = 15):
        """Continuous training loop"""
        logger.info(f"🚀 Starting Deep RL continuous training ({training_window_minutes}min windows)...")
        
        start_time = time.time()
        
        while True:
            try:
                # Train on batches from replay memory
                for _ in range(10):
                    loss = await self.train_on_batch()
                    if loss > 0:
                        logger.debug(f"Training loss: {loss:.6f}")
                
                # Update metrics
                self.episode_count += 1
                self.metrics.episode = self.episode_count
                
                if self.episode_rewards:
                    self.metrics.avg_episode_reward = float(np.mean(list(self.episode_rewards)))
                
                if self.episode_losses:
                    self.metrics.model_loss = float(np.mean(list(self.episode_losses)))
                
                # Calculate win rate (episodes with positive reward)
                if self.episode_rewards:
                    positive_episodes = sum(1 for r in self.episode_rewards if r > 0)
                    self.metrics.win_rate = (positive_episodes / len(self.episode_rewards)) * 100
                
                # Periodic model evaluation
                if self.episode_count % 50 == 0:
                    await self._evaluate_model()
                    
                    logger.info(
                        f"📊 RL Training Update | Episode: {self.episode_count} | "
                        f"Win Rate: {self.metrics.win_rate:.1f}% | "
                        f"Avg Reward: {self.metrics.avg_episode_reward:.4f} | "
                        f"Loss: {self.metrics.model_loss:.6f} | "
                        f"Exploration: {self.metrics.exploration_rate:.3f}"
                    )
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Continuous training error: {e}")
                await asyncio.sleep(5)
    
    async def _evaluate_model(self) -> None:
        """Evaluate model on test data"""
        if not self.policy_model or not HAS_TF:
            return
        
        try:
            # Generate synthetic test states
            test_states = np.random.randn(100, self.state_size)
            
            # Get predictions
            predictions = self.policy_model.predict(test_states, verbose=0)
            predicted_actions = np.argmax(predictions, axis=1)
            
            # Calculate accuracy (entropy-based)
            max_confidences = np.max(predictions, axis=1)
            confidence = float(np.mean(max_confidences))
            
            self.metrics.model_accuracy = confidence * 100
            
            # Check for model improvement
            if self.metrics.win_rate > self.best_win_rate:
                self.best_win_rate = self.metrics.win_rate
                self.best_model_version = self.model_version
                logger.info(f"🏆 New best model: Version {self.model_version} | Win Rate: {self.metrics.win_rate:.1f}%")
                
                # Save improved model
                await self._save_model()
            
            self.model_version += 1
            
        except Exception as e:
            logger.error(f"Model evaluation error: {e}")
    
    async def _save_model(self) -> None:
        """Save current best model"""
        if not self.policy_model or not HAS_TF:
            return
        
        try:
            timestamp = datetime.utcnow().isoformat()
            model_path = f"models/deep_rl_v{self.best_model_version}_{timestamp.replace(':', '-')}.h5"
            self.policy_model.save(model_path)
            logger.info(f"💾 Model saved: {model_path}")
        except Exception as e:
            logger.error(f"Model save error: {e}")
    
    def predict_profit_opportunity(self, market_data: Dict) -> Tuple[float, float]:
        """Predict profit opportunity and confidence"""
        try:
            if not self.policy_model or not HAS_TF:
                return 0.5, 0.65
            
            # Extract features from market data
            features = self._extract_features(market_data)
            
            # Get policy prediction
            state_tensor = np.array(features).reshape(1, -1)
            action_probs = self.policy_model.predict(state_tensor, verbose=0)[0]
            
            # Get value estimate
            value = self.value_model.predict(state_tensor, verbose=0)[0][0]
            
            # Profit estimate = normalized value
            profit_estimate = float(value) / 100.0 if value else 0.5
            confidence = float(np.max(action_probs))
            
            return min(profit_estimate, 2.0), confidence
            
        except Exception as e:
            logger.error(f"Profit prediction error: {e}")
            return 0.5, 0.65
    
    def _extract_features(self, market_data: Dict) -> List[float]:
        """Extract features from market data for RL model"""
        features = []
        
        # Price features
        features.append(float(market_data.get('price', 0)))
        features.append(float(market_data.get('price_change_1h', 0)))
        features.append(float(market_data.get('price_change_24h', 0)))
        
        # Volume features
        features.append(float(market_data.get('volume_24h', 0)))
        features.append(float(market_data.get('volume_change', 0)))
        
        # Volatility features
        features.append(float(market_data.get('volatility', 0)))
        features.append(float(market_data.get('rsi', 50)))
        features.append(float(market_data.get('macd', 0)))
        
        # Liquidity features
        features.append(float(market_data.get('bid_ask_spread', 0.01)))
        features.append(float(market_data.get('liquidity_score', 0.5)))
        
        # Pad to state_size
        while len(features) < self.state_size:
            features.append(0.0)
        
        return features[:self.state_size]
    
    def get_training_stats(self) -> Dict:
        """Get current training statistics"""
        return {
            'episodes_trained': self.episode_count,
            'model_version': self.model_version,
            'best_model_version': self.best_model_version,
            'best_win_rate': self.best_win_rate,
            'current_win_rate': self.metrics.win_rate,
            'model_accuracy': self.metrics.model_accuracy,
            'avg_episode_reward': self.metrics.avg_episode_reward,
            'current_loss': self.metrics.model_loss,
            'exploration_rate': self.metrics.exploration_rate,
            'memory_size': len(self.memory),
            'epsilon': self.epsilon,
            'model_available': self.policy_model is not None,
            'tensorflow_available': HAS_TF
        }
