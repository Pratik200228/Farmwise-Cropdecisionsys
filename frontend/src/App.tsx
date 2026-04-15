import { useState } from "react";
import { DashboardPanel } from "./components/DashboardPanel";
import { FarmAdvisorPanel } from "./components/FarmAdvisorPanel";
import { MultiAgentPlanPanel } from "./components/MultiAgentPlanPanel";

type NavKey = "advisor" | "multi" | "dashboard";

export default function App() {
  const [nav, setNav] = useState<NavKey>("advisor");

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Main navigation">
        <div className="sidebar__brand">
          <span className="sidebar__logo" aria-hidden>
            🌾
          </span>
          <div>
            <div className="sidebar__name">FarmWise AI</div>
            <div className="sidebar__tag">Crop decisions</div>
          </div>
        </div>

        <nav className="sidebar__nav">
          <button
            type="button"
            className={`nav-btn ${nav === "advisor" ? "nav-btn--active" : ""}`}
            onClick={() => setNav("advisor")}
          >
            AI advisor
          </button>
          <button
            type="button"
            className={`nav-btn ${nav === "multi" ? "nav-btn--active" : ""}`}
            onClick={() => setNav("multi")}
          >
            3-agent plan
          </button>
          <button
            type="button"
            className={`nav-btn ${nav === "dashboard" ? "nav-btn--active" : ""}`}
            onClick={() => setNav("dashboard")}
          >
            Dashboard
          </button>
        </nav>

        <footer className="sidebar__foot">
          <p>Frontend stack: React + Vite + Recharts</p>
          <a
            className="nav-btn sidebar__invite"
            href="mailto:?subject=Join%20FarmWise%20AI&body=You%20are%20invited%20to%20collaborate%20on%20FarmWise%20AI."
            aria-label="Invite collaborators to FarmWise AI via email"
          >
            Invite
          </a>
        </footer>
      </aside>

      <main className="main">
        {nav === "advisor" ? (
          <FarmAdvisorPanel />
        ) : nav === "multi" ? (
          <MultiAgentPlanPanel />
        ) : (
          <DashboardPanel />
        )}
      </main>
    </div>
  );
}
