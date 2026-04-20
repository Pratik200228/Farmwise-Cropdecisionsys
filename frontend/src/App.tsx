import { useState } from "react";
import { CropHealthPanel } from "./components/CropHealthPanel";
import { CropSuitabilityAgentPanel } from "./components/CropSuitabilityAgentPanel";
import { FarmAdvisorPanel } from "./components/FarmAdvisorPanel";
import { MarketPricesPanel } from "./components/MarketPricesPanel";
import { MultiAgentPlanPanel } from "./components/MultiAgentPlanPanel";
import { OverviewDashboard } from "./components/OverviewDashboard";
import { isMockAiEnabled } from "./lib/runtimeConfig";

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
  eyebrow: string;
  serial: string;
};

type NavSection = {
  title: string;
  note: string;
  items: NavItem[];
};

const NAV_SECTIONS: NavSection[] = [
  {
    title: "Start Here",
    note: "Open with the calm, high-level read.",
    items: [
      {
        key: "overview",
        serial: "01",
        eyebrow: "Morning brief",
        label: "Home",
        hint: "See crop fit, pricing, and field health in one place.",
      },
      {
        key: "suitability",
        serial: "02",
        eyebrow: "Crop planning",
        label: "Crop Suitability",
        hint: "Check what fits the season before you plant.",
      },
    ],
  },
  {
    title: "Watch The Season",
    note: "Signals worth checking through the week.",
    items: [
      {
        key: "market",
        serial: "03",
        eyebrow: "Selling rhythm",
        label: "Market Outlook",
        hint: "Follow direction, timing windows, and price pressure.",
      },
      {
        key: "health",
        serial: "04",
        eyebrow: "Field checks",
        label: "Crop Health",
        hint: "Review symptoms, risks, and next scouting steps.",
      },
      {
        key: "multi",
        serial: "05",
        eyebrow: "Whole-plan view",
        label: "Season Plan",
        hint: "Pull the major signals into one integrated read.",
      },
    ],
  },
  {
    title: "Talk It Through",
    note: "Use plain language when the tradeoffs feel messy.",
    items: [
      {
        key: "advisor",
        serial: "06",
        eyebrow: "Decision support",
        label: "FarmWise Assistant",
        hint: "Ask questions and get help weighing the next move.",
      },
    ],
  },
];

export default function App() {
  const [nav, setNav] = useState<NavKey>("overview");
  const mockMode = isMockAiEnabled();

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Main navigation">
        <div className="sidebar__brand">
          <span className="sidebar__logo" aria-hidden>
            🌾
          </span>
          <div>
            <div className="sidebar__name">FarmWise</div>
            <div className="sidebar__tag">A working desk for small-farm decisions</div>
          </div>
        </div>

        <div className="sidebar__intro">
          <div className="sidebar__intro-kicker">Field notebook</div>
          <p>
            Move through the app like a real farm check-in: start with the
            brief, then step into planting, prices, and field checks only when
            you need them.
          </p>
        </div>

        <nav className="sidebar__nav" aria-label="Primary">
          {NAV_SECTIONS.map((section) => (
            <section key={section.title} className="sidebar__section">
              <div className="sidebar__section-head">
                <div className="sidebar__section-title">{section.title}</div>
                <div className="sidebar__section-note">{section.note}</div>
              </div>

              <div className="sidebar__section-links">
                {section.items.map((item) => (
                  <button
                    key={item.key}
                    type="button"
                    className={`nav-btn ${nav === item.key ? "nav-btn--active" : ""}`}
                    onClick={() => setNav(item.key)}
                  >
                    <span className="nav-btn__serial" aria-hidden>
                      {item.serial}
                    </span>
                    <span className="nav-btn__text">
                      <span className="nav-btn__eyebrow">{item.eyebrow}</span>
                      <span className="nav-btn__label">{item.label}</span>
                      <span className="nav-btn__hint">{item.hint}</span>
                    </span>
                    <span className="nav-btn__marker" aria-hidden>
                      ↗
                    </span>
                  </button>
                ))}
              </div>
            </section>
          ))}
        </nav>

        <footer className="sidebar__foot">
          <div className="sidebar__status">
            <span className="sidebar__dot" aria-hidden />
            <span>{mockMode ? "Demo mode · browser mocks" : "Backend mode · FastAPI"}</span>
          </div>
          <p>
            Crop suitability leads the decision flow, with market and crop
            health layered in when timing or field risk matters.
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
        ) : nav === "multi" ? (
          <MultiAgentPlanPanel />
        ) : (
          <FarmAdvisorPanel />
        )}
      </main>
    </div>
  );
}
