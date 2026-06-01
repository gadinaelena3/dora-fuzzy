import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Cell,
} from 'recharts';
import { api } from '../api/client';

const AXIS_META = {
  DSPD: { title: 'DSPD (Volume)', formula: 'clip(n_prs / mean_prs × k, 0, 50)', published_k: 14 },
  LTBF: { title: 'LTBF (Value)',  formula: 'clip(median_cycle_days × k, 0, 30)', published_k: 8 },
  Qd:   { title: 'Qd (Viability)', formula: 'clip(FTMR × 10 / (churn × k), 0, 10)', published_k: 3 },
};

function AxisSweep({ axis, info, maxEntropy }) {
  const chartData = info.rows.map((r) => ({
    k: String(r.k), entropy: r.entropy, optimal: r.k === info.optimal_k,
  }));
  return (
    <div className="panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                    flexWrap: 'wrap', gap: 'var(--s-2)', marginBottom: 'var(--s-3)' }}>
        <h3>{AXIS_META[axis].title}</h3>
        <code style={{ fontSize: '0.78rem', color: 'var(--ink-3)' }}>{AXIS_META[axis].formula}</code>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 4, left: -12 }}>
          <CartesianGrid stroke="var(--rule)" strokeDasharray="2 3" vertical={false} />
          <XAxis dataKey="k" tick={{ fontSize: 11, fill: 'var(--ink-3)' }} />
          <YAxis domain={[0, 1.6]} tick={{ fontSize: 10, fill: 'var(--ink-3)' }} />
          <Tooltip contentStyle={{ fontSize: 12, fontFamily: 'var(--font-mono)',
                                   background: 'var(--paper)', border: '1px solid var(--ink)' }} />
          <ReferenceLine y={maxEntropy} stroke="var(--ink-3)" strokeDasharray="4 4"
                         label={{ value: `max log₂3 = ${maxEntropy}`, fontSize: 9,
                                  fill: 'var(--ink-3)', position: 'insideTopRight' }} />
          <Bar dataKey="entropy" radius={[2, 2, 0, 0]}>
            {chartData.map((d, i) => (
              <Cell key={i} fill={d.optimal ? 'var(--accent)' : 'var(--paper-2)'}
                    stroke={d.optimal ? 'var(--accent)' : 'var(--rule)'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p style={{ fontSize: '0.82rem', color: 'var(--ink-2)', marginTop: 'var(--s-2)' }}>
        Entropy-maximising k on this sample = <strong>{info.optimal_k}</strong>
        {' '}(H = {info.optimal_entropy} bits). Published calibration:
        {' '}k = <strong>{AXIS_META[axis].published_k}</strong>.
      </p>
    </div>
  );
}

export default function Calibration() {
  const [data, setData]   = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.sensitivity().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="error-box">Failed to load sensitivity sweep: {error}</div>;
  if (!data) return <p style={{ color: 'var(--ink-3)' }}>Sweeping scaling factors…</p>;

  return (
    <div>
      <div className="section-eyebrow">
        Scaling-factor calibration
      </div>
      <h2 className="section-title">Sensitivity analysis</h2>
      <p className="section-lede">
        Each proxy formula carries a free scaling parameter k. For every candidate k, every
        project-quarter is assigned to the fuzzy set with the highest membership (peak
        classification), and the Shannon entropy of the resulting three-zone distribution is
        computed. The k that maximises entropy — distributing observations most evenly across
        the linguistic zones — is the calibrated value. The contribution is the
        <em> procedure</em>, not the parameter values themselves.
      </p>

      <div className="callout">
        On the bundled illustrative sample the optima are
        {' '}{Object.entries(data.axes).map(([ax, d], i, arr) => (
          <span key={ax}>k<sub>{ax}</sub> = <strong>{d.optimal_k}</strong>{i < arr.length - 1 ? ', ' : ''}</span>
        ))}.
        The published calibration (k<sub>DSPD</sub>=14, k<sub>LTBF</sub>=8, k<sub>Qd</sub>=3) is
        derived from live GitHub data; LTBF's sample optimum differs because the bundled sample
        ships cycle-times already in DSS units. See <code>docs/METHODOLOGY.md 2</code>.
      </div>

      {['DSPD', 'LTBF', 'Qd'].map((axis) => (
        <AxisSweep key={axis} axis={axis} info={data.axes[axis]} maxEntropy={data.max_entropy_bits} />
      ))}
    </div>
  );
}
