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

export default function EraShift() {
  const [data, setData]   = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.study()
       .then((d) => { setData(d); setError(null); })
       .catch((e) => setError(e.message));
  }, []);

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
  const sigCount = data.era_comparison.filter((e) => e.significant_bonferroni).length;
  const wf = data.workflow_change;
  const span = (r, unit = '') => `${r[0]}–${r[1]}${unit}`;

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
        statistically significant shift at the Bonferroni-corrected threshold
        (α′ = {data.alpha_bonferroni}).
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
                <td>{e.significant_bonferroni
                      ? <span style={{ color: 'var(--accent)', fontWeight: 700 }}>✓</span>
                      : <span style={{ color: 'var(--ink-3)' }}>—</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p style={{ fontSize: '0.8rem', color: 'var(--ink-3)', marginTop: 'var(--s-3)' }}>
          Two-sided Mann–Whitney U on the quarterly PHS values (n = 8 Pre-AI, n = 9 AI-era);
          Sig. marks p &lt; α′ = {data.alpha_bonferroni}.
        </p>
      </div>

      <div className="panel">
        <h3 style={{ marginBottom: 'var(--s-3)' }}>Reading the {wf.project_id} shift</h3>
        <p style={{ fontSize: '0.9rem', color: 'var(--ink-2)', marginBottom: 'var(--s-4)' }}>
          The shift is not interpreted as an effect of AI adoption. In {wf.break_quarter}, two
          quarters before the AI-era window opens, the population of merged pull requests of
          this project changes: volume rises about fourfold, almost every pull request is
          reviewed, and about nine in ten are merged by their own author. The volume and
          cycle-time proxies cannot distinguish such a change in merge workflow from a change
          in delivery performance.
        </p>
        <table className="data-table">
          <thead>
            <tr>
              <th>Per quarter (range)</th>
              <th className="num">before {wf.break_quarter} ({wf.before.quarters} quarters)</th>
              <th className="num">from {wf.break_quarter} ({wf.after.quarters} quarters)</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>Merged pull requests</td>
                <td className="num">{span(wf.before.merged_prs)}</td>
                <td className="num">{span(wf.after.merged_prs)}</td></tr>
            <tr><td>Median cycle time</td>
                <td className="num">{span(wf.before.median_cycle_hours, ' h')}</td>
                <td className="num">{span(wf.after.median_cycle_hours, ' h')}</td></tr>
            <tr><td>Merged within one hour</td>
                <td className="num">{span(wf.before.merged_within_1h_pct, '%')}</td>
                <td className="num">{span(wf.after.merged_within_1h_pct, '%')}</td></tr>
            <tr><td>Merged without any review</td>
                <td className="num">{span(wf.before.merged_without_review_pct, '%')}</td>
                <td className="num">{span(wf.after.merged_without_review_pct, '%')}</td></tr>
            <tr><td>Merged by their own author</td>
                <td className="num">{span(wf.before.merged_by_own_author_pct, '%')}</td>
                <td className="num">{span(wf.after.merged_by_own_author_pct, '%')}</td></tr>
            <tr><td>From forks</td>
                <td className="num">{span(wf.before.from_forks_pct, '%')}</td>
                <td className="num">{span(wf.after.from_forks_pct, '%')}</td></tr>
          </tbody>
        </table>
        <ul className="note-list">
          <li>
            rust-lang/rust: the score falls although volume rises and the cycle time shortens.
            Its Pre-AI quarters match no rule and receive the fallback score of 50, which lies
            above the consequent of Rule R10 (At Risk, 35) that fires afterwards. This is a
            defect of the incomplete rule base, not a finding about the project.
          </li>
          <li>
            An earlier version of the study reported a significant positive shift for
            rust-lang/rust. It was produced by a data collection truncated at 1,000 pull
            requests per quarter and has been withdrawn.
          </li>
        </ul>
      </div>
    </div>
  );
}
