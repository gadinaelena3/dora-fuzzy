import React, { useEffect, useState } from 'react';
import { api } from '../api/client';

const STATE_LABELS = {
  critical_risk:    'Critical Risk',
  at_risk:          'At Risk',
  sustainable:      'Sustainable',
  high_performance: 'High Performance',
  elite_ai:         'Elite AI',
};

export default function RuleBook() {
  const [rules, setRules]       = useState(null);
  const [error, setError]       = useState(null);

  useEffect(() => {
    api.rules().then(setRules).catch((e) => setError(e.message));
  }, []);

  if (error)  return <div className="error-box">Failed to load rule base: {error}</div>;
  if (!rules) return <p style={{ color: 'var(--ink-3)' }}>Loading…</p>;

  return (
    <div>
      <div className="section-eyebrow">Rule base</div>
      <h2 className="section-title">12-rule Mamdani base</h2>
      <p className="section-lede">
        The full antecedent → consequent map. Rule weights are uniform; viability
        (Qd) acts as a safety governor: rules R3, R8 and R12 force a Critical Risk
        verdict whenever Qd is fragile, even when volume is high.
      </p>

      <div className="panel">
        <table className="data-table">
          <thead>
            <tr>
              <th>Rule</th>
              <th>Volume (DSPD)</th>
              <th>Value (LTBF)</th>
              <th>Viability (Qd)</th>
              <th>→ Project Health</th>
              <th>Logic</th>
            </tr>
          </thead>
          <tbody>
            {rules.rules.map((r) => (
              <tr key={r.id}>
                <td className="num"><strong style={{ color: 'var(--accent)' }}>{r.id}</strong></td>
                <td>{r.DSPD}</td>
                <td>{r.LTBF}</td>
                <td>{r.Qd}</td>
                <td>
                  <span className="state-chip" data-state={STATE_LABELS[r.PHS]}>
                    {STATE_LABELS[r.PHS]}
                  </span>
                </td>
                <td style={{ fontSize: '0.82rem', color: 'var(--ink-2)',
                             fontStyle: 'italic' }}>
                  {r.rationale.replace(/^R\d+:\s*/, '')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
