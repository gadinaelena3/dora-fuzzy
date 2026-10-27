import React, { useEffect, useState } from 'react';
import { api } from '../api/client';

const STATE_ORDER = ['Critical Risk', 'At Risk', 'Sustainable', 'High Performance', 'Elite AI Maturity'];
const STATE_SHORT = {
  'Critical Risk': 'Critical Risk', 'At Risk': 'At Risk', 'Sustainable': 'Sustainable',
  'High Performance': 'High Performance', 'Elite AI Maturity': 'Elite AI',
};

function StateCell({ cell }) {
  if (!cell || !cell.state) {
    return <td className="hm-cell hm-empty" title="no data">·</td>;
  }
  const note = cell.fallback ? ' · no rule fired (fallback)' : '';
  return (
    <td className="hm-cell"
        title={`${cell.quarter}: ${cell.state} (PHS ${cell.phs?.toFixed(1)})${note}`}>
      <span className={`state-dot ${cell.fallback ? 'is-fallback' : ''}`} data-state={STATE_SHORT[cell.state]} />
    </td>
  );
}

export default function OSSStudy() {
  const [data, setData]   = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.study()
       .then((d) => { setData(d); setError(null); })
       .catch((e) => setError(e.message))
       .finally(() => setLoading(false));
  }, []);

  if (error)   return <div className="error-box">Failed to load study: {error}</div>;
  if (!data && loading) return <p style={{ color: 'var(--ink-3)' }}>Running the longitudinal study…</p>;
  if (!data) return null;

  const dp = data.discriminative_power;
  const k = data.scaling_factors;
  const milestoneQuarters = Object.values(data.milestones);

  return (
    <div>
      <div className="section-eyebrow">
        Feasibility study <span className="ref-tag">§5 · {dp.n_observations} project-quarters</span>
      </div>
      <h2 className="section-title">OSS longitudinal study</h2>
      <p className="section-lede">
        The DSS applied to {dp.n_projects} open-source projects on a quarterly cadence
        (2019-Q1 → 2024-Q4), computed from {data.n_pull_requests.toLocaleString('en-US')} merged
        pull requests collected from GitHub in October 2026
        ({data.source.bot_authored_excluded} bot-authored pull requests excluded). The scaling
        factors are anchored on the Pre-AI era: k<sub>DSPD</sub> = {k.k_dspd},
        k<sub>LTBF</sub> = {k.k_ltbf}, k<sub>Qd</sub> = {k.k_qd} (see the Calibration tab).
        Each cell below is the linguistic state assigned for one project-quarter; a hollow
        cell means that no rule fired and the fallback score of 50 was used. Underlined
        columns mark the AI-tooling milestones (Copilot beta, ChatGPT GA, GPT-4).
      </p>

      <div className="metric-grid">
        <div className="metric-card">
          <div className="metric-card__value numeric">{dp.entropy_bits}</div>
          <div className="metric-card__label">linguistic-state entropy (bits)</div>
          <div className="metric-card__sub">normalised {dp.entropy_normalised} of {dp.entropy_max_bits}</div>
        </div>
        <div className="metric-card">
          <div className="metric-card__value numeric">{dp.kruskal_H}</div>
          <div className="metric-card__label">cross-project Kruskal–Wallis H</div>
          <div className="metric-card__sub">
            p = {dp.kruskal_p < 0.001 ? '< 0.001' : dp.kruskal_p.toFixed(3)}
            {dp.kruskal_significant_05 ? ' · projects differ' : ' · n.s.'}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-card__value numeric">{dp.no_rule_fallback_pct}%</div>
          <div className="metric-card__label">no-rule fallback rate</div>
          <div className="metric-card__sub">
            {dp.no_rule_fallback_n} / {dp.n_observations} quarters · {data.active_rules} rules (Table VII)
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-card__value numeric">{dp.phs_mean}</div>
          <div className="metric-card__label">mean PHS (σ {dp.phs_std})</div>
          <div className="metric-card__sub">range [{dp.phs_min}, {dp.phs_max}]</div>
        </div>
      </div>

      <div className="callout">
        This study shows that the DSS can be applied to public repository data and
        characterises its output there. It is not a validation of the membership functions
        or of the rule base: the inputs are proxies built from pull-request signals, the
        separation between projects is inherited from those inputs, and
        {' '}{dp.no_rule_fallback_pct}% of the project-quarters match none of the twelve
        rules and receive the fallback score.
      </div>

      <div className="panel">
        <h3 style={{ marginBottom: 'var(--s-4)' }}>Linguistic state · project × quarter</h3>
        <div className="hm-scroll">
          <table className="heatmap">
            <thead>
              <tr>
                <th className="hm-rowhead">project</th>
                {data.quarters.map((q) => (
                  <th key={q}
                      className={`hm-colhead ${milestoneQuarters.includes(q) ? 'hm-milestone' : ''}`}>
                    <span>{q}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.heatmap.map((row) => (
                <tr key={row.project_id}>
                  <td className="hm-rowhead" title={row.repo}>{row.project_id}</td>
                  {row.cells.map((c) => <StateCell key={c.quarter} cell={c} />)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="hm-legend">
          {STATE_ORDER.map((s) => (
            <span key={s} className="hm-legend__item">
              <span className="state-dot" data-state={STATE_SHORT[s]} /> {STATE_SHORT[s]}
            </span>
          ))}
          <span className="hm-legend__item">
            <span className="state-dot is-fallback" data-state="Sustainable" /> no rule fired (fallback, PHS = 50)
          </span>
        </div>
      </div>

      <div className="panel">
        <h3 style={{ marginBottom: 'var(--s-4)' }}>State distribution</h3>
        <table className="data-table">
          <thead><tr><th>Linguistic state</th><th className="num">Count</th><th className="num">Share</th></tr></thead>
          <tbody>
            {STATE_ORDER.map((s) => {
              const c = dp.state_distribution[s] || 0;
              return (
                <tr key={s}>
                  <td><span className="state-chip" data-state={STATE_SHORT[s]}>{STATE_SHORT[s]}</span></td>
                  <td className="num">{c}</td>
                  <td className="num">{(c / dp.n_observations * 100).toFixed(1)}%</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
