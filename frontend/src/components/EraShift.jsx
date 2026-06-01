import React, { useEffect, useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Legend,
} from 'recharts';
import { api } from '../api/client';

const PROJECT_COLORS = {
  vscode: '#b1542a', rust: '#214d39', kubernetes: '#8c2a1f',
  django: '#6e7d4a', numpy: '#3a352e', react: '#3f7050',
};

export default function EraShift({ ruleMode }) {
  const [data, setData]   = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.study(ruleMode)
       .then((d) => { setData(d); setError(null); })
       .catch((e) => setError(e.message));
  }, [ruleMode]);

  if (error) return <div className="error-box">Failed to load era analysis: {error}</div>;
  if (!data) return <p style={{ color: 'var(--ink-3)' }}>Loading era comparison…</p>;

  // Pivot the time series into recharts-friendly rows: one row per quarter.
  const byQuarter = {};
  data.timeseries.forEach((r) => {
    byQuarter[r.quarter] = byQuarter[r.quarter] || { quarter: r.quarter };
    byQuarter[r.quarter][r.project_id] = r.phs;
  });
  const chartData = data.quarters.map((q) => byQuarter[q] || { quarter: q });
  const projects = Object.keys(data.project_meta);
  const sigCount = data.era_comparison.filter((e) => e.significant_05).length;

  return (
    <div>
      <div className="section-eyebrow">
        Pre-AI vs AI-era
      </div>
      <h2 className="section-title">Era shift detection</h2>
      <p className="section-lede">
        Per-project PHS trajectories across the study window. The era comparison contrasts
        the Pre-AI baseline (2019–2020) against the AI-era (post-ChatGPT-GA, 2022-Q4 → 2024-Q4)
        with a Mann–Whitney U test and Cliff's δ effect size.
        <strong> {sigCount} of {data.era_comparison.length}</strong> projects show a
        statistically significant shift (α = 0.05).
      </p>

      <div className="panel">
        <h3 style={{ marginBottom: 'var(--s-4)' }}>PHS time series</h3>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData} margin={{ top: 8, right: 16, bottom: 8, left: -8 }}>
            <CartesianGrid stroke="var(--rule)" strokeDasharray="2 3" />
            <XAxis dataKey="quarter" tick={{ fontSize: 10, fill: 'var(--ink-3)' }}
                   interval={1} angle={-40} textAnchor="end" height={50} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: 'var(--ink-3)' }} />
            <Tooltip contentStyle={{ fontSize: 12, fontFamily: 'var(--font-mono)',
                                     background: 'var(--paper)', border: '1px solid var(--ink)' }} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            {Object.entries(data.milestones).map(([label, q]) => (
              <ReferenceLine key={label} x={q} stroke="var(--ink-3)" strokeDasharray="4 4"
                             label={({ viewBox }) => {
                               const { x, y } = viewBox;
                               return (
                                 <text
                                   x={x + 3}
                                   y={y + 4}
                                   textAnchor="start"
                                   transform={`rotate(90, ${x + 3}, ${y + 4})`}
                                   fontSize={9}
                                   fill="var(--ink-3)"
                                 >
                                   {label}
                                 </text>
                               );
                             }} />
            ))}
            {projects.map((p) => (
              <Line key={p} type="monotone" dataKey={p} stroke={PROJECT_COLORS[p]}
                    strokeWidth={1.8} dot={false} connectNulls />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="panel">
        <h3 style={{ marginBottom: 'var(--s-4)' }}>Era comparison </h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Project</th>
              <th className="num">Pre-AI mean</th>
              <th className="num">AI-era mean</th>
              <th className="num">Δ</th>
              <th className="num">MWU U</th>
              <th className="num">p</th>
              <th className="num">Cliff's δ</th>
              <th>Sig.</th>
            </tr>
          </thead>
          <tbody>
            {data.era_comparison.map((e) => (
              <tr key={e.project_id}>
                <td title={e.repo}><strong>{e.project_id}</strong></td>
                <td className="num">{e.phs_pre_mean}</td>
                <td className="num">{e.phs_ai_mean}</td>
                <td className="num" style={{ color: e.phs_shift > 0 ? 'var(--state-high)' : 'var(--state-critical)',
                                             fontWeight: 600 }}>
                  {e.phs_shift > 0 ? '+' : ''}{e.phs_shift}
                </td>
                <td className="num">{e.mwu_U}</td>
                <td className="num">{e.mwu_p}</td>
                <td className="num">{e.cliffs_delta > 0 ? '+' : ''}{e.cliffs_delta}</td>
                <td>{e.significant_05
                      ? <span style={{ color: 'var(--accent)', fontWeight: 700 }}>✓</span>
                      : <span style={{ color: 'var(--ink-3)' }}>—</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p style={{ fontSize: '0.8rem', color: 'var(--ink-3)', marginTop: 'var(--s-3)' }}>
          Bundled-sample figures are illustrative and deterministic. The headline live-data
          figures reported in 5 are produced by running <code>scripts/fetch_github.py</code>
          (a GitHub token re-derives every number through the calibrated proxy layer).
        </p>
      </div>
    </div>
  );
}
