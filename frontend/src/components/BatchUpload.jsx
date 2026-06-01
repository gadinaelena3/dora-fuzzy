import React, { useRef, useState } from 'react';
import { api } from '../api/client';

export default function BatchUpload() {
  const [file, setFile]         = useState(null);
  const [results, setResults]   = useState(null);
  const [error, setError]       = useState(null);
  const [loading, setLoading]   = useState(false);
  const inputRef = useRef(null);

  const handleFile = (f) => {
    setFile(f);
    setResults(null);
    setError(null);
  };

  const onSubmit = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const data = await api.assessBatch(file);
      setResults(data);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadCsv = () => {
    if (!results) return;
    const rows = [
      ['project_name', 'dspd', 'ltbf', 'qd', 'phs', 'linguistic_state'],
      ...results.results.map((r) => [
        r.project_name, r.inputs.DSPD, r.inputs.LTBF, r.inputs.Qd,
        r.phs, r.linguistic_state,
      ]),
    ];
    const csv = rows.map((r) => r.map((c) => `"${c}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'phs_results.csv'; a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      <div className="section-eyebrow">Batch assessment</div>
      <h2 className="section-title">Bulk classify projects from a CSV</h2>
      <p className="section-lede">
        Upload a CSV with the columns <code>dspd</code>, <code>ltbf</code>, <code>qd</code>,
        and (optional) <code>project_name</code>. Each row is run through the full Mamdani
        inference pipeline and assigned a Project Health Score plus linguistic state.
        Use this for the OSS longitudinal study and the industrial workshop ranking exercise
        described in the revision plan.
      </p>

      {/* Upload zone */}
      <label className="upload-zone">
        <input ref={inputRef} type="file" accept=".csv"
               onChange={(e) => handleFile(e.target.files?.[0])} />
        <div style={{ fontFamily: 'var(--font-display)', fontStyle: 'italic',
                      fontSize: '1.4rem', marginBottom: 'var(--s-2)' }}>
          {file ? file.name : 'Drop a CSV file here'}
        </div>
        <div style={{ fontSize: '0.85rem', color: 'var(--ink-3)' }}>
          {file ? `${(file.size / 1024).toFixed(1)} KB · click to change`
                : 'or click to browse'}
        </div>
      </label>

      <div style={{ display: 'flex', gap: 'var(--s-3)', marginTop: 'var(--s-5)',
                    alignItems: 'center' }}>
        <button className="btn btn--primary" disabled={!file || loading}
                onClick={onSubmit}>
          {loading ? 'Processing…' : 'Run inference'}
        </button>
        {results && (
          <button className="btn btn--ghost" onClick={downloadCsv}>
            Download results CSV
          </button>
        )}
        <a href="/api/membership-curves" target="_blank" rel="noreferrer"
           style={{ marginLeft: 'auto', fontSize: '0.78rem', color: 'var(--ink-3)' }}>
          API: /api/assess-batch ↗
        </a>
      </div>

      {error && <div className="error-box">{error}</div>}

      {/* Results */}
      {results && (
        <div style={{ marginTop: 'var(--s-6)' }}>
          {/* Summary */}
          <div className="panel" style={{ marginBottom: 'var(--s-4)' }}>
            <div style={{ display: 'flex', gap: 'var(--s-6)', flexWrap: 'wrap',
                          alignItems: 'baseline' }}>
              <div>
                <div className="field__label-text">Projects</div>
                <div className="numeric" style={{ fontSize: '1.6rem',
                                                  fontFamily: 'var(--font-display)',
                                                  fontWeight: 300 }}>
                  {results.n_projects}
                </div>
              </div>
              {Object.entries(results.summary).map(([state, count]) => (
                <div key={state}>
                  <div className="field__label-text">{state}</div>
                  <div className="numeric" style={{ fontSize: '1.6rem',
                                                    fontFamily: 'var(--font-display)',
                                                    fontWeight: 300 }}>
                    {count}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Table */}
          <div className="panel">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Project</th>
                  <th>DSPD</th>
                  <th>LTBF</th>
                  <th>Qd</th>
                  <th>PHS</th>
                  <th>State</th>
                </tr>
              </thead>
              <tbody>
                {results.results.map((r, i) => (
                  <tr key={i}>
                    <td>{r.project_name}</td>
                    <td className="num">{r.inputs.DSPD.toFixed(1)}</td>
                    <td className="num">{r.inputs.LTBF.toFixed(1)}</td>
                    <td className="num">{r.inputs.Qd.toFixed(2)}</td>
                    <td className="num"><strong>{r.phs.toFixed(1)}</strong></td>
                    <td>
                      <span className="state-chip" data-state={r.linguistic_state}>
                        {r.linguistic_state}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
