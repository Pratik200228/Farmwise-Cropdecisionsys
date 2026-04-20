import { useEffect, useRef, useState, type FormEvent } from "react";
import { useFarmAdvisor } from "../hooks/useFarmAdvisor";
import { defaultFarmContext } from "../types/farm";
import { FarmContextForm } from "./FarmContextForm";
import { RichText } from "./RichText";

const SUGGESTIONS = [
  "What should I grow this season given my soil and goals?",
  "How do I time selling maize with market trends?",
  "My tomato leaves have yellow spots — what should I check first?",
  "How should I interpret soil moisture for irrigation this week?",
];

export function FarmAdvisorPanel() {
  const {
    context,
    setContext,
    messages,
    send,
    pending,
    error,
    clearThread,
  } = useFarmAdvisor(defaultFarmContext());
  const [draft, setDraft] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pending]);

  const commitSend = () => {
    void send(draft);
    setDraft("");
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    commitSend();
  };

  return (
    <div className="advisor-layout">
      <section className="advisor-chat card" aria-label="Farm advisor chat">
        <header className="advisor-chat__head">
          <div>
            <h1 className="advisor-chat__title">FarmWise assistant</h1>
            <p className="advisor-chat__sub">
              Context-aware assistant for the crop suitability workflow and connected services
            </p>
          </div>
          <button
            type="button"
            className="btn btn--ghost"
            onClick={() => clearThread()}
            disabled={pending}
          >
            Clear chat
          </button>
        </header>

        <div className="advisor-chat__messages" role="log" aria-live="polite">
          {messages.map((m) => (
            <article
              key={m.id}
              className={`bubble bubble--${m.role}`}
              aria-label={m.role === "user" ? "You" : "Advisor"}
            >
              {m.role === "assistant" ? (
                <RichText text={m.content} />
              ) : (
                <p className="bubble__plain">{m.content}</p>
              )}
            </article>
          ))}
          {pending ? (
            <div className="bubble bubble--assistant bubble--typing" aria-busy>
              <span className="dot" />
              <span className="dot" />
              <span className="dot" />
            </div>
          ) : null}
          <div ref={endRef} />
        </div>

        {error ? (
          <p className="advisor-chat__error" role="status">
            {error}
          </p>
        ) : null}

        <div className="suggestions" aria-label="Suggested questions">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              type="button"
              className="suggestion-chip"
              disabled={pending}
              onClick={() => void send(s)}
            >
              {s}
            </button>
          ))}
        </div>

        <form className="composer" onSubmit={onSubmit}>
          <label className="sr-only" htmlFor="advisor-input">
            Message to farm advisor
          </label>
          <textarea
            id="advisor-input"
            className="composer__input"
            rows={2}
            placeholder="Ask about crops, markets, soil moisture, or plant health…"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                commitSend();
              }
            }}
            disabled={pending}
          />
          <button
            type="submit"
            className="btn btn--primary"
            disabled={pending || !draft.trim()}
          >
            Send
          </button>
        </form>
      </section>

      <aside className="advisor-side">
        <div className="card farm-context-card">
          <FarmContextForm value={context} onChange={setContext} />
        </div>
        <div className="card dev-hint">
          <h3 className="dev-hint__title">Wire-up</h3>
          <ul className="dev-hint__list">
            <li>
              Backend: implement <code>POST /api/v1/farm-advisor/chat</code>{" "}
              accepting <code>messages</code> + <code>context</code>.
            </li>
            <li>
              Dev proxy: Vite forwards <code>/api</code> to{" "}
              <code>localhost:8000</code>.
            </li>
            <li>
              Demo: set <code>VITE_USE_MOCK_AI=true</code> in{" "}
              <code>.env.local</code>.
            </li>
          </ul>
        </div>
      </aside>
    </div>
  );
}
