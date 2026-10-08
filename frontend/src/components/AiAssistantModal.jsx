import React, { useState, useEffect, useRef } from "react";
import api from "../api";

function AiAssistantModal({ user, isOpen, onClose, onOpen }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [minimized, setMinimized] = useState(false);
  const messagesEndRef = useRef(null);

  // Define role-specific suggested questions
  const roleSuggestions = {
    Admin: [
      "Show institution information",
      "How many faculty are registered?",
      "What are the pending activities?",
      "List all engineering branches",
    ],
    Faculty: [
      "What tasks are assigned to me?",
      "Explain question paper requirements",
      "Explain course structure rules",
      "Why was my document rejected?",
    ],
    HOD: [
      "Show my department information",
      "What activities are pending?",
      "How many submissions are accepted?",
      "How to download verified documents?",
    ],
    Auditor: [
      "What is the current audit status?",
      "Which documents need review?",
      "What format presets are available?",
      "Explain the Boolean compliance decision rule",
    ],
  };

  const currentSuggestions = roleSuggestions[user?.role] || roleSuggestions.Faculty;

  // Initialize initial greeting on load or role change
  useEffect(() => {
    if (user) {
      const greeting = getInitialGreeting(user);
      setMessages([
        {
          id: "welcome",
          role: "assistant",
          content: greeting,
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    }
  }, [user]);

  useEffect(() => {
    if (isOpen && !minimized) {
      scrollToBottom();
    }
  }, [messages, isOpen, minimized]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  function getInitialGreeting(u) {
    const name = u.name || u.email.split("@")[0];
    if (u.role === "Admin") {
      return `Hello **${name}**! I am your **Institutional Admin Assistant**.\n\nI can provide executive summaries on registered faculty, department compliance, and overall audit progress across **${u.institution_name || "the institution"}**. How may I help you?`;
    } else if (u.role === "HOD") {
      return `Welcome **${name}**! I am your **Department Audit Assistant** for **${u.department_name || "your department"}**.\n\nI can summarize faculty submissions, show pending audits, and check compliant records for your branch.`;
    } else if (u.role === "Faculty") {
      return `Hello **${name}**! I am your **Faculty Compliance Assistant**.\n\nI can help you format Question Papers, Course Structures, and Question Banks correctly to pass 100% structural compliance on first submission!`;
    } else if (u.role === "Auditor") {
      return `Greetings **${name}**! I am your **Structural Audit Assistant**.\n\nI can assist with format rule definitions, document verification queues, and audit reporting.`;
    }
    return `Hello ${name}! How can I assist you with document compliance today?`;
  }

  const handleSendMessage = async (textToSend) => {
    const text = textToSend || inputMessage;
    if (!text.trim() || loading) return;

    const userMsg = {
      id: Date.now().toString(),
      role: "user",
      content: text.trim(),
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage("");
    setLoading(true);

    try {
      const res = await api.post("/ai/chat", {
        message: text.trim(),
        history: messages.slice(-4).map((m) => ({ role: m.role, content: m.content })),
      });

      const aiMsg = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: res.data.response,
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      const errorMsg = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "I encountered an error retrieving data. Please check your network connection and try again.",
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  // Convert simple markdown bullets & bold to rendered text
  const renderFormattedContent = (content) => {
    const lines = content.split("\n");
    return lines.map((line, i) => {
      // Bold replacement
      let formatted = line;
      const boldRegex = /\*\*(.*?)\*\*/g;
      const parts = [];
      let lastIndex = 0;
      let match;

      while ((match = boldRegex.exec(line)) !== null) {
        if (match.index > lastIndex) {
          parts.push(line.substring(lastIndex, match.index));
        }
        parts.push(<strong key={match.index}>{match[1]}</strong>);
        lastIndex = match.index + match[0].length;
      }
      if (lastIndex < line.length) {
        parts.push(line.substring(lastIndex));
      }

      const isBullet = line.trim().startsWith("•") || line.trim().startsWith("-");
      return (
        <p
          key={i}
          style={{
            margin: "0 0 6px 0",
            paddingLeft: isBullet ? "12px" : "0",
            lineHeight: "1.5",
          }}
        >
          {parts.length > 0 ? parts : line}
        </p>
      );
    });
  };

  return (
    <>
      {/* Floating Action Button (Always available in bottom-right) */}
      {!isOpen && (
        <button
          className="ai-floating-trigger-btn"
          onClick={onOpen}
          title="Open AI Compliance Assistant"
        >
          <span className="ai-fab-icon">🤖</span>
          <span className="ai-fab-label">AI Assistant</span>
          <span className="ai-fab-pulse"></span>
        </button>
      )}

      {/* Floating Chat Modal Window */}
      {isOpen && (
        <div className={`ai-chat-window ${minimized ? "minimized" : ""}`}>
          {/* Header */}
          <div className="ai-chat-header">
            <div className="ai-chat-header-info">
              <div className="ai-chat-avatar">🤖</div>
              <div>
                <h3 className="ai-chat-title">AI Compliance Assistant</h3>
                <span className="ai-chat-role-badge">
                  {user?.role} Assistant • Live Data
                </span>
              </div>
            </div>

            <div className="ai-chat-header-actions">
              <button
                className="ai-header-btn"
                onClick={() => setMinimized(!minimized)}
                title={minimized ? "Expand" : "Minimize"}
              >
                {minimized ? "▢" : "—"}
              </button>
              <button
                className="ai-header-btn"
                onClick={onClose}
                title="Close AI Assistant"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Body */}
          {!minimized && (
            <>
              <div className="ai-chat-body">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`ai-message-row ${msg.role === "user" ? "user-row" : "ai-row"}`}
                  >
                    {msg.role === "assistant" && (
                      <div className="ai-msg-avatar">🤖</div>
                    )}
                    <div
                      className={`ai-message-bubble ${
                        msg.role === "user" ? "user-bubble" : "ai-bubble"
                      }`}
                    >
                      {renderFormattedContent(msg.content)}
                      <span className="ai-msg-time">{msg.time}</span>
                    </div>
                  </div>
                ))}

                {loading && (
                  <div className="ai-message-row ai-row">
                    <div className="ai-msg-avatar">🤖</div>
                    <div className="ai-message-bubble ai-bubble ai-typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Suggested Questions Chips */}
              <div className="ai-chat-suggestions">
                <span className="suggestions-label">Suggestions:</span>
                <div className="suggestions-scroll">
                  {currentSuggestions.map((sug, idx) => (
                    <button
                      key={idx}
                      className="suggestion-chip"
                      onClick={() => handleSendMessage(sug)}
                      disabled={loading}
                    >
                      {sug}
                    </button>
                  ))}
                </div>
              </div>

              {/* Input Footer */}
              <form
                className="ai-chat-footer"
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
              >
                <input
                  type="text"
                  className="ai-chat-input"
                  placeholder={`Ask a question as ${user?.role}...`}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  disabled={loading}
                />
                <button
                  type="submit"
                  className="ai-send-btn"
                  disabled={loading || !inputMessage.trim()}
                  title="Send Question"
                >
                  ➤
                </button>
              </form>
            </>
          )}
        </div>
      )}
    </>
  );
}

export default AiAssistantModal;
