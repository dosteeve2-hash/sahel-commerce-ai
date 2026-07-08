"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";

const WELCOME = {
  role: "agent",
  text:
    "Salut ! Je suis Sahel, ton assistant commercial. Dis-moi par exemple :\n" +
    "• « montre le stock »\n" +
    "• « vends 2 Savon Citec en orange money »\n" +
    "• « bilan de la semaine »",
};

export default function Chat({ onAction }) {
  const [messages, setMessages] = useState([WELCOME]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setError("");
    setMessages((m) => [...m, { role: "user", text }]);
    setLoading(true);
    try {
      const res = await api.chat(text);
      setMessages((m) => [
        ...m,
        {
          role: "agent",
          text: res.reply,
          tools: res.tools_used,
          demo: res.demo_mode,
        },
      ]);
      // Si l'agent a modifié des données, on rafraîchit le dashboard
      if (res.tools_used?.length && onAction) onAction();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="chat">
      <div className="chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.text}
            {m.tools?.length > 0 && (
              <span className="meta">
                outils : {m.tools.join(", ")}
                {m.demo ? " · mode démo" : ""}
              </span>
            )}
          </div>
        ))}
        {loading && <div className="msg agent">…</div>}
        <div ref={bottomRef} />
      </div>
      {error && <p className="error">{error}</p>}
      <form className="chat-input" onSubmit={send}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Parle à ton assistant…"
          aria-label="Message"
        />
        <button type="submit" disabled={loading}>
          Envoyer
        </button>
      </form>
    </div>
  );
}
