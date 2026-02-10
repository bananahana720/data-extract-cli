import { NavLink, Route, Routes } from "react-router-dom";

import { JobDetailPage } from "./pages/JobDetailPage";
import { JobsPage } from "./pages/JobsPage";
import { NewRunPage } from "./pages/NewRunPage";
import { SessionsPage } from "./pages/SessionsPage";

export default function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Local Analyst Workspace</p>
          <h1>Data Extract Control Room</h1>
        </div>
        <nav>
          <NavLink to="/" end>
            New Run
          </NavLink>
          <NavLink to="/jobs">Jobs</NavLink>
          <NavLink to="/sessions">Sessions</NavLink>
        </nav>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<NewRunPage />} />
          <Route path="/jobs" element={<JobsPage />} />
          <Route path="/jobs/:jobId" element={<JobDetailPage />} />
          <Route path="/sessions" element={<SessionsPage />} />
        </Routes>
      </main>
    </div>
  );
}
