import asyncio
import numpy as np
import json
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import hashlib

logger = logging.getLogger(__name__)

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    HAS_TF = True
except:
    HAS_TF = False
    logger.warning("TensorFlow not available, using heuristic mode")

@dataclass
class StrategyState:
    """Market state for RL model"""
    timestamp: str
    chain_id: int
    dex_spreads: List[float]
    gas_price: float
    volatility: float
    liquidity: float
    slippage: float
    position_size: float
    recent_win_rate: float
    recent_profit_avg: float

@dataclass
class RLAction:
    """Action taken by RL agent"""
    strategy_id: int
    position_size: float
    gas_multiplier: float
    slippage_tolerance: float
    priority: str
    confidence: float

class PPONetwork:
    """Proximal Policy Optimization Actor-Critic Network"""
    
    def __init__(self, state_dim: int, action_dim: int, learning_rate: float = 1e-4):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.learning_rate = learning_rate
        self.gamma = 0.99
        self.gae_lambda = 0.95
        self.clip_ratio = 0.2
        
        self._build_networks()
    
    def _build_networks(self):
        """Build actor and critic networks"""
        if not HAS_TF:
            self.actor = None
            self.critic = None
            return
            
        # Actor Network (Policy)
        actor_input = keras.Input(shape=(self.state_dim,), name="actor_input")
        x = layers.Dense(256, activation="relu")(actor_input)
        x = layers.BatchNormalization()(x)
        x = layers.Dense(256, activation="relu")(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dense(128, activation="relu")(x)
        actor_output = layers.Dense(self.action_dim, activation="tanh", name="actor_output")(x)
        self.actor = keras.Model(inputs=actor_input, outputs=actor_output)
        self.actor_optimizer = keras.optimizers.Adam(learning_rate=self.learning_rate)
        
        # Critic Network (Value)
        critic_input = keras.Input(shape=(self.state_dim,), name="critic_input")
        x = layers.Dense(256, activation="relu")(critic_input)
        x = layers.BatchNormalization()(x)
        x = layers.Dense(256, activation="relu")(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dense(128, activation="relu")(x)
        critic_output = layers.Dense(1, name="critic_output")(x)
        self.critic = keras.Model(inputs=critic_input, outputs=critic_output)
        self.critic_optimizer = keras.optimizers.Adam(learning_rate=self.learning_rate)
    
    def get_action(self, state: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Get action and log probability from current state"""
        if not HAS_TF:
            return np.random.uniform(-1, 1, self.action_dim), np.zeros(1)
        
        state = np.array([state])
        action = self.actor(state)
        return action[0].numpy(), np.zeros(1)
    
    def get_value(self, state: np.ndarray) -> float:
        """Get state value from critic"""
        if not HAS_TF:
            return 0.0
        
        state = np.array([state])
        value = self.critic(state)
        return value[0][0].numpy()
    
    def train_step(self, states: np.ndarray, actions: np.ndarray, advantages: np.ndarray, returns: np.ndarray):
        """Single PPO training step"""
        if not HAS_TF:
            return {"actor_loss": 0.0, "critic_loss": 0.0}
        
        with tf.GradientTape() as actor_tape:
            actor_output = self.actor(states)
            policy_loss = -tf.reduce_mean(actor_output * advantages)
        
        actor_grads = actor_tape.gradient(policy_loss, self.actor.trainable_variables)
        self.actor_optimizer.apply_gradients(zip(actor_grads, self.actor.trainable_variables))
        
        with tf.GradientTape() as critic_tape:
            values = self.critic(states)
            critic_loss = tf.reduce_mean(tf.square(returns - values))
        
        critic_grads = critic_tape.gradient(critic_loss, self.critic.trainable_variables)
        self.critic_optimizer.apply_gradients(zip(critic_grads, self.critic.trainable_variables))
        
        return {"actor_loss": float(policy_loss), "critic_loss": float(critic_loss)}

class DeepRLModel:
    """Deep Reinforcement Learning Agent for Strategy Selection & Optimization"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.state_dim = 10  # spreads, gas, volatility, liquidity, slippage, size, win_rate, profit_avg, timestamp, chain
        self.action_dim = 5  # strategy_id, position_size, gas_multiplier, slippage_tol, priority
        
        self.ppo_network = PPONetwork(
            state_dim=self.state_dim,
            action_dim=self.action_dim,
            learning_rate=self.config.get('learning_rate', 1e-4)
        )
        
        self.strategy_weights = {
            0: 0.35,  # multi_dex_arbitrage
            1: 0.25,  # flash_loan_sandwich
            2: 0.15,  # mev_extraction
            3: 0.12,  # liquidity_sweep
            4: 0.08,  # curve_bridge_arb
            5: 0.05   # advanced_liquidation
        }
        
        self.last_training = datetime.now()
        self.training_interval = timedelta(hours=1)
        self.episode_buffer = []
        self.performance_history = []
        self.accuracy_history = []
    
    def encode_state(self, market_data: Dict) -> np.ndarray:
        """Encode market state for RL model"""
        state = np.zeros(self.state_dim)
        
        state[0] = market_data.get('avg_spread', 0.0001)
        state[1] = market_data.get('gas_price', 50.0)
        state[2] = market_data.get('volatility', 0.02)
        state[3] = market_data.get('liquidity', 1000.0)
        state[4] = market_data.get('slippage', 0.0005)
        state[5] = market_data.get('position_size', 100.0)
        state[6] = market_data.get('recent_win_rate', 0.85)
        state[7] = market_data.get('recent_profit_avg', 1.0)
        state[8] = float(datetime.now().timestamp()) % 86400  # seconds in day
        state[9] = market_data.get('chain_id', 1)
        
        # Normalize
        state[0] = np.clip(state[0] / 0.01, 0, 10)
        state[1] = np.clip(state[1] / 200, 0, 10)
        state[2] = np.clip(state[2] / 0.1, 0, 10)
        state[3] = np.clip(state[3] / 10000, 0, 10)
        state[4] = np.clip(state[4] / 0.01, 0, 10)
        state[5] = np.clip(state[5] / 1000, 0, 10)
        
        return state
    
    def decode_action(self, action: np.ndarray) -> RLAction:
        """Decode RL action to executable parameters"""
        strategy_id = int(np.clip((action[0] + 1) / 2 * 5.99, 0, 5))
        position_size = np.clip(200 + action[1] * 800, 50, 1000)
        gas_multiplier = np.clip(0.8 + action[2] * 0.4, 0.8, 1.2)
        slippage_tol = np.clip(0.0005 + action[3] * 0.0005, 0.0001, 0.001)
        
        priority = "HIGH" if action[4] > 0.5 else "MEDIUM"
        confidence = float((action[4] + 1) / 2)
        
        return RLAction(
            strategy_id=strategy_id,
            position_size=position_size,
            gas_multiplier=gas_multiplier,
            slippage_tolerance=slippage_tol,
            priority=priority,
            confidence=confidence
        )
    
    async def select_strategy(self, market_data: Dict) -> Dict:
        """Select optimal strategy using RL model"""
        state = self.encode_state(market_data)
        action, log_prob = self.ppo_network.get_action(state)
        rl_action = self.decode_action(action)
        
        return {
            'strategy_id': rl_action.strategy_id,
            'strategy_name': self._get_strategy_name(rl_action.strategy_id),
            'position_size': rl_action.position_size,
            'gas_multiplier': rl_action.gas_multiplier,
            'slippage_tolerance': rl_action.slippage_tolerance,
            'priority': rl_action.priority,
            'confidence': rl_action.confidence,
            'model_version': 'PPO-v1.0',
            'timestamp': datetime.now().isoformat()
        }
    
    def record_episode(self, state: np.ndarray, action: np.ndarray, reward: float, next_state: np.ndarray, done: bool):
        """Record experience for training"""
        self.episode_buffer.append({
            'state': state,
            'action': action,
            'reward': reward,
            'next_state': next_state,
            'done': done
        })
    
    async def train(self, experiences: List[Dict]) -> Dict:
        """Train RL model on batch of experiences"""
        if len(experiences) < 32:
            return {"status": "insufficient_data", "experiences": len(experiences)}
        
        states = np.array([e['state'] for e in experiences])
        actions = np.array([e['action'] for e in experiences])
        rewards = np.array([e['reward'] for e in experiences])
        next_states = np.array([e['next_state'] for e in experiences])
        dones = np.array([e['done'] for e in experiences])
        
        # Calculate advantages
        values = np.array([self.ppo_network.get_value(s) for s in states])
        next_values = np.array([self.ppo_network.get_value(s) for s in next_states])
        
        advantages = rewards + self.ppo_network.gamma * next_values * (1 - dones) - values
        returns = advantages + values
        
        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # Train for multiple epochs
        total_actor_loss = 0.0
        total_critic_loss = 0.0
        epochs = 4
        
        for epoch in range(epochs):
            metrics = self.ppo_network.train_step(states, actions, advantages, returns)
            total_actor_loss += metrics['actor_loss']
            total_critic_loss += metrics['critic_loss']
        
        avg_reward = np.mean(rewards)
        self.performance_history.append(avg_reward)
        
        return {
            'status': 'trained',
            'epochs': epochs,
            'avg_actor_loss': total_actor_loss / epochs,
            'avg_critic_loss': total_critic_loss / epochs,
            'avg_reward': avg_reward,
            'experiences_used': len(experiences)
        }
    
    async def hourly_retraining(self, training_data: List[Dict]) -> Dict:
        """Hourly retraining cycle"""
        if datetime.now() - self.last_training < self.training_interval:
            return {"status": "not_due"}
        
        logger.info(f"Starting hourly retraining with {len(training_data)} experiences")
        
        # Train
        results = await self.train(training_data)
        
        # Calculate accuracy
        accuracy = self._calculate_model_accuracy(training_data)
        self.accuracy_history.append(accuracy)
        
        self.last_training = datetime.now()
        
        return {
            'status': 'retrained',
            'training_results': results,
            'model_accuracy': accuracy,
            'accuracy_trend': self._get_accuracy_trend(),
            'next_retraining': (datetime.now() + self.training_interval).isoformat()
        }
    
    def _calculate_model_accuracy(self, experiences: List[Dict]) -> float:
        """Calculate model prediction accuracy"""
        if not experiences:
            return 0.0
        
        correct = 0
        for exp in experiences:
            state = exp.get('state')
            actual_reward = exp.get('reward', 0)
            predicted_value = self.ppo_network.get_value(state)
            
            if abs(actual_reward - predicted_value) < 0.5:
                correct += 1
        
        accuracy = (correct / len(experiences)) * 100
        return min(accuracy, 99.9)
    
    def _get_accuracy_trend(self) -> str:
        """Analyze accuracy trend"""
        if len(self.accuracy_history) < 2:
            return "stable"
        
        recent = np.mean(self.accuracy_history[-5:])
        previous = np.mean(self.accuracy_history[-10:-5]) if len(self.accuracy_history) >= 10 else recent
        
        if recent > previous + 1.0:
            return "improving"
        elif recent < previous - 1.0:
            return "degrading"
        else:
            return "stable"
    
    def _get_strategy_name(self, strategy_id: int) -> str:
        """Get strategy name from ID"""
        names = {
            0: "multi_dex_arbitrage",
            1: "flash_loan_sandwich",
            2: "mev_extraction",
            3: "liquidity_sweep",
            4: "curve_bridge_arb",
            5: "advanced_liquidation"
        }
        return names.get(strategy_id, "unknown")
    
    def get_model_stats(self) -> Dict:
        """Get current model statistics"""
        return {
            'model_type': 'PPO',
            'state_dim': self.state_dim,
            'action_dim': self.action_dim,
            'total_performances': len(self.performance_history),
            'total_accuracy_samples': len(self.accuracy_history),
            'latest_accuracy': self.accuracy_history[-1] if self.accuracy_history else 0.0,
            'accuracy_trend': self._get_accuracy_trend(),
            'last_training': self.last_training.isoformat(),
            'strategy_weights': self.strategy_weights,
            'avg_recent_performance': np.mean(self.performance_history[-100:]) if self.performance_history else 0.0
        }
    
    def save_model(self, path: str):
        """Save model to disk"""
        if HAS_TF and self.ppo_network.actor:
            self.ppo_network.actor.save(f"{path}/actor_model.h5")
            self.ppo_network.critic.save(f"{path}/critic_model.h5")
            logger.info(f"Models saved to {path}")
    
    def load_model(self, path: str):
        """Load model from disk"""
        if HAS_TF:
            try:
                self.ppo_network.actor = keras.models.load_model(f"{path}/actor_model.h5")
                self.ppo_network.critic = keras.models.load_model(f"{path}/critic_model.h5")
                logger.info(f"Models loaded from {path}")
            except Exception as e:
                logger.error(f"Failed to load models: {e}")
