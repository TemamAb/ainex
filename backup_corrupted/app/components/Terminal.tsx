'use client';
import React, { useState, useEffect, useRef } from 'react';
import { Terminal as TerminalIcon, Send, Sparkles, TrendingUp, BarChart3, Lightbulb } from 'lucide-react';
import { aiTerminal, AIResponse, QueryIntent } from '../engine/AITerminalEngine';

interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  response?: AIResponse;
  timestamp: Date;
}

const Terminal: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '0',
      type: 'ai',
      content: '👋 Welcome to AI Terminal Assistant! I can help you with:\n\n• Finding arbitrage opportunities\n• Analyzing your performance\n• Explaining technical concepts\n• Predicting market outcomes\n• Recommending strategies\n\nAsk me anything!',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsProcessing(true);

    try {
      // Process query with AI engine
      const response = await aiTerminal.processQuery(input);

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: response.content,
        response,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: '❌ Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
      inputRef.current?.focus();
    }
  };

  const handleQuickAction = (query: string) => {
    setInput(query);
    inputRef.current?.focus();
  };

  const renderMessage = (message: Message) => {
    if (message.type === 'user') {
      return (
        <div key={message.id} className="flex justify-end mb-4">
          <div className="bg-[#5794F2] text-white px-4 py-2 rounded-lg max-w-[80%]">
            <div className="text-sm">{message.content}</div>
          </div>
        </div>
      );
    }

    // AI message
    return (
      <div key={message.id} className="flex gap-3 mb-4">
        <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
          <Sparkles className="w-4 h-4 text-white" />
        </div>
        <div className="flex-1">
          <div className="bg-[#1a1d23] border border-[#2a2d33] rounded-lg p-4">
            <div className="text-sm text-gray-300 whitespace-pre-line leading-relaxed">
              {message.content}
            </div>

            {/* Render action buttons if available */}
            {message.response?.actions && message.response.actions.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-gray-700">
                {message.response.actions.map((action, idx) => (
                  <button
                    key={idx}
                    className="px-3 py-1 bg-[#5794F2]/20 hover:bg-[#5794F2]/30 border border-[#5794F2] text-[#5794F2] rounded text-xs transition-colors"
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            )}

            {/* Show confidence if available */}
            {message.response?.confidence && (
              <div className="mt-2 text-xs text-gray-500">
                Confidence: {(message.response.confidence * 100).toFixed(0)}%
              </div>
            )}
          </div>
          <div className="text-[10px] text-gray-600 mt-1">
            {message.timestamp.toLocaleTimeString()}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-2xl flex flex-col h-full font-mono text-xs">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-900/50 to-pink-900/50 px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="relative">
            <TerminalIcon className="w-4 h-4 text-purple-400" />
            <div className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          </div>
          <span className="text-purple-300 font-semibold">AI Terminal Assistant</span>
          <span className="text-[10px] text-gray-500 ml-2">Powered by NLP</span>
        </div>
        <div className="flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500/20 border border-red-500"></div>
          <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/20 border border-yellow-500"></div>
          <div className="w-2.5 h-2.5 rounded-full bg-green-500 border border-green-600 shadow-lg shadow-green-500/50"></div>
        </div>
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 p-4 overflow-y-auto custom-scrollbar bg-black/50"
      >
        {messages.map(renderMessage)}

        {/* Typing indicator */}
        {isProcessing && (
          <div className="flex gap-3 mb-4">
            <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white animate-pulse" />
            </div>
            <div className="bg-[#1a1d23] border border-[#2a2d33] rounded-lg px-4 py-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="px-4 py-2 border-t border-slate-800 bg-slate-900/50">
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => handleQuickAction("What's the best opportunity now?")}
            className="flex items-center gap-1 px-2 py-1 bg-slate-800 hover:bg-slate-700 rounded text-[10px] text-gray-400 hover:text-white transition-colors"
          >
            <TrendingUp className="w-3 h-3" />
            Opportunities
          </button>
          <button
            onClick={() => handleQuickAction("How am I doing today?")}
            className="flex items-center gap-1 px-2 py-1 bg-slate-800 hover:bg-slate-700 rounded text-[10px] text-gray-400 hover:text-white transition-colors"
          >
            <BarChart3 className="w-3 h-3" />
            Performance
          </button>
          <button
            onClick={() => handleQuickAction("Give me a strategy tip")}
            className="flex items-center gap-1 px-2 py-1 bg-slate-800 hover:bg-slate-700 rounded text-[10px] text-gray-400 hover:text-white transition-colors"
          >
            <Lightbulb className="w-3 h-3" />
            Tips
          </button>
        </div>
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-slate-800 bg-slate-900">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me anything... (e.g., 'What's the best trade now?')"
            className="flex-1 bg-black border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-purple-500 transition-colors"
            disabled={isProcessing}
          />
          <button
            type="submit"
            disabled={!input.trim() || isProcessing}
            className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed rounded-lg transition-all flex items-center gap-2 text-white font-semibold"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
};

export default Terminal;
