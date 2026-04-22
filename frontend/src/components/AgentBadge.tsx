export type AgentType =
  | "goal-based"
  | "api-service"
  | "integration"
  | "assistant";

type Props = {
  name: string;
  type: AgentType;
  role: string;
  accent: "suit" | "market" | "health" | "multi" | "chat";
};

const TYPE_LABEL: Record<AgentType, string> = {
  "goal-based": "Goal-based agent",
  "api-service": "External API service",
  integration: "Integrated workflow",
  assistant: "Decision-support assistant",
};

export function AgentBadge({ name, type, role, accent }: Props) {
  return (
    <aside className={`agent-badge agent-badge--${accent}`} aria-label="Profile">
      <span className="agent-badge__kicker">{name}</span>
      <strong className="agent-badge__type">{TYPE_LABEL[type]}</strong>
      <span className="agent-badge__role">{role}</span>
    </aside>
  );
}
