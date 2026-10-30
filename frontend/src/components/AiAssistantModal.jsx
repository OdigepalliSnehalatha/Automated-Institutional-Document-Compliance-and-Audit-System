import React, { useState, useEffect, useRef } from "react";
import api from "../api";

function AiAssistantModal({ user, isOpen, onClose, onOpen }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [minimized, setMinimized] = useState(false);
  const messagesEndRef = useRef(null);

  // Role-specific curated prompts reflecting the ALITS academic system
  const roleSuggestions = {
    Admin: [
      "Show institutional compliance summary",
      "List all 9 engineering branches",
      "Explain the Boolean compliance policy",
      "Show registered faculty & HOD directory",
    ],
    Faculty: [
      "Explain Mid-1 and Mid-2 (R-24) format rules",
      "Explain Resume standard requirements (10 points)",
      "List JNTUK curricula & branch subjects",
      "Why was my document rejected?",
    ],
    HOD: [
      "Show my department submission status",
      "Explain R-24 Mid examination requirements",
      "Which faculty documents are pending approval?",
      "How are compliant documents downloaded?",
    ],
    Auditor: [
      "Explain the 100% Boolean compliance engine",
      "What format presets are available in Builder?",
      "Explain Resume 10-point standard requirements",
      "Which documents currently need review?",
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
    const dept = u.department_name ? ` (${u.department_name})` : "";
    return `Welcome **${name}**${dept}! I am your **ALITS Academic Compliance Copilot**.\n\nI am configured with **Autonomous Regulations (R-24)**, **JNTUK all-branch curricula (1-1 to 4-2 Semesters)**, **Resume Standard Verification (10 Points)**, and the **100% Boolean Decision Engine**.\n\nHow can I assist you with your institutional documentation today?`;
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

  // Convert simple markdown bullets & bold to rendered elements
  const renderFormattedContent = (content) => {
    const lines = content.split("\n");
    return lines.map((line, i) => {
      const boldRegex = /\*\*(.*?)\*\*/g;
      const parts = [];
      let lastIndex = 0;
      let match;

      while ((match = boldRegex.exec(line)) !== null) {
        if (match.index > lastIndex) {
          parts.push(line.substring(lastIndex, match.index));
        }
        parts.push(<strong key={match.index} style={{ color: "#0f172a", fontWeight: 700 }}>{match[1]}</strong>);
        lastIndex = match.index + match[0].length;
      }
      if (lastIndex < line.length) {
        parts.push(line.substring(lastIndex));
      }

      const isBullet = line.trim().startsWith("•") || line.trim().startsWith("-");
      const isHeader = line.trim().startsWith("###") || line.trim().startsWith("##");

      return (
        <p
          key={i}
          style={{
            margin: "0 0 6px 0",
            paddingLeft: isBullet ? "12px" : "0",
            lineHeight: "1.55",
            fontSize: isHeader ? "14px" : "13px",
            fontWeight: isHeader ? 700 : 400,
            color: "#334155"
          }}
        >
          {parts.length > 0 ? parts : line}
        </p>
      );
    });
  };

  return (
    <>
      {/* 1. FLOATING EXECUTIVE TRIGGER PILL (When closed) */}
      {!isOpen && (
        <div className="alits-copilot-dock">
          <button
            type="button"
            className="alits-copilot-pill"
            onClick={onOpen}
            title="Open ALITS Institutional Compliance Copilot"
          >
            {/* Elegant Institutional Emblem */}
            <div className="alits-copilot-emblem">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L3 7V12C3 17.52 6.84 22.74 12 24C17.16 22.74 21 17.52 21 12V7L12 2Z" fill="url(#crestGrad)" />
                <path d="M12 6L13.8 10.4L18 11.2L14.7 14.1L15.7 18.5L12 16.2L8.3 18.5L9.3 14.1L6 11.2L10.2 10.4L12 6Z" fill="#FDE047" />
                <defs>
                  <linearGradient id="crestGrad" x1="3" y1="2" x2="21" y2="24" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#1E3A8A" />
                    <stop offset="1" stopColor="#0284C7" />
                  </linearGradient>
                </defs>
              </svg>
              <span className="alits-pulse-dot" />
            </div>

            <div className="alits-copilot-labels">
              <span className="alits-copilot-name">ALITS Compliance Copilot</span>
              <span className="alits-copilot-status">Institutional Advisor • R-24</span>
            </div>

            <span className="alits-sparkle-icon">✨</span>
          </button>
        </div>
      )}

      {/* 2. EXPANDED CONVERSATION WINDOW */}
      {isOpen && (
        <div className={`alits-copilot-window ${minimized ? "minimized" : ""}`}>
          {/* Executive Institutional Header */}
          <div className="alits-copilot-header">
            <div className="alits-header-main">
              <div className="alits-header-emblem">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2L3 7V12C3 17.52 6.84 22.74 12 24C17.16 22.74 21 17.52 21 12V7L12 2Z" fill="url(#crestGradHead)" />
                  <path d="M12 6L13.8 10.4L18 11.2L14.7 14.1L15.7 18.5L12 16.2L8.3 18.5L9.3 14.1L6 11.2L10.2 10.4L12 6Z" fill="#FDE047" />
                  <defs>
                    <linearGradient id="crestGradHead" x1="3" y1="2" x2="21" y2="24" gradientUnits="userSpaceOnUse">
                      <stop stopColor="#2563EB" />
                      <stop offset="1" stopColor="#38BDF8" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>

              <div>
                <h3 className="alits-window-title">ALITS Compliance Copilot</h3>
                <div className="alits-window-badges">
                  <span className="alits-status-badge">● Online</span>
                  <span className="alits-scope-badge">{user?.role} Portal</span>
                  <span className="alits-scope-badge">R-24 & JNTUK</span>
                </div>
              </div>
            </div>

            <div className="alits-header-actions">
              <button
                type="button"
                className="alits-btn-icon"
                onClick={() => setMinimized(!minimized)}
                title={minimized ? "Expand" : "Minimize"}
              >
                {minimized ? "▢" : "—"}
              </button>
              <button
                type="button"
                className="alits-btn-icon"
                onClick={onClose}
                title="Close Copilot"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Body */}
          {!minimized && (
            <>
              <div className="alits-copilot-body">
                {/* Institutional Notice Card */}
                <div className="alits-intro-card">
                  <div className="alits-intro-icon">🏛️</div>
                  <div>
                    <strong>Anantha Lakshmi Institute Compliance Advisor</strong>
                    <p>Verified with Autonomous Regulations (R-24), JNTUK 1-1 to 4-2 curricula, and 100% Boolean audit rules.</p>
                  </div>
                </div>

                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`alits-message-row ${msg.role === "user" ? "user-row" : "copilot-row"}`}
                  >
                    {msg.role === "assistant" && (
                      <div className="alits-copilot-avatar">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                          <path d="M12 2L4 6V11C4 16.5 7.4 21.6 12 23C16.6 21.6 20 16.5 20 11V6L12 2Z" fill="#1E3A8A"/>
                          <path d="M12 7L13.5 10.5L17 11.2L14.3 13.5L15.1 17L12 15.2L8.9 17L9.7 13.5L7 11.2L10.5 10.5L12 7Z" fill="#FACC15"/>
                        </svg>
                      </div>
                    )}

                    <div
                      className={`alits-bubble ${
                        msg.role === "user" ? "user-bubble" : "copilot-bubble"
                      }`}
                    >
                      {renderFormattedContent(msg.content)}
                      <span className="alits-msg-time">{msg.time}</span>
                    </div>

                    {msg.role === "user" && (
                      <div className="alits-user-avatar">
                        {user?.name ? user.name[0].toUpperCase() : "U"}
                      </div>
                    )}
                  </div>
                ))}

                {loading && (
                  <div className="alits-message-row copilot-row">
                    <div className="alits-copilot-avatar">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                        <path d="M12 2L4 6V11C4 16.5 7.4 21.6 12 23C16.6 21.6 20 16.5 20 11V6L12 2Z" fill="#1E3A8A"/>
                        <path d="M12 7L13.5 10.5L17 11.2L14.3 13.5L15.1 17L12 15.2L8.9 17L9.7 13.5L7 11.2L10.5 10.5L12 7Z" fill="#FACC15"/>
                      </svg>
                    </div>
                    <div className="alits-bubble copilot-bubble alits-typing">
                      <span className="dot"></span>
                      <span className="dot"></span>
                      <span className="dot"></span>
                      <em style={{ fontSize: "11px", color: "#64748b", marginLeft: "6px" }}>Analyzing institutional compliance database...</em>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Recommended Curricular Queries */}
              <div className="alits-copilot-suggestions">
                <span className="alits-suggestions-title">RECOMMENDED COMPLIANCE GUIDANCE:</span>
                <div className="alits-suggestions-scroll">
                  {currentSuggestions.map((sug, idx) => (
                    <button
                      key={idx}
                      type="button"
                      className="alits-suggestion-pill"
                      onClick={() => handleSendMessage(sug)}
                      disabled={loading}
                    >
                      {sug}
                    </button>
                  ))}
                </div>
              </div>

              {/* Message Composer */}
              <form
                className="alits-copilot-footer"
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
              >
                <input
                  type="text"
                  className="alits-copilot-input"
                  placeholder={`Ask about R-24 Mid papers, Resume criteria, JNTUK subjects...`}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  disabled={loading}
                />
                <button
                  type="submit"
                  className="alits-copilot-send"
                  disabled={loading || !inputMessage.trim()}
                  title="Submit Inquiry"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                  </svg>
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
