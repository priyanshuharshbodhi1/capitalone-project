import React, { useState, useRef, useEffect } from 'react';
import { 
  MessageSquare, 
  Send, 
  Loader2, 
  Bot, 
  User, 
  Sparkles
} from 'lucide-react';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

const Chatbot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Hello! I\'m your Shetkari farming assistant. How can I help you today?',
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const hasUserMessage = messages.some(m => m.sender === 'user');

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const generateResponse = async (): Promise<string> => {
    // This is a mock function that would be replaced with actual API call
    setIsLoading(true);
    
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const responses = [
      `Based on your soil moisture levels, I recommend watering your crops in the next 24 hours.`,
      `The temperature is optimal for crop growth. No action needed at this time.`,
      `Your soil nitrogen levels are low. Consider applying fertilizer within the next week.`,
      `The humidity levels suggest potential for fungal growth. Consider preventative treatment.`,
      `Based on your sensor data, crop conditions are optimal. Keep monitoring for changes.`,
      `I've analyzed your data and everything looks good. Your farm is operating efficiently.`,
    ];
    
    // For demo purposes, pick a random response
    const response = responses[Math.floor(Math.random() * responses.length)];
    setIsLoading(false);
    return response;
  };

  const handleSend = async () => {
    if (input.trim() === '') return;

    const userMessage = {
      id: Date.now().toString(),
      text: input,
      sender: 'user' as const,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');

    // Generate bot response
    try {
      const botResponse = await generateResponse();
      const botMessage = {
        id: (Date.now() + 1).toString(),
        text: botResponse,
        sender: 'bot' as const,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error generating response:', error);
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        text: 'Sorry, I encountered an error processing your request.',
        sender: 'bot' as const,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-4 sm:py-8">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Enhanced Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 sm:mb-8 space-y-4 sm:space-y-0">
          <div className="flex items-center space-x-3 sm:space-x-4">
            <div className="bg-gradient-to-br from-emerald-500 to-emerald-600 p-2 sm:p-3 rounded-xl sm:rounded-2xl shadow-lg">
              <MessageSquare className="h-6 w-6 sm:h-8 sm:w-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                Shetkari Assistant
              </h1>
              <p className="text-gray-600 mt-1 flex items-center text-sm sm:text-base">
                <Sparkles className="h-3 w-3 sm:h-4 sm:w-4 mr-1 text-emerald-500" />
                AI-powered farming recommendations
              </p>
            </div>
          </div>
        </div>

        {/* Chat Area */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 mb-4 overflow-hidden flex flex-col" style={{ minHeight: '70vh', maxHeight: '70vh' }}>
          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6">
            {messages.map((message) => (
              <div 
                key={message.id} 
                className={`mb-4 flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div 
                  className={`flex max-w-[80%] md:max-w-[70%] rounded-2xl px-4 py-3 ${
                    message.sender === 'user' 
                      ? 'bg-emerald-600 text-white' 
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  <div className={`mr-2 mt-1 ${message.sender === 'user' ? 'text-white' : 'text-emerald-600'}`}>
                    {message.sender === 'user' ? (
                      <User className="h-5 w-5" />
                    ) : (
                      <Bot className="h-5 w-5" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center mb-1">
                      <span className="font-medium">
                        {message.sender === 'user' ? 'You' : 'Shetkari Assistant'}
                      </span>
                      <span className={`text-xs ml-2 ${message.sender === 'user' ? 'text-emerald-200' : 'text-gray-500'}`}>
                        {formatTime(message.timestamp)}
                      </span>
                    </div>
                    <p className="text-sm sm:text-base whitespace-pre-wrap">{message.text}</p>
                  </div>
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex justify-start mb-4">
                <div className="bg-gray-100 rounded-2xl px-4 py-3 max-w-[80%] md:max-w-[70%]">
                  <div className="flex items-center">
                    <Bot className="h-5 w-5 text-emerald-600 mr-2" />
                    <Loader2 className="h-4 w-4 animate-spin text-emerald-600" />
                    <span className="ml-2 text-sm text-gray-500">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
          {/* Inline suggestions inside chat card (show only until first user message) */}
          {!hasUserMessage && (
            <div className="border-t border-gray-100 px-4 sm:px-6 py-3 bg-white">
              <h3 className="text-sm font-semibold text-gray-800 mb-2">Suggested Questions</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                {[
                  'How should I optimize irrigation?',
                  'When is the best time to apply fertilizer?',
                  "What's the optimal soil pH for my crops?",
                  'How can I prevent common plant diseases?',
                  'What crops are suitable for my current conditions?',
                  'How can I improve my soil quality?'
                ].map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      setInput(suggestion);
                      // Immediately send as first user query
                      setTimeout(() => handleSend(), 0);
                    }}
                    className="bg-gray-50 hover:bg-gray-100 text-gray-800 text-xs sm:text-sm px-3 py-2 rounded-lg transition-colors text-left"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}
          
          {/* Input Area */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex items-center space-x-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message here..."
                className="flex-1 bg-gray-50 border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
              />
              <button
                onClick={handleSend}
                disabled={input.trim() === '' || isLoading}
                className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:opacity-50 transition-colors"
              >
                {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
              </button>
            </div>
          </div>
        </div>
        
        {/* Suggestions moved inside chat card above input and auto-hidden after first user message */}
      </div>
    </div>
  );
};

export default Chatbot;
