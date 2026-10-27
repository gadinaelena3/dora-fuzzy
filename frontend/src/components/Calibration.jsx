import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Cell,
} from 'recharts';
import { api } from '../api/client';

const AXIS_META = {
  DSPD: { title: 'DSPD (Volume)', formula: 'clip(n_prs / pre_ai_mean_prs × k, 0, 50)',
          signal: 'merged PRs of the quarter / project Pre-AI quarterly mean', key: 'k_dspd' },
  LTBF: { title: 'LTBF (Value)', formula: 'clip(median_cycle_days × k, 0, 30)',
          signal: 'quarterly median PR cycle time (days)', key: 'k_ltbf' },
  Qd:   { title: 'Qd (Viability)', formula: 'clip(FTMR × 10 / (churn × k), 0, 10)',
          signal: 'first-time merge rate / churn ratio', key: 'k_qd' },
};
const signed = (x) => `${x > 0 ? '+' : x < 0 ? '−' : ''}${Math.abs(x).toFixed(3)}`;

function AxisEntropy({ axis, info, maxEntropy }) {
  const chartData = info.rows.map((r) => ({ k: String(r.k), entropy: r.entropy, reported: r.reported }));
  const reported = info.rows.find((r) => r.reported);
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
          <Tooltip formatter={(v) => [`${v} bits`, 'entropy']} labelFormatter={(l) => `k = ${l}`}
                   contentStyle={{ fontSize: 12, fontFamily: 'var(--font-mono)',
                                   background: 'var(--paper)', border: '1px solid var(--ink)' }} />
          <ReferenceLine y={maxEntropy} stroke="var(--ink-3)" strokeDasharray="4 4"
                         label={{ value: `max log₂3 = ${maxEntropy}`, fontSize: 9,
                                  fill: 'var(--ink-3)', position: 'insideTopRight' }} />
          <Bar dataKey="entropy" radius={[2, 2, 0, 0]}>
            {chartData.map((d, i) => (
              <Cell key={i} fill={d.reported ? 'var(--accent)' : 'var(--paper-2)'}
                    stroke={d.reported ? 'var(--accent)' : 'var(--rule)'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p style={{ fontSize: '0.82rem', color: 'var(--ink-2)', marginTop: 'var(--s-2)' }}>
        Anchored k = <strong>{info.k}</strong> (highlighted; H = {reported.entropy} bits,
        {' '}{info.labels.map((l) => `${reported.counts[l]} ${l}`).join(' / ')}).
        {' '}Highest entropy among the candidates: k = {info.entropy_max_k} (H = {info.entropy_max} bits).
      </p>
    </div>
  );
}

export default function Calibration() {
  const [data, setData]   = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.calibration().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="error-box">Failed to load the calibration report: {error}</div>;
  if (!data) return <p style={{ color: 'var(--ink-3)' }}>Computing the calibration report…</p>;

  const axes = ['DSPD', 'LTBF', 'Qd'];

  return (
    <div>
      <div className="section-eyebrow">
        Scaling-factor calibration <span className="ref-tag">§5.2 · Addendum</span>
      </div>
      <h2 className="section-title">Calibration anchored on the Pre-AI era</h2>
      <p className="section-lede">
        Each proxy formula carries a scaling factor k that maps a raw GitHub signal into a
        fuzzy universe. The factors are fixed by an external anchor: each maps the pooled
        median of the {data.n_pre_ai_project_quarters} Pre-AI project-quarters (2019–2020)
        onto the human-baseline value that the paper assigns to that input. The Transition
        and AI-era observations are not used, and nothing about the resulting distribution
        is optimised.
      </p>

      <div className="panel">
        <h3 style={{ marginBottom: 'var(--s-4)' }}>Anchors and resulting factors</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Input</th>
              <th>Raw signal</th>
              <th className="num">Pooled Pre-AI median</th>
              <th className="num">Anchor</th>
              <th className="num">k</th>
            </tr>
          </thead>
          <tbody>
            {axes.map((axis) => (
              <tr key={axis}>
                <td><strong>{axis}</strong></td>
                <td>{AXIS_META[axis].signal}</td>
                <td className="num">{data.axes[axis].pooled_pre_ai_median}</td>
                <td className="num">{data.axes[axis].anchor}</td>
                <td className="num"><strong>{data.axes[axis].k}</strong></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="callout">
        The anchor rests on one assumption, which the study does not test: that the typical
        Pre-AI quarter of these six projects corresponds to the human baseline of the paper.
        The membership functions are therefore not validated against the proxies.
      </div>

      <div className="panel">
        <h3 style={{ marginBottom: 'var(--s-3)' }}>Held-out check</h3>
        <p style={{ fontSize: '0.9rem', color: 'var(--ink-2)', marginBottom: 'var(--s-4)' }}>
          For each project the factors are derived from the other five projects only, so that
          none of its observations contributes to the factors applied to it.
        </p>
        <table className="data-table">
          <thead>
            <tr>
              <th>Held-out project</th>
              <th className="num">k<sub>DSPD</sub></th>
              <th className="num">k<sub>LTBF</sub></th>
              <th className="num">k<sub>Qd</sub></th>
              <th className="num">Cliff's δ</th>
              <th className="num">p</th>
              <th className="num">Quarters with a different state (of 24)</th>
            </tr>
          </thead>
          <tbody>
            {data.held_out.map((h) => (
              <tr key={h.project_id}>
                <td><strong>{h.project_id}</strong></td>
                <td className="num">{h.k_dspd}</td>
                <td className="num">{h.k_ltbf}</td>
                <td className="num">{h.k_qd}</td>
                <td className="num">{signed(h.cliffs_delta)}</td>
                <td className="num">{h.mwu_p.toFixed(4)}{h.significant_bonferroni ? ' ✓' : ''}</td>
                <td className="num">{h.quarters_state_changed}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h3 style={{ margin: 'var(--s-6) 0 var(--s-2)' }}>Entropy of the input zones (diagnostic)</h3>
      <p style={{ fontSize: '0.9rem', color: 'var(--ink-2)', marginBottom: 'var(--s-4)' }}>
        For each candidate k on one axis, every project-quarter is assigned to the fuzzy set
        with the highest membership and the Shannon entropy of the three-zone distribution is
        computed. Selecting k by maximising this entropy would be circular; it is shown here
        only to locate the anchored values.
      </p>
      {axes.map((axis) => (
        <AxisEntropy key={axis} axis={axis} info={data.axes[axis]} maxEntropy={data.max_entropy_bits} />
      ))}
    </div>
  );
}
