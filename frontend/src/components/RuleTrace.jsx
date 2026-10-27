import React from 'react';

const PHS_LABELS = {
  critical_risk:    'Critical Risk',
  at_risk:          'At Risk',
  sustainable:      'Sustainable',
  high_performance: 'High Performance',
  elite_ai:         'Elite AI',
};

export default function RuleTrace({ rules }) {
  if (!rules || rules.length === 0) return null;

  // Sort: fired first, then by descending firing strength
  const sorted = [...rules].sort((a, b) => b.firing_strength - a.firing_strength);

  return (
    <div>
      <div className="section-eyebrow">Rule activations </div>
      <h3 style={{ fontFamily: 'var(--font-display)', fontStyle: 'italic',
                   marginBottom: 'var(--s-4)' }}>
        Inference trace
      </h3>

      <div style={{ borderTop: 'var(--rule-thick)' }}>
        {sorted.map((r) => {
          const fired = r.firing_strength > 0;
          return (
            <div key={r.id} className="rule-row" style={{
              opacity: fired ? 1 : 0.45,
            }}>
              <div className="rule-id">{r.id}</div>
              <div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem',
                              color: 'var(--ink-2)' }}>
                  {r.antecedents.DSPD} · {r.antecedents.LTBF} · {r.antecedents.Qd}
                  <span style={{ color: 'var(--ink-3)' }}> → </span>
                  <span style={{ color: 'var(--accent)' }}>
                    {PHS_LABELS[r.consequent]}
                  </span>
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--ink-3)',
                              marginTop: 2, fontStyle: 'italic' }}>
                  {r.rationale}
                </div>
              </div>
              <div className="rule-firing" data-fired={fired}>
                {r.firing_strength.toFixed(3)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
