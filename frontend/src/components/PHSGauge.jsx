import React from 'react';

const STATE_COLOR = {
  'Critical Risk':     'var(--state-critical)',
  'At Risk':           'var(--state-at-risk)',
  'Sustainable':       'var(--state-sustainable)',
  'High Performance':  'var(--state-high)',
  'Elite AI Maturity': 'var(--state-elite)',
};

export default function PHSGauge({ phs, state, membership }) {
  const color = STATE_COLOR[state] || 'var(--ink)';
  // visual gauge: 200 wide arc representing 0-100
  const ratio = Math.max(0, Math.min(100, phs)) / 100;

  return (
    <div className="phs-display">
      <div className="phs-number numeric" style={{ color }}>
        {phs.toFixed(1)}
      </div>
      <div>
        <div className="phs-state-label">Project Health Score</div>
        <div className="phs-state-name" style={{ color }}>{state}</div>
        <div style={{ marginTop: 'var(--s-3)' }}>
          <svg width="100%" height="14" viewBox="0 0 320 14" preserveAspectRatio="none">
            <line x1="0" y1="7" x2="320" y2="7" stroke="var(--rule)" strokeWidth="1" />
            <line x1="0" y1="7" x2={320 * ratio} y2="7" stroke={color} strokeWidth="3" />
            {[0, 20, 40, 60, 80, 100].map((t) => (
              <line key={t} x1={t * 3.2} y1="2" x2={t * 3.2} y2="12"
                    stroke="var(--ink-3)" strokeWidth="0.5" />
            ))}
          </svg>
          <div style={{
            display: 'flex', justifyContent: 'space-between',
            fontFamily: 'var(--font-mono)', fontSize: '0.7rem',
            color: 'var(--ink-3)', marginTop: 4, letterSpacing: '0.1em',
          }}>
            <span>0</span><span>20</span><span>40</span>
            <span>60</span><span>80</span><span>100</span>
          </div>
        </div>
        <div style={{
          marginTop: 'var(--s-3)', fontSize: '0.78rem', color: 'var(--ink-3)',
          fontStyle: 'italic',
        }}>
          dominant-state membership μ = {membership.toFixed(3)}
        </div>
      </div>
    </div>
  );
}
