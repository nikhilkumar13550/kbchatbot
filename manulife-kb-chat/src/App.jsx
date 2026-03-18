import React, { useState, useRef, useEffect } from 'react';
import { Search, Globe, Send, User, Bot, HelpCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown'; // <-- 1. Added Markdown Import
import './App.css';

export default function App() {
  const [messages, setMessages] = useState([
    { 
      id: 1, 
      text: "Hello, welcome to the Advisor Operations Assistant. I can help you with operational processes such as advisor transfers, coverage updates, legal deductions, and deceased case handling. Please enter your query to get step-by-step guidance.", 
      sender: "bot" 
    }
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userText = inputValue;
    const newUserMsg = { id: Date.now(), text: userText, sender: "user" };
    
    setMessages(prev => [...prev, newUserMsg]);
    setInputValue("");
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userText, userId: "nikhil_123" }),
      });

      if (!response.ok) throw new Error("Network error");
      const data = await response.json();
      
      setMessages(prev => [...prev, { id: Date.now() + 1, text: data.answer, sender: "bot" }]);
    } catch (error) {
      setMessages(prev => [...prev, { 
        id: Date.now() + 1, 
        text: "⚠️ Backend is not running! Please start the Python server.", 
        sender: "bot" 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-layout">
      <header className="top-header">
        <div className="brand-area">
          <img src="/brand-logo.png" alt="Logo" className="brand-logo" />
          <span className="brand-text">Manulife</span>
          <span className="brand-divider">|</span>
          <span className="brand-subtext">John Hancock</span>
        </div>
        <div className="header-actions">
          <Search className="header-icon" size={20} />
          <div className="language-selector">
            <span>EN</span><Globe size={16} />
          </div>
        </div>
      </header>

      <div className="chat-workspace">
        <div className="chat-container">
          <div className="chat-header-internal">
            <HelpCircle size={24} color="#007A33" />
            <h2>Operations Process Assistant (Transfers, Legal deductions, Deceased handling)</h2>
          </div>
          
          <div className="messages-area">
            {messages.map((msg) => (
              <div key={msg.id} className={`message-wrapper ${msg.sender}`}>
                <div className={`avatar ${msg.sender === 'bot' ? 'bot-avatar' : 'user-avatar'}`}>
                  {msg.sender === 'bot' ? <Bot size={20} color="white" /> : <User size={20} color="#4B5563" />}
                </div>
                
                {/* 2. Markdown Wrapper added below */}
                <div className="message-bubble">
                  {msg.sender === 'bot' ? (
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  ) : (
                    msg.text
                  )}
                </div>

              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="input-area">
            <input 
              type="text" 
              className="chat-input" 
              placeholder="Ask your query?" 
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              disabled={isLoading}
            />
            <button className="send-btn" onClick={handleSend} disabled={isLoading}>
              <Send size={18} />
              {isLoading ? 'Thinking...' : 'Send'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}