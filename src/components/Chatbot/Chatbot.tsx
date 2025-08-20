import React, { useState, useRef, useEffect } from 'react';
import { 
  MessageSquare, 
  Send, 
  Loader2, 
  Bot, 
  User, 
  Sparkles
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import ReactMarkdown from 'react-markdown';
import remarkBreaks from 'remark-breaks';
import { completeAgent, type ChatMessage } from '../../services/agentApi';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

const Chatbot: React.FC = () => {
  const { t } = useTranslation();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [thinkingText, setThinkingText] = useState('Thinking');
  const agentUrl = import.meta.env.VITE_AGENT_API_URL as string | undefined;
  const agentEnabled = Boolean(agentUrl);
  const [isMobile, setIsMobile] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const hasUserMessage = messages.some(m => m.sender === 'user');
  
  // Initialize greeting message when component mounts or language changes
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([{
        id: '1',
        text: t('assistant.greeting'),
        sender: 'bot',
        timestamp: new Date()
      }]);
    } else {
      // Update greeting message if language changes
      setMessages(prev => prev.map((msg, index) => 
        index === 0 && msg.sender === 'bot' 
          ? { ...msg, text: t('assistant.greeting') }
          : msg
      ));
    }
  }, [t]);
  
  // Location state for weather features
  const [userLocation, setUserLocation] = useState<{lat: number, lon: number} | null>(null);
  const [locationStatus, setLocationStatus] = useState<'requesting' | 'granted' | 'denied' | 'unavailable'>('requesting');
  
  // Auto-request location access on component mount for weather features
  useEffect(() => {
    const requestLocation = () => {
      if (!navigator.geolocation) {
        setLocationStatus('unavailable');
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setUserLocation({ lat: latitude, lon: longitude });
          setLocationStatus('granted');
          console.log('✅ Location access granted:', { lat: latitude, lon: longitude });
        },
        (error) => {
          setLocationStatus('denied');
          console.warn('⚠️ Location access denied:', error.message);
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 300000 // 5 minutes cache
        }
      );
    };

    requestLocation();
  }, []);

  // Check for mobile viewport
  useEffect(() => {
    const checkIsMobile = () => {
      setIsMobile(window.innerWidth < 640);
    };
    
    // Initial check
    checkIsMobile();
    
    // Add listener for window resize
    window.addEventListener('resize', checkIsMobile);
    
    // Cleanup
    return () => window.removeEventListener('resize', checkIsMobile);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Rotate thinking text while loading
  useEffect(() => {
    if (!isLoading) return;
    
    const thinkingStates = ['Thinking', 'Planning', 'Analysing', 'Processing'];
    let currentIndex = 0;
    
    const interval = setInterval(() => {
      currentIndex = (currentIndex + 1) % thinkingStates.length;
      setThinkingText(thinkingStates[currentIndex]);
    }, 1000);
    
    return () => clearInterval(interval);
  }, [isLoading]);

  const generateResponse = async (): Promise<string> => {
    // Fallback local mock if backend agent is not configured
    if (!agentEnabled) {
      setIsLoading(true);
      await new Promise(resolve => setTimeout(resolve, 800));
      const responses = [
        `Based on nearby forecasts, conditions look stable.`,
        `Market prices show moderate volatility this week.`,
      ];
      const response = responses[Math.floor(Math.random() * responses.length)];
      setIsLoading(false);
      return response;
    }

    // When agent backend is available, we will stream tokens and return final text
    return new Promise<string>((resolve, reject) => {
      (async () => {
        try {
          setIsLoading(true);
          // Prepare message history for backend
          const history: ChatMessage[] = messages.map(m => ({ role: m.sender === 'bot' ? 'assistant' : 'user', content: m.text }));
          // Include location data in context for weather features
          const context = { 
            session_id: 'web-' + Date.now(),
            locale: 'en-IN',
            location_status: locationStatus,
            ...(userLocation && { lat: userLocation.lat, lon: userLocation.lon })
          }

          const payload = {
            messages: [...history, { role: 'user' as const, content: input }],
            context
          };

          // Create a placeholder assistant message to stream into
          let streamed = '';
          const placeholderId = (Date.now() + 2).toString();
          
          // Get complete response
          const response = await completeAgent<{ text: string }>(`${agentUrl}/agent/complete`, payload);
          streamed = response?.text || 'No response received';
          
          // Add final response
          setMessages(prev => [...prev, { id: placeholderId, text: streamed, sender: 'bot', timestamp: new Date() }]);

          setIsLoading(false);
          resolve(streamed || '');
        } catch (err) {
          setIsLoading(false);
          const friendly = 'Sorry, I could not fetch a response. Please try again.';
          // Add error message
          setMessages(prev => [...prev, { id: (Date.now()).toString(), text: friendly, sender: 'bot' as const, timestamp: new Date() }]);
          reject(err);
        }
      })();
    });
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
      if (!agentEnabled) {
        const botMessage = {
          id: (Date.now() + 1).toString(),
          text: botResponse,
          sender: 'bot' as const,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, botMessage]);
      }
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
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 flex flex-col flex-grow py-4 sm:py-8">
        {/* Enhanced Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 sm:mb-8 space-y-4 sm:space-y-0">
          <div className="flex items-center space-x-3 sm:space-x-4">
            <div className="bg-gradient-to-br from-emerald-500 to-emerald-600 p-2 sm:p-3 rounded-xl sm:rounded-2xl shadow-lg">
              <MessageSquare className="h-6 w-6 sm:h-8 sm:w-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                {t('assistant.title')}
              </h1>
              <p className="text-gray-600 mt-1 flex items-center text-sm sm:text-base">
                <Sparkles className="h-3 w-3 sm:h-4 sm:w-4 mr-1 text-emerald-500" />
                {t('assistant.subtitle')}
              </p>
            </div>
          </div>
        </div>

        {/* Chat Area */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 flex flex-col flex-grow overflow-hidden">
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
                        {message.sender === 'user' ? 'You' : t('assistant.title')}
                      </span>
                      <span className={`text-xs ml-2 ${message.sender === 'user' ? 'text-emerald-200' : 'text-gray-500'}`}>
                        {formatTime(message.timestamp)}
                      </span>
                    </div>
                    {message.sender === 'bot' ? (
                      <div className="text-sm sm:text-base prose prose-sm max-w-none prose-gray">
                        <ReactMarkdown 
                          components={{
                            p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                            strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
                            em: ({ children }) => <em className="italic">{children}</em>,
                            ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                            ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                            li: ({ children }) => <li className="text-sm">{children}</li>,
                            h1: ({ children }) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
                            h2: ({ children }) => <h2 className="text-base font-semibold mb-2">{children}</h2>,
                            h3: ({ children }) => <h3 className="text-sm font-medium mb-1">{children}</h3>,
                            code: ({ children }) => <code className="bg-gray-100 px-1 py-0.5 rounded text-xs font-mono">{children}</code>,
                            blockquote: ({ children }) => <blockquote className="border-l-4 border-gray-300 pl-3 italic">{children}</blockquote>,
                            br: () => <br />
                          }}
                          remarkPlugins={[remarkBreaks]}
                          rehypePlugins={[]}
                        >
                          {message.text}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <p className="text-sm sm:text-base whitespace-pre-wrap">{message.text}</p>
                    )}
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
                    <span className="ml-2 text-sm text-gray-500">{thinkingText}...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
          {/* Inline suggestions inside chat card (show only until first user message) */}
          {!hasUserMessage && (
            <div className="border-t border-gray-100 px-4 sm:px-6 py-3 bg-white">
              <h3 className="text-sm font-semibold text-gray-800 mb-2">{t('assistant.suggestedQuestions')}</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                {
                  [
                  t('assistant.govtPoliciesDripIrrigation'),
                  t('assistant.weatherNext2Weeks'),
                  t('assistant.preventPlantDiseases'),
                  t('assistant.bestTimeForFertilizer')
                  ]
                  // Show only first 3 questions on mobile
                  .filter((_, idx) => !isMobile || idx < 3)
                  .map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      setInput(suggestion);
                    }}
                    onDoubleClick={() => {
                      setInput(suggestion);
                      setTimeout(() => handleSend(), 0);
                    }}
                    className="bg-gray-50 hover:bg-gray-100 text-gray-800 text-xs sm:text-sm px-3 py-2 rounded-lg transition-colors text-left"
                    title="Single click to add to message box, double click to send"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}
          
          {/* Input Area - Fixed to bottom */}
          <div className="sticky bottom-0 bg-white border-t border-gray-200 p-4">
            <div className="flex items-end space-x-2">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={t('assistant.typeMessage')}
                rows={1}
                className="flex-1 bg-gray-50 border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors resize-none overflow-hidden min-h-[48px] max-h-32"
                style={{
                  height: 'auto',
                  minHeight: '48px'
                }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = 'auto';
                  target.style.height = Math.min(target.scrollHeight, 128) + 'px';
                }}
              />
              <button
                onClick={handleSend}
                disabled={input.trim() === '' || isLoading}
                className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:opacity-50 transition-colors self-end"
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
