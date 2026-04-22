import { useState } from "react";
import { CropHealthPanel } from "./components/CropHealthPanel";
import { CropSuitabilityAgentPanel } from "./components/CropSuitabilityAgentPanel";
import { FarmAdvisorPanel } from "./components/FarmAdvisorPanel";
import { MarketPricesPanel } from "./components/MarketPricesPanel";
import { MultiAgentPlanPanel } from "./components/MultiAgentPlanPanel";
import { OverviewDashboard } from "./components/OverviewDashboard";

type NavKey =
  | "overview"
  | "suitability"
  | "market"
  | "health"
  | "multi"
  | "advisor";

type NavItem = {
  key: NavKey;
  label: string;
  hint: string;
  icon: string;
};

const NAV: NavItem[] = [
  { key: "overview", label: "Overview", hint: "Farm dashboard", icon: "▦" },
  {
    key: "suitability",
    label: "Crop Suitability",
    hint: "Yield & conditions",
    icon: "✦",
  },
  {
    key: "market",
    label: "Market Intelligence",
    hint: "Price & timing",
    icon: "$",
  },
  {
    key: "health",
    label: "Crop Health",
    hint: "Disease monitoring",
    icon: "✚",
  },
  { key: "multi", label: "Season Plan", hint: "Orchestrator", icon: "⋈" },
  { key: "advisor", label: "Ask FarmWise", hint: "Conversational", icon: "◐" },
];

export default function App() {
  const [nav, setNav] = useState<NavKey>("overview");

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Main navigation">
        <div className="sidebar__brand">
          <span className="sidebar__logo" aria-hidden>
            🌾
          </span>
          <div>
            <div className="sidebar__name">FarmWise AI</div>
            <div className="sidebar__tag">Decisions for small farms</div>
          </div>
        </div>

        <nav className="sidebar__nav" aria-label="Primary">
          {NAV.map((item) => (
            <button
              key={item.key}
              type="button"
              className={`nav-btn ${nav === item.key ? "nav-btn--active" : ""}`}
              onClick={() => setNav(item.key)}
            >
              <span className="nav-btn__icon" aria-hidden>
                {item.icon}
              </span>
              <span className="nav-btn__text">
                <span className="nav-btn__label">{item.label}</span>
                <span className="nav-btn__hint">{item.hint}</span>
              </span>
            </button>
          ))}
        </nav>

      </aside>

      <main className="main">
        {nav === "overview" ? (
          <OverviewDashboard onNavigate={(k) => setNav(k)} />
        ) : nav === "suitability" ? (
          <CropSuitabilityAgentPanel />
        ) : nav === "market" ? (
          <MarketPricesPanel />
        ) : nav === "health" ? (
          <CropHealthPanel />
        ) : nav === "multi" ? (
          <MultiAgentPlanPanel />
        ) : (
          <FarmAdvisorPanel />
        )}
      </main>
    </div>
  );
}
