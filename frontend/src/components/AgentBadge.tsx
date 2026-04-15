export type AgentType =
  | "goal-based"
  | "utility-based"
  | "model-based"
  | "orchestrator"
  | "conversational";

type Props = {
  name: string;
  type: AgentType;
  role: string;
  accent: "suit" | "market" | "health" | "multi" | "chat";
};

const TYPE_LABEL: Record<AgentType, string> = {
  "goal-based": "Goal-based agent",
  "utility-based": "Utility-based agent",
  "model-based": "Model-based reflex agent",
  orchestrator: "Orchestrator",
  conversational: "Conversational agent",
};

export function AgentBadge({ name, type, role, accent }: Props) {
  return (
    <aside className={`agent-badge agent-badge--${accent}`} aria-label="Agent profile">
      <span className="agent-badge__kicker">{name}</span>
      <strong className="agent-badge__type">{TYPE_LABEL[type]}</strong>
      <span className="agent-badge__role">{role}</span>
    </aside>
  );
}
