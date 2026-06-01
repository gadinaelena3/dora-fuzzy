import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import PHSGauge from './PHSGauge';
import MembershipPlot from './MembershipPlot';
import RuleTrace from './RuleTrace';

const PRESETS = [
  { label: 'Scenario A — Elite AI',     dspd: 22, ltbf: 3,  qd: 7.5 },
  { label: 'Scenario B — Human Base',   dspd: 12, ltbf: 7,  qd: 3.0 },
  { label: 'Scenario C — Precipice',    dspd: 25, ltbf: 15, qd: 0.8 },
];

export default function ProjectAssessment({ curves }) {
  const [dspd, setDspd] = useState(15);
  const [ltbf, setLtbf] = useState(7);
  const [qd,   setQd]   = useState(3);
  const [result, setResult] = useState(null);
  const [error, setError]   = useState(null);
  const [loading, setLoading] = useState(false);

  // Debounced live assessment
  useEffect(() => {
    setLoading(true);
    const t = setTimeout(async () => {
      try {
        const res = await api.assess({ dspd, ltbf, qd });
        setResult(res);
        setError(null);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    }, 120);
    return () => clearTimeout(t);
  }, [dspd, ltbf, qd]);

  return (
    <div>
      <div className="section-eyebrow">Single-project assessment</div>
      <h2 className="section-title">Live inference</h2>
      <p className="section-lede">
        Adjust the three input metrics — Volume (DSPD), Value (LTBF), and Viability
        (Quality Duo) — to see the fuzzy DSS classify the project's health state in real time.
        The diamond on each membership-function plot tracks your current input.
      </p>

      {/* Presets */}
      <div style={{ display: 'flex', gap: 'var(--s-2)', marginBottom: 'var(--s-5)',
                    flexWrap: 'wrap' }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem',
                       textTransform: 'uppercase', letterSpacing: '0.16em',
                       color: 'var(--ink-3)', alignSelf: 'center', marginRight: 'var(--s-2)' }}>
          Scenarios:
        </span>
        {PRESETS.map((p) => (
          <button key={p.label} className="btn btn--ghost"
                  style={{ padding: '6px 12px', fontSize: '0.7rem' }}
                  onClick={() => { setDspd(p.dspd); setLtbf(p.ltbf); setQd(p.qd); }}>
            {p.label}
          </button>
        ))}
      </div>

      <div className="two-col">
        {/* Left: inputs */}
        <div className="panel">
          <h3 style={{ marginBottom: 'var(--s-5)', fontStyle: 'italic' }}>Inputs</h3>

          <Slider label="DSPD — Delivered Story Points per Deployment"
                  hint="Volume · Eq. (1) of the manuscript"
                  min={0} max={50} step={0.5}
                  value={dspd} onChange={setDspd} />

          <Slider label="LTBF — Lead Time for Business Features"
                  hint="Value (days) · Eq. (3): LT_new = αT_c + βT_r"
                  min={0} max={30} step={0.5}
                  value={ltbf} onChange={setLtbf} />

          <Slider label="Qd — Quality Duo"
                  hint="Viability · Eq. (4): Qd = AI Acceptance Rate / Code Churn"
                  min={0} max={10} step={0.1}
                  value={qd} onChange={setQd} />
        </div>

        {/* Right: results */}
        <div className="panel panel--ink">
          {error && <div className="error-box">{error}</div>}
          {result && (
            <PHSGauge
              phs={result.phs}
              state={result.linguistic_state}
              membership={result.state_membership}
            />
          )}
          {loading && <div style={{ fontSize: '0.78rem', opacity: 0.6,
                                     fontFamily: 'var(--font-mono)' }}>
            Computing…
          </div>}
        </div>
      </div>

      {/* Membership plots */}
      {curves && (
        <div style={{ marginTop: 'var(--s-7)' }}>
          <div className="section-eyebrow">Fuzzy spaces</div>
          <h2 style={{ marginBottom: 'var(--s-5)' }}>Membership functions</h2>
          <div className="two-col">
            <div className="panel">
              <MembershipPlot title="DSPD (Volume)" variable="DSPD"
                              curves={curves.DSPD} currentValue={dspd} />
            </div>
            <div className="panel">
              <MembershipPlot title="LTBF (Value)" variable="LTBF"
                              curves={curves.LTBF} currentValue={ltbf} />
            </div>
          </div>
          <div className="two-col" style={{ marginTop: 'var(--s-5)' }}>
            <div className="panel">
              <MembershipPlot title="Qd (Viability)" variable="Qd"
                              curves={curves.Qd} currentValue={qd} />
            </div>
            <div className="panel">
              <MembershipPlot title="PHS (Output)" variable="PHS"
                              curves={curves.PHS}
                              currentValue={result?.phs} />
            </div>
          </div>
        </div>
      )}

      {/* Rule trace */}
      {result && (
        <div style={{ marginTop: 'var(--s-7)' }}>
          <div className="panel">
            <RuleTrace rules={result.rule_activations} />
          </div>
        </div>
      )}
    </div>
  );
}

function Slider({ label, hint, min, max, step, value, onChange }) {
  return (
    <div className="field">
      <div className="field__label">
        <span className="field__label-text">{label}</span>
        <span className="field__value">{Number(value).toFixed(2)}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value}
             onChange={(e) => onChange(Number(e.target.value))} />
      <span className="field__hint">{hint}</span>
    </div>
  );
}
