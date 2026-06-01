import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceDot,
} from 'recharts';

const SET_COLORS = {
  // Inputs
  low:        'var(--state-critical)',
  average:    'var(--state-sustainable)',
  high:       'var(--state-elite)',
  rapid:      'var(--state-elite)',
  nominal:    'var(--state-sustainable)',
  sluggish:   'var(--state-critical)',
  fragile:    'var(--state-critical)',
  stable:     'var(--state-sustainable)',
  resilient:  'var(--state-elite)',
  // Output PHS
  critical_risk:    'var(--state-critical)',
  at_risk:          'var(--state-at-risk)',
  sustainable:      'var(--state-sustainable)',
  high_performance: 'var(--state-high)',
  elite_ai:         'var(--state-elite)',
};

const SET_LABELS = {
  low: 'Low (Stagnant)', average: 'Average (Steady)', high: 'High (AI-Accel.)',
  rapid: 'Rapid (Elite AI)', nominal: 'Nominal (Human)', sluggish: 'Sluggish (AI-Tax)',
  fragile: 'Fragile', stable: 'Stable', resilient: 'Resilient',
  critical_risk: 'Critical Risk', at_risk: 'At Risk',
  sustainable: 'Sustainable', high_performance: 'High Performance',
  elite_ai: 'Elite AI',
};

export default function MembershipPlot({ title, variable, curves, currentValue, height = 200 }) {
  if (!curves) return null;
  const { x, sets } = curves;
  const setNames = Object.keys(sets);

  // Reshape into Recharts row-format: [{ x: 0, low: 1, average: 0, high: 0 }, ...]
  // Subsample to keep DOM lean (every 5th point is fine for plotting).
  const stride = Math.max(1, Math.floor(x.length / 200));
  const data = [];
  for (let i = 0; i < x.length; i += stride) {
    const row = { x: x[i] };
    for (const s of setNames) row[s] = sets[s][i];
    data.push(row);
  }

  return (
    <div>
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
        marginBottom: 'var(--s-2)',
      }}>
        <h3 style={{ fontFamily: 'var(--font-display)', fontStyle: 'italic' }}>
          {title}
        </h3>
        {currentValue !== undefined && currentValue !== null && (
          <span className="numeric" style={{ fontSize: '0.8rem', color: 'var(--ink-3)' }}>
            current = <strong style={{ color: 'var(--accent)' }}>
              {Number(currentValue).toFixed(2)}
            </strong>
          </span>
        )}
      </div>

      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 4 }}>
          <CartesianGrid stroke="var(--rule)" strokeDasharray="2 4" vertical={false} />
          <XAxis
            dataKey="x" type="number" domain={['dataMin', 'dataMax']}
            tick={{ fill: 'var(--ink-3)', fontFamily: 'var(--font-mono)', fontSize: 11 }}
            stroke="var(--ink-3)"
          />
          <YAxis
            domain={[0, 1]} ticks={[0, 0.5, 1]}
            tick={{ fill: 'var(--ink-3)', fontFamily: 'var(--font-mono)', fontSize: 11 }}
            stroke="var(--ink-3)"
            label={{ value: 'μ', angle: -90, position: 'insideLeft',
                     style: { fill: 'var(--ink-3)', fontFamily: 'var(--font-mono)' } }}
          />
          <Tooltip
            contentStyle={{
              background: 'var(--paper)', border: '1px solid var(--ink)',
              fontFamily: 'var(--font-mono)', fontSize: '0.78rem',
            }}
            formatter={(v, name) => [Number(v).toFixed(3), SET_LABELS[name] || name]}
            labelFormatter={(v) => `${variable} = ${Number(v).toFixed(2)}`}
          />
          {setNames.map((s) => (
            <Line
              key={s} type="monotone" dataKey={s} stroke={SET_COLORS[s] || 'var(--ink)'}
              dot={false} strokeWidth={1.6} isAnimationActive={false}
              name={s}
            />
          ))}
          {currentValue !== undefined && currentValue !== null && (
            <ReferenceDot
              x={Number(currentValue)} y={0}
              r={4} fill="var(--accent)" stroke="var(--ink)" strokeWidth={1.5}
            />
          )}
        </LineChart>
      </ResponsiveContainer>

      <div className="legend">
        {setNames.map((s) => (
          <span key={s}>
            <span className="legend-swatch"
                  style={{ background: SET_COLORS[s] || 'var(--ink)' }} />
            {SET_LABELS[s] || s}
          </span>
        ))}
      </div>
    </div>
  );
}
