import { useState } from "react";
import { CropHealthPanel } from "./components/CropHealthPanel";
import { CropSuitabilityAgentPanel } from "./components/CropSuitabilityAgentPanel";
import { FarmAdvisorPanel } from "./components/FarmAdvisorPanel";
import { MarketPricesPanel } from "./components/MarketPricesPanel";
import { OverviewDashboard } from "./components/OverviewDashboard";

type NavKey = "overview" | "suitability" | "market" | "health" | "advisor";

type NavItem = {
  key: NavKey;
  label: string;
  hint: string;
  icon: string;
};

const NAV: NavItem[] = [
  { key: "overview", label: "Overview", hint: "Today's snapshot", icon: "▦" },
  {
    key: "suitability",
    label: "Crop Suitability",
    hint: "AI agent",
    icon: "✦",
  },
  { key: "market", label: "Market Prices", hint: "API", icon: "$" },
  { key: "health", label: "Crop Health", hint: "API", icon: "✚" },
  { key: "advisor", label: "Ask FarmWise", hint: "Chat", icon: "◐" },
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

        <footer className="sidebar__foot">
          <div className="sidebar__status">
            <span className="sidebar__dot" aria-hidden />
            <span>Demo mode · mock APIs</span>
          </div>
          <p>
            1 AI agent (Suitability) + 2 APIs (Market, Health) + a farmer-facing
            chat.
          </p>
        </footer>
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
        ) : (
          <FarmAdvisorPanel />
        )}
      </main>
    </div>
  );
}
