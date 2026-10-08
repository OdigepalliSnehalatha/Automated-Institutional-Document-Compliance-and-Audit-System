import React, { useState, useEffect, useRef } from "react";
import api from "../api";

function AiAssistantModal({ user, isOpen, onClose, onOpen }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [minimized, setMinimized] = useState(false);
  const [quickInput, setQuickInput] = useState("");
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

    if (!isOpen) {
      onOpen();
    }
    setMinimized(false);

    const userMsg = {
      id: Date.now().toString(),
      role: "user",
      content: text.trim(),
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage("");
    setQuickInput("");
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
      {/* 1. DOCKED WIDGET AT BOTTOM RIGHT (When chat is closed or minimized) */}
      {!isOpen && (
        <div className="ai-dock-widget">
          {/* Picture Type Illusion */}
          <div
            className="ai-illusion-avatar-wrapper"
            onClick={onOpen}
            title="Click to open AI Assistant chat"
          >
            <div className="ai-illusion-bubble">
              ✨ Ask AI Assistant
            </div>
            <div className="ai-illusion-character">
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2 2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z"/>
                <rect x="4" y="8" width="16" height="12" rx="4"/>
                <circle cx="9" cy="13" r="1.5" fill="#ffffff"/>
                <circle cx="15" cy="13" r="1.5" fill="#ffffff"/>
                <path d="M9 17h6"/>
              </svg>
              <span
                style={{
                  position: "absolute",
                  bottom: "1px",
                  right: "1px",
                  width: "10px",
                  height: "10px",
                  borderRadius: "50%",
                  background: "#22c55e",
                  border: "2px solid #ffffff",
                }}
              />
            </div>
          </div>

          {/* Below that: Rectangle Bar to Chat */}
          <form
            className="ai-rectangle-chat-bar"
            onSubmit={(e) => {
              e.preventDefault();
              if (quickInput.trim()) {
                handleSendMessage(quickInput.trim());
              } else {
                onOpen();
              }
            }}
          >
            <span style={{ fontSize: "15px", marginRight: "6px" }}>💬</span>
            <input
              type="text"
              className="ai-rectangle-input"
              placeholder={`Ask AI as ${user?.role || "User"}...`}
              value={quickInput}
              onChange={(e) => setQuickInput(e.target.value)}
              onClick={() => {
                if (!isOpen) onOpen();
              }}
            />
            <button type="submit" className="ai-rectangle-send-btn">
              Chat ➤
            </button>
          </form>
        </div>
      )}

      {/* 2. EXPANDED CONVERSATION WINDOW AT BOTTOM RIGHT */}
      {isOpen && (
        <div
          className={`ai-chat-window ${minimized ? "minimized" : ""}`}
          style={{
            position: "fixed",
            bottom: "24px",
            right: "24px",
            zIndex: 9999,
          }}
        >
          {/* Header with Picture Illusion Character */}
          <div className="ai-chat-header">
            <div className="ai-chat-header-info">
              <div className="ai-illusion-character" style={{ width: "38px", height: "38px" }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2 2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z"/>
                  <rect x="4" y="8" width="16" height="12" rx="4"/>
                  <circle cx="9" cy="13" r="1.5" fill="#ffffff"/>
                  <circle cx="15" cy="13" r="1.5" fill="#ffffff"/>
                  <path d="M9 17h6"/>
                </svg>
              </div>
              <div>
                <h3 className="ai-chat-title">AI Compliance Assistant</h3>
                <span className="ai-chat-role-badge">
                  {user?.role} Mode • Live Database
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
                <span className="suggestions-label">Suggested Prompts:</span>
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

              {/* Rectangle Bar to Chat (at Bottom) */}
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
