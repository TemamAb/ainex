import asyncio
import numpy as np
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import aiohttp

logger = logging.getLogger(__name__)

@dataclass
class TrainingBatch:
    """Batch of experiences for training"""
    batch_id: str
    state_vectors: List[np.ndarray]
    actions: List[np.ndarray]
    rewards: List[float]
    next_states: List[np.ndarray]
    dones: List[bool]
    timestamps: List[str]
    size: int

class ContinuousLearningEngine:
    """Hourly retraining and online learning for RL model"""
    
    def __init__(self, rl_model, config: Dict = None):
        self.rl_model = rl_model
        self.config = config or {}
        
        self.batch_size = self.config.get('batch_size', 32)
        self.retraining_interval = timedelta(hours=1)
        self.experience_buffer = []
        self.max_buffer_size = 10000
        
        self.training_history = []
        self.adaptive_params = {
            'learning_rate': 1e-4,
            'batch_size': self.batch_size,
            'gamma': 0.99,
            'gae_lambda': 0.95
        }
        
        self.last_retraining = datetime.now()
        self.training_count = 0
        self.total_experiences = 0
        self.training_enabled = True
    
    async def add_experience(self, state: np.ndarray, action: np.ndarray, reward: float, 
                            next_state: np.ndarray, done: bool) -> None:
        """Add experience to buffer"""
        experience = {
            'state': state,
            'action': action,
            'reward': reward,
            'next_state': next_state,
            'done': done,
            'timestamp': datetime.now().isoformat()
        }
        
        self.experience_buffer.append(experience)
        self.total_experiences += 1
        
        # Maintain buffer size
        if len(self.experience_buffer) > self.max_buffer_size:
            self.experience_buffer.pop(0)
    
    async def should_retrain(self) -> bool:
        """Check if retraining is due"""
        time_elapsed = datetime.now() - self.last_retraining
        buffer_ready = len(self.experience_buffer) >= self.batch_size * 4
        
        return (time_elapsed >= self.retraining_interval) and buffer_ready
    
    async def perform_retraining(self) -> Dict:
        """Execute hourly retraining cycle"""
        if not self.training_enabled:
            return {"status": "training_disabled"}
        
        if len(self.experience_buffer) < self.batch_size:
            return {"status": "insufficient_experiences", "buffered": len(self.experience_buffer)}
        
        logger.info(f"Starting hourly retraining with {len(self.experience_buffer)} experiences")
        
        start_time = datetime.now()
        
        # Create training batch
        batch = self._create_training_batch(self.experience_buffer)
        
        # Train model
        training_results = await self.rl_model.train(self.experience_buffer)
        
        # Evaluate performance
        evaluation = self._evaluate_performance(self.experience_buffer)
        
        # Adapt parameters
        adaptation_info = self._adapt_parameters(evaluation)
        
        # Record training
        elapsed = (datetime.now() - start_time).total_seconds()
        training_record = {
            'timestamp': datetime.now().isoformat(),
            'training_results': training_results,
            'evaluation': evaluation,
            'adaptation': adaptation_info,
            'elapsed_seconds': elapsed,
            'experiences_used': len(self.experience_buffer),
            'total_experiences_ever': self.total_experiences
        }
        
        self.training_history.append(training_record)
        self.training_count += 1
        self.last_retraining = datetime.now()
        
        logger.info(f"Retraining #{self.training_count} completed in {elapsed:.2f}s")
        
        return {
            'status': 'retrained',
            'training_count': self.training_count,
            'training_results': training_results,
            'evaluation': evaluation,
            'adaptation': adaptation_info,
            'elapsed_seconds': elapsed,
            'next_retraining': (datetime.now() + self.retraining_interval).isoformat()
        }
    
    def _create_training_batch(self, experiences: List[Dict]) -> TrainingBatch:
        """Create a training batch from experiences"""
        batch_id = f"batch_{self.training_count}_{int(datetime.now().timestamp())}"
        
        states = [e['state'] for e in experiences]
        actions = [e['action'] for e in experiences]
        rewards = [e['reward'] for e in experiences]
        next_states = [e['next_state'] for e in experiences]
        dones = [e['done'] for e in experiences]
        timestamps = [e['timestamp'] for e in experiences]
        
        return TrainingBatch(
            batch_id=batch_id,
            state_vectors=states,
            actions=actions,
            rewards=rewards,
            next_states=next_states,
            dones=dones,
            timestamps=timestamps,
            size=len(experiences)
        )
    
    def _evaluate_performance(self, experiences: List[Dict]) -> Dict:
        """Evaluate model performance on batch"""
        if not experiences:
            return {}
        
        rewards = np.array([e['reward'] for e in experiences])
        
        return {
            'avg_reward': float(np.mean(rewards)),
            'max_reward': float(np.max(rewards)),
            'min_reward': float(np.min(rewards)),
            'std_reward': float(np.std(rewards)),
            'win_rate': float(np.sum(rewards > 0) / len(rewards)),
            'total_profit': float(np.sum(rewards)),
            'experiences': len(experiences)
        }
    
    def _adapt_parameters(self, evaluation: Dict) -> Dict:
        """Adapt learning parameters based on performance"""
        adaptation = {
            'adjustments': [],
            'rationale': []
        }
        
        avg_reward = evaluation.get('avg_reward', 0)
        win_rate = evaluation.get('win_rate', 0.5)
        
        # Adapt batch size based on reward variance
        std_reward = evaluation.get('std_reward', 1.0)
        if std_reward > 5.0:
            self.adaptive_params['batch_size'] = min(64, self.adaptive_params['batch_size'] + 4)
            adaptation['adjustments'].append('batch_size_increased')
            adaptation['rationale'].append('High reward variance, need larger batches')
        elif std_reward < 0.5:
            self.adaptive_params['batch_size'] = max(16, self.adaptive_params['batch_size'] - 4)
            adaptation['adjustments'].append('batch_size_decreased')
            adaptation['rationale'].append('Low variance, smaller batches sufficient')
        
        # Adapt learning rate based on win rate
        if win_rate > 0.9:
            self.adaptive_params['learning_rate'] *= 0.95
            adaptation['adjustments'].append('learning_rate_decreased')
            adaptation['rationale'].append('High win rate, reduce learning rate')
        elif win_rate < 0.7:
            self.adaptive_params['learning_rate'] *= 1.05
            adaptation['adjustments'].append('learning_rate_increased')
            adaptation['rationale'].append('Low win rate, increase learning rate')
        
        # Adapt gamma based on avg reward trend
        if len(self.training_history) > 5:
            recent_rewards = [t['evaluation']['avg_reward'] for t in self.training_history[-5:]]
            if np.mean(recent_rewards) > np.mean(recent_rewards[:-1]):
                self.adaptive_params['gamma'] = min(0.99, self.adaptive_params['gamma'] + 0.002)
                adaptation['adjustments'].append('gamma_increased')
                adaptation['rationale'].append('Positive trend in rewards')
        
        return adaptation
    
    async def online_learning_step(self, state: np.ndarray, action: np.ndarray, 
                                   reward: float, next_state: np.ndarray, done: bool) -> Dict:
        """Single online learning step (no batch wait)"""
        await self.add_experience(state, action, reward, next_state, done)
        
        # Check if retraining is due
        if await self.should_retrain():
            return await self.perform_retraining()
        
        return {"status": "experience_buffered", "buffer_size": len(self.experience_buffer)}
    
    def get_learning_stats(self) -> Dict:
        """Get learning engine statistics"""
        recent_history = self.training_history[-10:] if self.training_history else []
        
        return {
            'training_count': self.training_count,
            'total_experiences': self.total_experiences,
            'buffer_size': len(self.experience_buffer),
            'last_retraining': self.last_retraining.isoformat(),
            'next_retraining': (self.last_retraining + self.retraining_interval).isoformat(),
            'training_enabled': self.training_enabled,
            'adaptive_params': self.adaptive_params,
            'recent_performance': [
                {
                    'training_id': i,
                    'avg_reward': t.get('evaluation', {}).get('avg_reward'),
                    'win_rate': t.get('evaluation', {}).get('win_rate'),
                    'timestamp': t.get('timestamp')
                }
                for i, t in enumerate(recent_history)
            ]
        }
    
    def enable_training(self):
        """Enable training"""
        self.training_enabled = True
        logger.info("Training enabled")
    
    def disable_training(self):
        """Disable training"""
        self.training_enabled = False
        logger.warning("Training disabled")
    
    async def clear_buffer(self) -> Dict:
        """Clear experience buffer"""
        size_before = len(self.experience_buffer)
        self.experience_buffer = []
        logger.info(f"Cleared {size_before} experiences from buffer")
        return {"cleared": size_before, "buffer_size": len(self.experience_buffer)}


class MarketAdaptationEngine:
    """Real-time market condition adaptation"""
    
    def __init__(self, rl_model, learning_engine):
        self.rl_model = rl_model
        self.learning_engine = learning_engine
        
        self.market_regimes = {
            'high_volatility': {'volatility': (0.05, 1.0), 'liquidity': (0, 1000)},
            'normal': {'volatility': (0.02, 0.05), 'liquidity': (1000, 10000)},
            'low_volatility': {'volatility': (0, 0.02), 'liquidity': (10000, 100000)},
            'low_liquidity': {'liquidity': (0, 100)},
            'high_liquidity': {'liquidity': (50000, 1000000)}
        }
        
        self.regime_history = []
        self.adaptation_history = []
    
    def detect_regime(self, market_data: Dict) -> str:
        """Detect current market regime"""
        volatility = market_data.get('volatility', 0.03)
        liquidity = market_data.get('liquidity', 5000)
        
        if volatility > 0.05 and liquidity < 5000:
            regime = 'high_volatility'
        elif volatility > 0.05:
            regime = 'high_volatility'
        elif volatility < 0.02 and liquidity > 50000:
            regime = 'low_volatility'
        elif liquidity < 100:
            regime = 'low_liquidity'
        else:
            regime = 'normal'
        
        self.regime_history.append({
            'regime': regime,
            'timestamp': datetime.now().isoformat(),
            'market_data': market_data
        })
        
        return regime
    
    async def adapt_to_regime(self, regime: str) -> Dict:
        """Adapt strategy parameters to market regime"""
        adaptations = {}
        
        if regime == 'high_volatility':
            adaptations = {
                'position_size_multiplier': 0.7,
                'slippage_tolerance': 0.0003,
                'gas_multiplier': 1.1,
                'preferred_strategies': [2, 1],  # MEV extraction, sandwich
                'risk_limit_reduction': 0.8
            }
        
        elif regime == 'low_volatility':
            adaptations = {
                'position_size_multiplier': 1.3,
                'slippage_tolerance': 0.0007,
                'gas_multiplier': 0.9,
                'preferred_strategies': [0, 3],  # Multi-DEX, liquidity sweep
                'risk_limit_reduction': 1.0
            }
        
        elif regime == 'low_liquidity':
            adaptations = {
                'position_size_multiplier': 0.5,
                'slippage_tolerance': 0.0002,
                'gas_multiplier': 1.2,
                'preferred_strategies': [4],  # Bridge arbitrage
                'risk_limit_reduction': 0.6
            }
        
        else:  # normal
            adaptations = {
                'position_size_multiplier': 1.0,
                'slippage_tolerance': 0.0005,
                'gas_multiplier': 1.0,
                'preferred_strategies': [0, 1, 2],
                'risk_limit_reduction': 1.0
            }
        
        self.adaptation_history.append({
            'regime': regime,
            'adaptations': adaptations,
            'timestamp': datetime.now().isoformat()
        })
        
        return {
            'regime': regime,
            'adaptations': adaptations,
            'applied': True
        }
    
    def get_adaptation_stats(self) -> Dict:
        """Get adaptation statistics"""
        recent_regimes = self.regime_history[-100:] if self.regime_history else []
        regime_counts = {}
        
        for item in recent_regimes:
            regime = item['regime']
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
        
        return {
            'total_regime_detections': len(self.regime_history),
            'regime_distribution': regime_counts,
            'recent_regime': self.regime_history[-1]['regime'] if self.regime_history else 'unknown',
            'adaptation_count': len(self.adaptation_history),
            'latest_adaptation': self.adaptation_history[-1] if self.adaptation_history else None
        }
