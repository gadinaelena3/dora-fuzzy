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
  return (
    <td className="hm-cell"
        title={`${cell.quarter}: ${cell.state} (PHS ${cell.phs?.toFixed(1)})`}>
      <span className="state-dot" data-state={STATE_SHORT[cell.state]} />
    </td>
  );
}

export default function OSSStudy({ ruleMode, onRuleModeChange }) {
  const [data, setData]   = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.study(ruleMode)
       .then((d) => { setData(d); setError(null); })
       .catch((e) => setError(e.message))
       .finally(() => setLoading(false));
  }, [ruleMode]);

  if (error)   return <div className="error-box">Failed to load study: {error}</div>;
  if (!data && loading) return <p style={{ color: 'var(--ink-3)' }}>Running the longitudinal study…</p>;
  if (!data) return null;

  const dp = data.discriminative_power;
  const milestoneQuarters = Object.values(data.milestones);

  return (
    <div>
      <div className="section-eyebrow">
        Empirical validation <span className="ref-tag">5 · {data.n_observations || dp.n_observations} project-quarters</span>
      </div>
      <h2 className="section-title">OSS longitudinal study</h2>
      <p className="section-lede">
        The DSS applied to {dp.n_projects} widely-studied OSS projects on a quarterly
        cadence (2019-Q1 → 2024-Q4). Each cell below is the linguistic state assigned by
        the engine for one project-quarter. Dashed columns mark the AI-tooling milestones
        (Copilot beta, ChatGPT GA, GPT-4). Data source: <strong>{data.source}</strong>.
      </p>

      <div className="study-controls">
        <span className="study-controls__label">Rule base:</span>
        <button className={`tab-btn ${ruleMode === 'base12' ? 'is-active' : ''}`}
                onClick={() => onRuleModeChange('base12')}>
          12-rule (Table VI · default-of-record)
        </button>
        <button className={`tab-btn ${ruleMode === 'extended27' ? 'is-active' : ''}`}
                onClick={() => onRuleModeChange('extended27')}>
          27-rule (full coverage)
        </button>
        {loading && <span style={{ color: 'var(--ink-3)', marginLeft: 'var(--s-3)' }}>updating…</span>}
      </div>

      {/* Headline metrics */}
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
            {dp.no_rule_fallback_n} / {dp.n_observations} quarters · {data.active_rules} active rules
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-card__value numeric">{dp.phs_mean}</div>
          <div className="metric-card__label">mean PHS (σ {dp.phs_std})</div>
          <div className="metric-card__sub">range [{dp.phs_min}, {dp.phs_max}]</div>
        </div>
      </div>

      {ruleMode === 'extended27' && (
        <div className="callout">
          The extended 27-rule base provides full 3×3×3 antecedent coverage, eliminating the
          no-rule fallback (rate → {dp.no_rule_fallback_pct}%). The 12-rule base remains the
          default-of-record so the published 5 figures reproduce exactly; this mode
          demonstrates the rule-completeness extension proposed in the Addendum.
        </div>
      )}

      {/* State heatmap */}
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
        </div>
      </div>

      {/* State distribution table */}
      <div className="panel">
        <h3 style={{ marginBottom: 'var(--s-4)' }}>State distribution </h3>
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
