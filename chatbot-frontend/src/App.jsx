import { useState, useRef, useEffect } from 'react'
import './App.css'

function App() {
  const [isChatOpen, setIsChatOpen] = useState(false)
  const [messages, setMessages] = useState([
    { id: 1, text: "Hello! I'm your AI assistant. How can I help you today?", isBot: true, timestamp: new Date() }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return

    const userMessage = {
      id: Date.now(),
      text: inputMessage,
      isBot: false,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    const messageToSend = inputMessage // Store the message before clearing
    setInputMessage('')
    setIsTyping(true)
    setIsLoading(true)

    try {
      // ✅ FIX: The backend is a FastAPI app, which expects a POST request to the /chat endpoint.
      // The previous code was sending a GET request to a Streamlit app.
      const apiUrl = 'https://chatbot-assistant-main.onrender.com/chat'; // Use your deployed Render URL

      const response = await fetch(apiUrl, {
        method: 'POST', // Changed to POST to match the FastAPI endpoint
        headers: {
          'Content-Type': 'application/json', // Specify that we are sending a JSON body
        },
        body: JSON.stringify({ message: messageToSend }), // Send the message in a JSON body
      });

      if (response.ok) {
        const data = await response.json();
        
        let botResponseText = "";
        
        if (data.status === 'success') {
          botResponseText = data.response || "I'm sorry, I couldn't process your request. Please try again.";
          console.log('Intent detected:', data.intent);
          console.log('Entities found:', data.entities);
          
          if (data.intent === 'Lead Capture' && 
              (data.entities.name || data.entities.email || data.entities.phone)) {
            console.log('Lead information captured:', data.entities);
          }
        } else {
          botResponseText = "I'm sorry, there was an unexpected response format.";
          console.error('API Error:', data);
        }

        const botResponse = {
          id: Date.now() + 1,
          text: botResponseText,
          isBot: true,
          timestamp: new Date(),
          intent: data.intent,
          entities: data.entities
        };
        setMessages(prev => [...prev, botResponse]);
      } else {
        console.error('HTTP Error:', response.status, response.statusText);
        const botResponse = {
          id: Date.now() + 1,
          text: "I'm sorry, there was an error processing your request. Please try again later.",
          isBot: true,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, botResponse]);
      }
    } catch (error) {
      console.error('Error calling chatbot API:', error);
      const botResponse = {
        id: Date.now() + 1,
        text: "I'm sorry, I'm having trouble connecting to my server. Please check your internet connection and try again.",
        isBot: true,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botResponse]);
    } finally {
      setIsTyping(false);
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleChat = () => {
    setIsChatOpen(!isChatOpen);
    if (!isChatOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };
  

  return (
    <div className="app">
      {/* Main Website Content */}
      <header className="header">
        <nav className="nav">
          <div className="logo">AI ChatBot</div>
          <ul className="nav-links">
            <li><a href="#home">Home</a></li>
            <li><a href="#about">About</a></li>
            <li><a href="#services">Services</a></li>
            <li><a href="#contact">Contact</a></li>
          </ul>
        </nav>
      </header>

      <main className="main-content">
        <section id="home" className="hero">
          <div className="hero-content">
            <h1>Welcome to AI ChatBot Assistant</h1>
            <p>Your intelligent companion for seamless conversations and assistance</p>
            <button className="cta-button">Get Started</button>
          </div>
        </section>

        <section id="about" className="section">
          <h2>About Our AI Assistant</h2>
          <p>Experience the future of customer service with our advanced AI chatbot. Get instant responses, 24/7 support, and personalized assistance for all your needs.</p>
        </section>

        <section id="services" className="section">
          <h2>Our Services</h2>
          <div className="services-grid">
            <div className="service-card">
              <h3>24/7 Support</h3>
              <p>Round-the-clock assistance whenever you need it</p>
            </div>
            <div className="service-card">
              <h3>Instant Responses</h3>
              <p>Get answers to your questions in real-time</p>
            </div>
            <div className="service-card">
              <h3>Smart Learning</h3>
              <p>AI that learns and improves with every interaction</p>
            </div>
          </div>
        </section>

        <section id="contact" className="section">
          <h2>Contact Us</h2>
          <p>Have questions? Our AI assistant is ready to help you right now!</p>
        </section>
      </main>

      {/* Chatbot Component */}
      <div className="chatbot-container">
        {/* Chat Toggle Button */}
        <button 
          className={`chat-toggle ${isChatOpen ? 'active' : ''}`}
          onClick={toggleChat}
          aria-label="Toggle chat"
        >
          {isChatOpen ? (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          ) : (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
          )}
        </button>

        {/* Chat Window */}
        {isChatOpen && (
          <div className="chat-window">
            <div className="chat-header">
              <h3>AI Assistant</h3>
              <button 
                className="close-chat"
                onClick={toggleChat}
                aria-label="Close chat"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>

            <div className="chat-messages">
              {messages.map((message) => (
                <div 
                  key={message.id} 
                  className={`message ${message.isBot ? 'bot' : 'user'}`}
                >
                  <div className="message-content">
                    <p>{message.text}</p>
                    <span className="timestamp">
                      {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="message bot">
                  <div className="message-content">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="chat-input">
              <textarea
                ref={inputRef}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={isLoading ? "Processing..." : "Type your message here..."}
                rows="1"
                disabled={isLoading}
              />
              <button 
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isLoading}
                className="send-button"
              >
                {isLoading ? (
                  <div className="loading-spinner"></div>
                ) : (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22,2 15,22 11,13 2,9"></polygon>
                  </svg>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
