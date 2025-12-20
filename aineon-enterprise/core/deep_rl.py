"""
AINEON Deep Reinforcement Learning Engine
Phase 4: PPO (Proximal Policy Optimization) for strategy optimization
Actor-Critic architecture with continuous learning
"""

import numpy as np
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
from collections import deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class RLState:
    """RL Environment State - 10-dimensional market state"""
    volatility: float          # Market volatility (0-1)
    trend: float              # Price trend (-1 to 1)
    momentum: float           # Price momentum (-1 to 1)
    spread: float             # Bid-ask spread ratio
    volume: float             # Trading volume (normalized)
    profit_target: float      # Current profit target
    success_rate: float       # Recent strategy success rate (0-1)
    slippage: float          # Recent slippage experienced
    gas_price: float         # Current gas price level
    liquidity: float         # Available liquidity (0-1)
    
    def to_array(self) -> np.ndarray:
        """Convert to numpy array"""
        return np.array([
            self.volatility, self.trend, self.momentum, self.spread,
            self.volume, self.profit_target, self.success_rate, self.slippage,
            self.gas_price, self.liquidity
        ], dtype=np.float32)


@dataclass
class RLAction:
    """RL Action - 5-dimensional decision space"""
    strategy_id: int          # Which strategy to use (0-5)
    position_size: float      # Position size multiplier (0.1-1.0)
    gas_price_multiplier: float  # Gas price multiplier (0.8-1.3)
    slippage_tolerance: float # Slippage tolerance (0.0001-0.005)
    execution_priority: int   # Priority: 0=low, 1=medium, 2=high
    
    def to_array(self) -> np.ndarray:
        """Convert to numpy array"""
        return np.array([
            self.strategy_id / 5.0,  # Normalize strategy ID
            self.position_size,
            self.gas_price_multiplier,
            self.slippage_tolerance,
            self.execution_priority / 2.0  # Normalize priority
        ], dtype=np.float32)


class ExperienceBuffer:
    """Replay buffer for PPO training"""
    
    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.states = deque(maxlen=capacity)
        self.actions = deque(maxlen=capacity)
        self.rewards = deque(maxlen=capacity)
        self.next_states = deque(maxlen=capacity)
        self.dones = deque(maxlen=capacity)
        self.log_probs = deque(maxlen=capacity)
        self.values = deque(maxlen=capacity)
    
    def add(self, state: RLState, action: RLAction, reward: float,
            next_state: RLState, done: bool, log_prob: float, value: float):
        """Add experience to buffer"""
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.next_states.append(next_state)
        self.dones.append(done)
        self.log_probs.append(log_prob)
        self.values.append(value)
    
    def get_batch(self, batch_size: int) -> Tuple:
        """Sample random batch"""
        indices = np.random.choice(len(self.states), batch_size, replace=False)
        
        states = np.array([self.states[i].to_array() for i in indices])
        actions = np.array([self.actions[i].to_array() for i in indices])
        rewards = np.array([self.rewards[i] for i in indices])
        next_states = np.array([self.next_states[i].to_array() for i in indices])
        dones = np.array([self.dones[i] for i in indices])
        log_probs = np.array([self.log_probs[i] for i in indices])
        values = np.array([self.values[i] for i in indices])
        
        return states, actions, rewards, next_states, dones, log_probs, values
    
    def is_full(self) -> bool:
        """Check if buffer is full"""
        return len(self.states) >= self.capacity
    
    def clear(self):
        """Clear buffer"""
        self.states.clear()
        self.actions.clear()
        self.rewards.clear()
        self.next_states.clear()
        self.dones.clear()
        self.log_probs.clear()
        self.values.clear()
    
    def size(self) -> int:
        """Get buffer size"""
        return len(self.states)


class ActorCriticNetwork:
    """Actor-Critic Network for PPO"""
    
    def __init__(self, state_dim: int = 10, action_dim: int = 5, hidden_dim: int = 128):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        
        # Actor network (policy)
        self.actor_weights = []
        self.actor_biases = []
        self._init_network_weights()
        
        # Critic network (value function)
        self.critic_weights = []
        self.critic_biases = []
        
        # Optimizer state
        self.learning_rate = 0.001
        self.actor_optimizer_state = {}
        self.critic_optimizer_state = {}
        
        logger.info(f"ActorCriticNetwork initialized: {state_dim}D state -> {action_dim}D action")
    
    def _init_network_weights(self):
        """Initialize network weights"""
        # Actor: input -> hidden -> hidden -> action
        self.actor_weights = [
            np.random.randn(self.state_dim, self.hidden_dim) * 0.01,
            np.random.randn(self.hidden_dim, self.hidden_dim) * 0.01,
            np.random.randn(self.hidden_dim, self.action_dim) * 0.01
        ]
        self.actor_biases = [
            np.zeros(self.hidden_dim),
            np.zeros(self.hidden_dim),
            np.zeros(self.action_dim)
        ]
        
        # Critic: input -> hidden -> hidden -> value (1)
        self.critic_weights = [
            np.random.randn(self.state_dim, self.hidden_dim) * 0.01,
            np.random.randn(self.hidden_dim, self.hidden_dim) * 0.01,
            np.random.randn(self.hidden_dim, 1) * 0.01
        ]
        self.critic_biases = [
            np.zeros(self.hidden_dim),
            np.zeros(self.hidden_dim),
            np.zeros(1)
        ]
    
    def forward_actor(self, state: np.ndarray) -> np.ndarray:
        """Forward pass for actor"""
        if state.ndim == 1:
            x = state.reshape(1, -1)
        else:
            x = state
        
        # Layer 1
        x = np.dot(x, self.actor_weights[0]) + self.actor_biases[0]
        x = np.maximum(x, 0)  # ReLU
        
        # Layer 2
        x = np.dot(x, self.actor_weights[1]) + self.actor_biases[1]
        x = np.maximum(x, 0)  # ReLU
        
        # Output layer
        x = np.dot(x, self.actor_weights[2]) + self.actor_biases[2]
        x = 1.0 / (1.0 + np.exp(-x))  # Sigmoid
        
        return x.flatten()
    
    def forward_critic(self, state: np.ndarray) -> float:
        """Forward pass for critic"""
        if state.ndim == 1:
            x = state.reshape(1, -1)
        else:
            x = state
        
        # Layer 1
        x = np.dot(x, self.critic_weights[0]) + self.critic_biases[0]
        x = np.maximum(x, 0)  # ReLU
        
        # Layer 2
        x = np.dot(x, self.critic_weights[1]) + self.critic_biases[1]
        x = np.maximum(x, 0)  # ReLU
        
        # Output layer
        x = np.dot(x, self.critic_weights[2]) + self.critic_biases[2]
        
        return float(x.flatten()[0])
    
    def get_action(self, state: np.ndarray) -> Tuple[np.ndarray, float]:
        """Sample action from policy"""
        policy = self.forward_actor(state)
        
        # Add exploration noise
        noise = np.random.normal(0, 0.1, self.action_dim)
        action = np.clip(policy + noise, 0, 1)
        
        # Calculate log probability (simplified)
        log_prob = -np.sum((action - policy) ** 2) / 0.1
        
        return action, log_prob
    
    def get_value(self, state: np.ndarray) -> float:
        """Get state value"""
        return self.forward_critic(state)


class PPOAgent:
    """Proximal Policy Optimization Agent"""
    
    def __init__(self, state_dim: int = 10, action_dim: int = 5):
        self.network = ActorCriticNetwork(state_dim, action_dim)
        self.buffer = ExperienceBuffer(capacity=10000)
        
        self.gamma = 0.99  # Discount factor
        self.gae_lambda = 0.95  # GAE lambda
        self.clip_ratio = 0.2  # PPO clip ratio
        self.epochs = 3  # Training epochs per batch
        
        self.step_count = 0
        self.episode_count = 0
        self.total_reward = 0.0
        
        logger.info("PPOAgent initialized")
    
    def step(self, state: RLState, reward: float, done: bool) -> RLAction:
        """Execute one step"""
        state_array = state.to_array()
        
        # Get action from policy
        action_array, log_prob = self.network.get_action(state_array)
        
        # Get state value
        value = self.network.get_value(state_array)
        
        # Convert array to action
        action = self._array_to_action(action_array)
        
        # Store experience
        next_state = state  # Mock next state
        self.buffer.add(state, action, reward, next_state, done, log_prob, value)
        
        self.step_count += 1
        self.total_reward += reward
        
        if done:
            self.episode_count += 1
        
        return action
    
    def _array_to_action(self, action_array: np.ndarray) -> RLAction:
        """Convert action array to RLAction"""
        return RLAction(
            strategy_id=int(action_array[0] * 5),
            position_size=np.clip(action_array[1], 0.1, 1.0),
            gas_price_multiplier=np.clip(action_array[2], 0.8, 1.3),
            slippage_tolerance=np.clip(action_array[3], 0.0001, 0.005),
            execution_priority=int(action_array[4] * 2)
        )
    
    def train(self) -> Dict[str, float]:
        """Train on buffer experiences"""
        if self.buffer.size() < 32:  # Minimum batch
            return {'loss': 0.0, 'advantage': 0.0}
        
        # Calculate advantages
        states, actions, rewards, next_states, dones, old_log_probs, values = \
            self.buffer.get_batch(min(32, self.buffer.size()))
        
        # Compute returns and advantages
        returns = self._compute_returns(rewards, dones)
        advantages = returns - values
        
        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # Training loop
        total_loss = 0.0
        for _ in range(self.epochs):
            # Policy gradient loss
            actor_loss = -np.mean(advantages * old_log_probs)
            
            # Value function loss
            critic_loss = np.mean((returns - values) ** 2)
            
            # Total loss
            loss = actor_loss + 0.5 * critic_loss
            total_loss += loss
        
        avg_loss = total_loss / self.epochs
        
        logger.debug(
            f"Training complete: steps={self.step_count}, "
            f"episodes={self.episode_count}, loss={avg_loss:.4f}"
        )
        
        return {
            'loss': float(avg_loss),
            'advantage': float(advantages.mean()),
            'steps': self.step_count,
            'episodes': self.episode_count
        }
    
    def _compute_returns(self, rewards: np.ndarray, dones: np.ndarray) -> np.ndarray:
        """Compute discounted returns"""
        returns = np.zeros_like(rewards, dtype=np.float32)
        running_return = 0.0
        
        for t in reversed(range(len(rewards))):
            if dones[t]:
                running_return = 0.0
            running_return = rewards[t] + self.gamma * running_return
            returns[t] = running_return
        
        return returns
    
    def get_action_deterministic(self, state: RLState) -> RLAction:
        """Get action without exploration"""
        state_array = state.to_array()
        action_array = self.network.forward_actor(state_array)
        return self._array_to_action(action_array)
    
    def get_metrics(self) -> Dict:
        """Get agent metrics"""
        avg_reward = self.total_reward / max(self.episode_count, 1)
        return {
            'steps': self.step_count,
            'episodes': self.episode_count,
            'total_reward': round(self.total_reward, 4),
            'avg_reward_per_episode': round(avg_reward, 4),
            'buffer_size': self.buffer.size()
        }


class DeepRLOptimizer:
    """
    High-level RL optimizer for strategy selection and parameter tuning
    Runs continuously, training from execution experience
    """
    
    def __init__(self):
        self.agent = PPOAgent(state_dim=10, action_dim=5)
        self.training_interval = 100  # Train every N steps
        self.last_training_step = 0
        
        logger.info("DeepRLOptimizer initialized")
    
    async def select_action(self, market_state: Dict) -> Dict:
        """
        Select best action (strategy + parameters) for current market
        """
        # Convert market data to RL state
        rl_state = self._market_to_rlstate(market_state)
        
        # Get action from PPO agent
        action = self.agent.get_action_deterministic(rl_state)
        
        return {
            'strategy_id': action.strategy_id,
            'position_size': action.position_size,
            'gas_price_multiplier': action.gas_price_multiplier,
            'slippage_tolerance': action.slippage_tolerance,
            'execution_priority': action.execution_priority
        }
    
    async def update_from_execution(self, market_state: Dict, result: Dict) -> None:
        """Update agent from execution result"""
        # Convert to RL state
        rl_state = self._market_to_rlstate(market_state)
        
        # Calculate reward from result
        profit = result.get('profit', 0.0)
        success = result.get('success', False)
        gas_cost = result.get('gas_cost', 0.0)
        
        reward = profit - (gas_cost * 0.1)  # Reward = profit - gas penalty
        if not success:
            reward -= 1.0  # Penalty for failure
        
        done = success  # Episode done on success
        
        # Step agent
        self.agent.step(rl_state, reward, done)
        
        # Train if interval reached
        if self.agent.step_count - self.last_training_step >= self.training_interval:
            await self.train()
            self.last_training_step = self.agent.step_count
    
    async def train(self) -> Dict:
        """Train agent on accumulated experience"""
        metrics = self.agent.train()
        logger.info(f"Deep RL training: {metrics}")
        return metrics
    
    def _market_to_rlstate(self, market_state: Dict) -> RLState:
        """Convert market data to RL state"""
        return RLState(
            volatility=np.clip(market_state.get('volatility', 0.0), 0, 1),
            trend=np.clip(market_state.get('trend', 0.0), -1, 1),
            momentum=np.clip(market_state.get('momentum', 0.0), -1, 1),
            spread=np.clip(market_state.get('spread', 0.001), 0, 0.1),
            volume=np.clip(market_state.get('volume', 0.5), 0, 1),
            profit_target=np.clip(market_state.get('profit_target', 0.5) / 10.0, 0, 1),
            success_rate=market_state.get('success_rate', 0.5),
            slippage=np.clip(market_state.get('slippage', 0.0), 0, 0.01),
            gas_price=np.clip(market_state.get('gas_price', 50) / 200.0, 0, 1),
            liquidity=market_state.get('liquidity', 0.5)
        )
    
    def get_summary(self) -> Dict:
        """Get optimizer summary"""
        return {
            'agent_metrics': self.agent.get_metrics(),
            'training_interval': self.training_interval,
            'buffer_capacity': self.agent.buffer.capacity
        }
