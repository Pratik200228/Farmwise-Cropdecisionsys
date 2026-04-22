type Props = {
  name: string;
  type: string;
  role: string;
  accent: "suit" | "market" | "health" | "multi" | "chat";
};

export function AgentBadge({ name, type, role, accent }: Props) {
  return (
    <aside className={`agent-badge agent-badge--${accent}`} aria-label="Profile">
      <span className="agent-badge__kicker">{name}</span>
      <strong className="agent-badge__type">{type}</strong>
      <span className="agent-badge__role">{role}</span>
    </aside>
  );
}
