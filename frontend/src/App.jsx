import React, { useEffect, useState } from 'react';
import { api } from './api/client';
import ProjectAssessment from './components/ProjectAssessment';
import BatchUpload from './components/BatchUpload';
import RuleBook from './components/RuleBook';
import OSSStudy from './components/OSSStudy';
import EraShift from './components/EraShift';
import Calibration from './components/Calibration';

const TABS = [
  { id: 'assess', label: 'Assess' },
  { id: 'batch',  label: 'Batch' },
  { id: 'study',  label: 'OSS Study' },
  { id: 'era',    label: 'Era Shift' },
  { id: 'calib',  label: 'Calibration' },
  { id: 'rules',  label: 'Rule Base' },
];

export default function App() {
  const [tab, setTab]       = useState('assess');
  const [curves, setCurves] = useState(null);
  const [bootError, setBootError] = useState(null);

  // Pre-fetch membership curves once at startup; the UI uses them everywhere.
  useEffect(() => {
    api.membershipCurves()
       .then(setCurves)
       .catch((e) => setBootError(e.message));
  }, []);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="container app-header__inner">
          <div className="app-header__title">
            <small>Reference Implementation · JSS 2026</small>
            Fuzzy DSS <em>—</em> AI-Augmented SDLC
          </div>
          <nav className="app-header__nav">
            {TABS.map((t) => (
              <button key={t.id}
                      className={`tab-btn ${tab === t.id ? 'is-active' : ''}`}
                      onClick={() => setTab(t.id)}>
                {t.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main>
        <div className="container">
          {bootError && (
            <div className="error-box">
              Cannot reach the backend ({bootError}). Make sure it's running on port 8000.
            </div>
          )}

          {tab === 'assess' && <ProjectAssessment curves={curves} />}
          {tab === 'batch'  && <BatchUpload />}
          {tab === 'study'  && <OSSStudy />}
          {tab === 'era'    && <EraShift />}
          {tab === 'calib'  && <Calibration />}
          {tab === 'rules'  && <RuleBook />}
        </div>
      </main>

      <footer className="app-footer">
        <div className="container" style={{ display: 'flex',
                                            justifyContent: 'space-between',
                                            flexWrap: 'wrap', gap: 'var(--s-3)' }}>
          <span>
            Valahia University of Târgoviște ·
            <em>Journal of Systems &amp; Software</em> · v0.2.0  MIT License
          </span>
          <span></span>
        </div>
      </footer>
    </div>
  );
}
