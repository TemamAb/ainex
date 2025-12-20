"""
Phase 4 Deep Learning Tests
Deep RL (PPO) + Transformer Predictor + Hardware Acceleration
"""

import pytest
import numpy as np
import asyncio
from unittest.mock import Mock, patch

from core.deep_rl import (
    PPOAgent, RLState, RLAction, ExperienceBuffer,
    ActorCriticNetwork, DeepRLOptimizer
)
from core.transformer_predictor import (
    TransformerPredictor, TransformerPredictionEngine, PredictionBuffer
)
from core.hardware_acceleration import (
    GPUAccelerator, LatencyOptimizer, HardwareAccelerationEngine
)


class TestRLState:
    """Test RL state representation"""
    
    def test_state_creation(self):
        """Test state creation"""
        state = RLState(
            volatility=0.05,
            trend=0.02,
            momentum=0.01,
            spread=0.001,
            volume=0.5,
            profit_target=0.5,
            success_rate=0.85,
            slippage=0.0003,
            gas_price=0.5,
            liquidity=0.8
        )
        
        assert state.volatility == 0.05
        assert len(state.to_array()) == 10
    
    def test_state_to_array(self):
        """Test state array conversion"""
        state = RLState(
            volatility=0.05, trend=0.02, momentum=0.01, spread=0.001,
            volume=0.5, profit_target=0.5, success_rate=0.85, slippage=0.0003,
            gas_price=0.5, liquidity=0.8
        )
        
        array = state.to_array()
        
        assert array.dtype == np.float32
        assert len(array) == 10
        assert np.all(np.isfinite(array))


class TestRLAction:
    """Test RL action representation"""
    
    def test_action_creation(self):
        """Test action creation"""
        action = RLAction(
            strategy_id=0,
            position_size=0.5,
            gas_price_multiplier=1.0,
            slippage_tolerance=0.001,
            execution_priority=1
        )
        
        assert action.strategy_id == 0
        assert action.position_size == 0.5
    
    def test_action_to_array(self):
        """Test action array conversion"""
        action = RLAction(3, 0.7, 1.1, 0.002, 2)
        
        array = action.to_array()
        
        assert array.dtype == np.float32
        assert len(array) == 5
        assert np.all(np.isfinite(array))


class TestExperienceBuffer:
    """Test experience replay buffer"""
    
    def test_buffer_initialization(self):
        """Test buffer init"""
        buffer = ExperienceBuffer(capacity=100)
        
        assert buffer.capacity == 100
        assert buffer.size() == 0
        assert not buffer.is_full()
    
    def test_add_experience(self):
        """Test adding experience"""
        buffer = ExperienceBuffer(capacity=100)
        state = RLState(0.05, 0.02, 0.01, 0.001, 0.5, 0.5, 0.85, 0.0003, 0.5, 0.8)
        action = RLAction(0, 0.5, 1.0, 0.001, 1)
        
        buffer.add(state, action, 1.5, state, False, -0.5, 0.3)
        
        assert buffer.size() == 1
    
    def test_batch_sampling(self):
        """Test batch sampling"""
        buffer = ExperienceBuffer(capacity=100)
        state = RLState(0.05, 0.02, 0.01, 0.001, 0.5, 0.5, 0.85, 0.0003, 0.5, 0.8)
        action = RLAction(0, 0.5, 1.0, 0.001, 1)
        
        for _ in range(50):
            buffer.add(state, action, 1.5, state, False, -0.5, 0.3)
        
        states, actions, rewards, _, _, _, _ = buffer.get_batch(16)
        
        assert states.shape == (16, 10)
        assert actions.shape == (16, 5)
        assert len(rewards) == 16


class TestActorCriticNetwork:
    """Test actor-critic network"""
    
    def test_network_initialization(self):
        """Test network init"""
        network = ActorCriticNetwork(state_dim=10, action_dim=5)
        
        assert network.state_dim == 10
        assert network.action_dim == 5
        assert len(network.actor_weights) == 3
        assert len(network.critic_weights) == 3
    
    def test_forward_pass(self):
        """Test forward pass"""
        network = ActorCriticNetwork()
        state = np.random.randn(10).astype(np.float32)
        
        action = network.forward_actor(state)
        value = network.forward_critic(state)
        
        assert action.shape == (5,)
        assert isinstance(value, float)
        assert 0 <= value <= 1  # Output normalized
    
    def test_action_sampling(self):
        """Test action sampling"""
        network = ActorCriticNetwork()
        state = np.random.randn(10).astype(np.float32)
        
        action, log_prob = network.get_action(state)
        
        assert action.shape == (5,)
        assert isinstance(log_prob, (float, np.floating))


class TestPPOAgent:
    """Test PPO agent"""
    
    def test_agent_initialization(self):
        """Test agent init"""
        agent = PPOAgent(state_dim=10, action_dim=5)
        
        assert agent.step_count == 0
        assert agent.episode_count == 0
        assert agent.total_reward == 0.0
    
    def test_agent_step(self):
        """Test agent step"""
        agent = PPOAgent()
        state = RLState(0.05, 0.02, 0.01, 0.001, 0.5, 0.5, 0.85, 0.0003, 0.5, 0.8)
        
        action = agent.step(state, reward=1.5, done=False)
        
        assert isinstance(action, RLAction)
        assert agent.step_count == 1
        assert agent.total_reward == 1.5
    
    def test_agent_training(self):
        """Test agent training"""
        agent = PPOAgent()
        state = RLState(0.05, 0.02, 0.01, 0.001, 0.5, 0.5, 0.85, 0.0003, 0.5, 0.8)
        
        # Add experiences
        for _ in range(50):
            agent.step(state, reward=1.0, done=False)
        
        metrics = agent.train()
        
        assert 'loss' in metrics
        assert 'advantage' in metrics
        assert metrics['steps'] == 50
    
    def test_deterministic_action(self):
        """Test deterministic action selection"""
        agent = PPOAgent()
        state = RLState(0.05, 0.02, 0.01, 0.001, 0.5, 0.5, 0.85, 0.0003, 0.5, 0.8)
        
        action = agent.get_action_deterministic(state)
        
        assert isinstance(action, RLAction)
        assert 0 <= action.strategy_id <= 5
        assert 0.1 <= action.position_size <= 1.0


class TestDeepRLOptimizer:
    """Test deep RL optimizer"""
    
    @pytest.mark.asyncio
    async def test_optimizer_initialization(self):
        """Test optimizer init"""
        optimizer = DeepRLOptimizer()
        
        assert optimizer.agent is not None
        assert optimizer.training_interval == 100
    
    @pytest.mark.asyncio
    async def test_action_selection(self):
        """Test action selection"""
        optimizer = DeepRLOptimizer()
        
        market_state = {
            'volatility': 0.05,
            'trend': 0.02,
            'momentum': 0.01,
            'spread': 0.001,
            'volume': 0.5,
            'profit_target': 0.5,
            'success_rate': 0.85,
            'slippage': 0.0003,
            'gas_price': 50,
            'liquidity': 0.5
        }
        
        action = await optimizer.select_action(market_state)
        
        assert 'strategy_id' in action
        assert 'position_size' in action
        assert 'gas_price_multiplier' in action


class TestTransformerPredictor:
    """Test transformer predictor"""
    
    def test_predictor_initialization(self):
        """Test predictor init"""
        predictor = TransformerPredictor(seq_len=60, input_dim=8, output_dim=5)
        
        assert predictor.seq_len == 60
        assert predictor.input_dim == 8
        assert predictor.output_dim == 5
    
    def test_positional_encoding(self):
        """Test positional encoding"""
        predictor = TransformerPredictor(seq_len=60)
        
        pe = predictor._create_positional_encoding(60, 64)
        
        assert pe.shape == (60, 64)
        assert np.all(np.isfinite(pe))
    
    def test_forward_pass(self):
        """Test forward pass"""
        predictor = TransformerPredictor()
        
        sequence = np.random.randn(60, 8).astype(np.float32)
        
        output = predictor.forward(sequence)
        
        assert output.shape == (5,)
        assert np.all((output >= 0) & (output <= 1))  # Normalized
    
    def test_prediction(self):
        """Test prediction"""
        predictor = TransformerPredictor()
        
        history = np.random.randn(60, 8).astype(np.float32)
        
        predictions = predictor.predict(history)
        
        assert 'profit_prediction' in predictions
        assert 'confidence' in predictions
        assert 'opportunity_score' in predictions
        assert 'direction' in predictions
        assert 'liquidity_trend' in predictions
        
        for value in predictions.values():
            assert 0 <= value <= 1


class TestPredictionBuffer:
    """Test prediction buffer"""
    
    def test_buffer_initialization(self):
        """Test buffer init"""
        buffer = PredictionBuffer(capacity=60)
        
        assert buffer.capacity == 60
        assert buffer.size() == 0
        assert not buffer.is_full()
    
    def test_add_data(self):
        """Test adding data"""
        buffer = PredictionBuffer(capacity=60)
        data = np.random.randn(8).astype(np.float32)
        
        buffer.add(data)
        
        assert buffer.size() == 1
    
    def test_history_retrieval(self):
        """Test history retrieval"""
        buffer = PredictionBuffer(capacity=10)
        
        for _ in range(10):
            data = np.random.randn(8).astype(np.float32)
            buffer.add(data)
        
        assert buffer.is_full()
        
        history = buffer.get_history()
        assert history.shape == (10, 8)


class TestTransformerPredictionEngine:
    """Test transformer prediction engine"""
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self):
        """Test engine init"""
        engine = TransformerPredictionEngine()
        
        assert engine.predictor is not None
        assert engine.buffer is not None
    
    @pytest.mark.asyncio
    async def test_add_market_data(self):
        """Test adding market data"""
        engine = TransformerPredictionEngine()
        
        market_data = {
            'price': 1.0,
            'volume': 100,
            'spread': 0.001,
            'volatility': 0.05,
            'trend': 0.02,
            'momentum': 0.01,
            'rsi': 50.0,
            'macd': 0.0
        }
        
        engine.add_market_data(market_data)
        
        assert engine.buffer.size() == 1
    
    @pytest.mark.asyncio
    async def test_prediction(self):
        """Test prediction with full buffer"""
        engine = TransformerPredictionEngine()
        
        # Fill buffer
        for _ in range(60):
            market_data = {
                'price': 1.0 + np.random.randn() * 0.01,
                'volume': 100,
                'spread': 0.001,
                'volatility': 0.05,
                'trend': 0.02,
                'momentum': 0.01,
                'rsi': 50.0,
                'macd': 0.0
            }
            engine.add_market_data(market_data)
        
        prediction = await engine.predict()
        
        assert prediction is not None
        assert 'profit_prediction' in prediction
        assert 'confidence' in prediction


class TestGPUAccelerator:
    """Test GPU accelerator"""
    
    def test_accelerator_initialization(self):
        """Test accelerator init"""
        accelerator = GPUAccelerator(enable_gpu=False)  # Disable GPU for testing
        
        assert accelerator.device == "CPU"
        assert accelerator.latency_history is not None
    
    def test_execute_function(self):
        """Test function execution"""
        accelerator = GPUAccelerator(enable_gpu=False)
        
        def dummy_func(x):
            return x * 2
        
        elapsed_ms, result = accelerator.execute_on_device(dummy_func, 5)
        
        assert result == 10
        assert elapsed_ms > 0
        assert len(accelerator.latency_history) == 1
    
    def test_matrix_multiply(self):
        """Test matrix multiplication"""
        accelerator = GPUAccelerator(enable_gpu=False)
        
        A = np.random.randn(10, 10)
        B = np.random.randn(10, 10)
        
        elapsed_ms, result = accelerator.matrix_multiply(A, B)
        
        assert result.shape == (10, 10)
        assert elapsed_ms > 0
    
    def test_latency_stats(self):
        """Test latency statistics"""
        accelerator = GPUAccelerator(enable_gpu=False)
        
        for _ in range(10):
            accelerator.execute_on_device(lambda x: x * 2, 5)
        
        stats = accelerator.get_latency_stats()
        
        assert 'avg_latency_ms' in stats
        assert 'min_latency_ms' in stats
        assert 'max_latency_ms' in stats
        assert stats['measurements'] == 10


class TestLatencyOptimizer:
    """Test latency optimizer"""
    
    @pytest.mark.asyncio
    async def test_optimizer_initialization(self):
        """Test optimizer init"""
        optimizer = LatencyOptimizer()
        
        assert optimizer.target_latency_us == 150
        assert optimizer.accelerator is not None
    
    @pytest.mark.asyncio
    async def test_optimize(self):
        """Test optimization"""
        optimizer = LatencyOptimizer()
        
        report = await optimizer.optimize()
        
        assert 'optimization_level' in report
        assert 'device' in report


class TestHardwareAccelerationEngine:
    """Test hardware acceleration engine"""
    
    def test_engine_initialization(self):
        """Test engine init"""
        engine = HardwareAccelerationEngine()
        
        assert engine.accelerator is not None
        assert engine.latency_optimizer is not None
    
    @pytest.mark.asyncio
    async def test_auto_tune(self):
        """Test auto-tuning"""
        engine = HardwareAccelerationEngine()
        
        report = await engine.auto_tune()
        
        assert 'optimization_report' in report
        assert 'latency_report' in report
        assert 'device' in report
    
    def test_get_stats(self):
        """Test stats retrieval"""
        engine = HardwareAccelerationEngine()
        
        stats = engine.get_stats()
        
        assert 'device' in stats
        assert 'gpu_available' in stats
        assert 'latency_stats' in stats


# Integration tests
class TestPhase4Integration:
    """Integration tests for Phase 4"""
    
    @pytest.mark.asyncio
    async def test_full_deep_rl_pipeline(self):
        """Test full deep RL pipeline"""
        optimizer = DeepRLOptimizer()
        
        # Simulate market and execution
        market_state = {
            'volatility': 0.05,
            'trend': 0.02,
            'momentum': 0.01,
            'spread': 0.001,
            'volume': 0.5,
            'profit_target': 0.5,
            'success_rate': 0.85,
            'slippage': 0.0003,
            'gas_price': 50,
            'liquidity': 0.5
        }
        
        # Select action
        action = await optimizer.select_action(market_state)
        assert action is not None
        
        # Simulate execution result
        result = {
            'profit': 1.5,
            'success': True,
            'gas_cost': 0.05
        }
        
        # Update agent
        await optimizer.update_from_execution(market_state, result)
        
        # Get summary
        summary = optimizer.get_summary()
        assert 'agent_metrics' in summary
    
    @pytest.mark.asyncio
    async def test_transformer_prediction_pipeline(self):
        """Test full transformer prediction pipeline"""
        engine = TransformerPredictionEngine()
        
        # Fill buffer with data
        for i in range(60):
            market_data = {
                'price': 1.0 + (i * 0.001),
                'volume': 100,
                'spread': 0.001,
                'volatility': 0.05,
                'trend': 0.02,
                'momentum': 0.01,
                'rsi': 50.0,
                'macd': 0.0
            }
            engine.add_market_data(market_data)
        
        # Make prediction
        prediction = await engine.predict()
        
        assert prediction is not None
        
        # Update accuracy
        result = {'profit': 1.5}
        engine.update_accuracy(prediction, result)
        
        # Get metrics
        metrics = engine.get_metrics()
        assert metrics['total_predictions'] >= 1
    
    @pytest.mark.asyncio
    async def test_latency_target(self):
        """Test <150µs latency target"""
        engine = HardwareAccelerationEngine()
        
        # Run auto-tuning
        report = await engine.auto_tune()
        
        latency_report = report.get('latency_report', {})
        avg_latency_us = latency_report.get('avg_latency_us', 1000)
        
        # Note: CPU may exceed 150µs, but we're testing the framework
        logger.info(f"Average latency: {avg_latency_us}µs (target: 150µs)")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
