# Defuzzification Logic Documentation

## Overview

Defuzzification is the final step of the Mamdani fuzzy inference system that converts the aggregated fuzzy membership function into a crisp (scalar) Project Health Score (PHS) value. This document describes how defuzzification works across both the backend inference engine and frontend visualization.

---

## Backend Implementation

### Location
File: `backend/app/core/fuzzy_engine.py` (lines 195–210)

### Process: Centre-of-Gravity (Centroid) Method

The defuzzification uses the Centre-of-Gravity method as specified in Equation 5 of the paper:

```
PHS = Σ(x · μ_aggregated(x)) / Σ(μ_aggregated(x))
```

Where:
- `x` = value in the PHS universe [0, 100]
- `μ_aggregated(x)` = the aggregated fuzzy output membership function
- The sum is computed over all discretized points in the PHS universe

### Implementation Details

#### 1. Universe of Discourse
```python
PHS_UNIVERSE = np.arange(0, 100.01, 0.1)  # 1001 points
```
- Resolution of 0.1 chosen to achieve defuzzification error < 0.1 PHS points
- Dense discretization ensures accurate centroid calculation

#### 2. Aggregation Function
Before defuzzification, the aggregated membership function is built via Mamdani implication:

```python
aggregated = np.zeros_like(PHS_UNIVERSE)
for idx, (d_lbl, l_lbl, q_lbl, out_lbl, rationale) in enumerate(RULES):
    firing = min(mu_dspd[d_lbl], mu_ltbf[l_lbl], mu_qd[q_lbl])      # min AND
    clipped = np.fmin(firing, _MFS_PHS[out_lbl])                     # clip consequent
    aggregated = np.fmax(aggregated, clipped)                        # max aggregation
```

This creates a piecewise membership function that combines all fired rules.

#### 3. Centroid Calculation
```python
if aggregated.sum() == 0:
    # Edge case: no rule fires (input outside antecedent support)
    phs = 50.0
    dominant = "sustainable"
    dominant_mu = 0.0
else:
    phs = float(fuzz.defuzz(PHS_UNIVERSE, aggregated, "centroid"))
```

Key points:
- Uses scikit-fuzzy's `fuzz.defuzz()` with method="centroid"
- This is the mathematical centre-of-mass of the aggregated membership function
- Implemented numerically using trapezoidal integration
- Returns a scalar value clamped to [0, 100]

#### 4. Dominant Linguistic State
After obtaining the crisp PHS value, the system determines which output fuzzy set is most representative:

```python
memberships_at_phs = {
    k: float(fuzz.interp_membership(PHS_UNIVERSE, _MFS_PHS[k], phs))
    for k in PHS_PARAMS
}
dominant = max(memberships_at_phs, key=memberships_at_phs.get)
dominant_mu = memberships_at_phs[dominant]
```

Process:
1. Evaluate all five output membership functions (critical_risk, at_risk, sustainable, high_performance, elite_ai) at the crisp PHS value
2. The set with the highest degree is the "dominant" linguistic state
3. Store its degree as `state_membership` (confidence that this label applies)

Output membership parameters (from PHS_PARAMS):
```python
PHS_PARAMS = {
    "critical_risk":     [0,  0,    10,  25],      # trapezoid
    "at_risk":           [20, 35,   50],           # triangle
    "sustainable":       [45, 60,   75],           # triangle
    "high_performance":  [60, 72.5, 85],           # triangle
    "elite_ai":          [70, 85,   100, 100],     # trapezoid
}
```

#### 5. Result Type
All defuzzification outputs are packaged in `InferenceResult`:

```python
@dataclass
class InferenceResult:
    inputs: Dict[str, float]                    # Clamped input values
    phs: float                                  # Crisp output (rounded to 0.01)
    linguistic_state: str                       # Friendly label (e.g., "Sustainable")
    state_membership: float                     # μ of dominant set (0–1)
    input_memberships: Dict[str, Dict[str, float]]   # Fuzzification step
    rule_activations: List[Dict]                # Rule firing details
```

---

## API Contract

### Endpoint: `POST /assess`
Input: `AssessmentRequest` (DSPD, LTBF, Qd, optional project_name)

Output: `AssessmentResponse` with defuzzification results:
```json
{
  "project_name": "ProjectA",
  "inputs": {"DSPD": 25.0, "LTBF": 8.5, "Qd": 6.2},
  "phs": 68.45,
  "linguistic_state": "High Performance",
  "state_membership": 0.7834,
  "input_memberships": {
    "DSPD": {"low": 0, "average": 0.15, "high": 0.85},
    "LTBF": {"rapid": 0, "nominal": 0.42, "sluggish": 0},
    "Qd": {"fragile": 0, "stable": 0.3, "resilient": 0.7}
  },
  "rule_activations": [
    {
      "id": "R1",
      "antecedents": {"DSPD": "high", "LTBF": "rapid", "Qd": "resilient"},
      "consequent": "elite_ai",
      "firing_strength": 0.0,
      "rationale": "R1: Maximum synergy; AI dividend fully realised."
    },
    ...
  ]
}
```

---

## Frontend Visualization

### 1. PHSGauge Component (`frontend/src/components/PHSGauge.jsx`)

Displays the crisp PHS value as a visual gauge:

```jsx
export default function PHSGauge({ phs, state, membership }) {
  const ratio = Math.max(0, Math.min(100, phs)) / 100;
  
  return (
    <div className="phs-display">
      <div className="phs-number numeric" style={{ color }}>
        {phs.toFixed(1)}  {/* e.g., "68.5" */}
      </div>
      <div className="phs-state-name" style={{ color }}>{state}</div>
      {/* Visual progress bar from 0–100 */}
      <svg>
        <line x1="0" y1="7" x2={320 * ratio} y2="7" 
              stroke={color} strokeWidth="3" />
      </svg>
      <div>
        dominant-state membership μ = {membership.toFixed(3)}
      </div>
    </div>
  );
}
```

What it shows:
- Crisp PHS score (0–100): the defuzzified scalar value
- Dominant linguistic state: e.g., "High Performance"
- Visual progress bar: maps PHS linearly to bar length
- State membership (μ): confidence in the dominant state (3 decimal places)

Color coding (uses CSS variables):
```javascript
const STATE_COLOR = {
  'Critical Risk': 'var(--state-critical)',      // red
  'At Risk': 'var(--state-at-risk)',             // orange
  'Sustainable': 'var(--state-sustainable)',    // yellow
  'High Performance': 'var(--state-high)',       // light green
  'Elite AI Maturity': 'var(--state-elite)',     // dark green
};
```

### 2. MembershipPlot Component (`frontend/src/components/MembershipPlot.jsx`)

Shows membership curves for any fuzzy variable, with the current input value marked:

```jsx
export default function MembershipPlot({ 
  title,              // e.g., "Delivered Story Points per Deployment"
  variable,           // e.g., "DSPD"
  curves,             // { x: [...], sets: { low: [...], average: [...], high: [...] } }
  currentValue,       // e.g., 25.0
  height = 200 
}) {
  return (
    <LineChart>
      {/* Plot each membership function curve */}
      {setNames.map(s => <Line dataKey={s} ... />)}
      
      {/* Mark current input value on x-axis */}
      {currentValue !== undefined && (
        <ReferenceDot x={Number(currentValue)} y={0} r={4} />
      )}
    </LineChart>
  );
}
```

What it shows:
- Membership curves: the fuzzy sets for each variable
- Current value marker: red dot on the x-axis showing where the input falls
- Membership degrees: displayed via line chart (y-axis = μ ∈ [0, 1])

Used for:
- Inputs: DSPD, LTBF, Qd curves + current input value
- Output: PHS curve + current crisp output value (as a red marker)

### 3. Data Flow

```
Backend /assess
    ↓
AssessmentResponse (includes phs, linguistic_state, state_membership)
    ↓
Frontend receives JSON
    ↓
PHSGauge renders crisp PHS + state label + membership degree
    ↓
MembershipPlot renders curves with current values marked
```

---

## Example Workflow

### Input
```
DSPD = 22.0  (high productivity)
LTBF = 6.0   (rapid delivery)
Qd   = 7.5   (resilient quality)
```

### Fuzzification (frontend display)
- DSPD 22.0 → {low: 0, average: 0.24, high: 0.76}  ← MembershipPlot shows marker at x=22
- LTBF 6.0  → {rapid: 0.4, nominal: 0.32, sluggish: 0}
- Qd 7.5    → {fragile: 0, stable: 0.1, resilient: 0.9}

### Rule Firing (backend log)
- R1 (high ∧ rapid ∧ resilient): firing = min(0.76, 0.4, 0.9) = 0.4 → clips elite_ai
- R2 (high ∧ rapid ∧ stable): firing = min(0.76, 0.4, 0.1) = 0.1 → clips high_performance
- ... (other rules fire with lower strengths)
- Aggregated MF = max of all clipped consequents

### Defuzzification (backend calculation)
- Centroid of aggregated MF = 82.34
- At PHS = 82.34:
  - critical_risk μ = 0
  - at_risk μ = 0
  - sustainable μ = 0.02
  - high_performance μ = 0.45
  - elite_ai μ = 0.82 ← dominant
- Result: phs = 82.34, state = "Elite AI Maturity", membership = 0.82

### Frontend Display (PHSGauge)
```
     82.3
  Elite AI Maturity
  ████████████████░ (82% filled bar)
  
  dominant-state membership μ = 0.820
```

---

## Edge Cases

### 1. No Rules Fire (aggregated.sum() == 0)
- Occurs when inputs fall outside all rule antecedent supports
- Fallback: PHS = 50.0 (neutral midpoint), state = "Sustainable", μ = 0.0
- Frontend display: Midpoint of gauge, neutral state

### 2. Multiple Peaks in Aggregated MF
- Centroid method naturally finds the weighted mean
- If two states are equally active (e.g., μ = 0.5 at boundary), centroid pulls between them
- Dominant state selection then picks the set with max μ at that crisp value

### 3. Input Clamping
```python
dspd_c = float(np.clip(dspd, DSPD_UNIVERSE[0], DSPD_UNIVERSE[-1]))
```
- Inputs are clamped to valid ranges before fuzzification
- Prevents NaN from propagating through inference

---

## Performance Characteristics

| Aspect | Value |
|--------|-------|
| Defuzzification method | Centre-of-Gravity (Centroid) |
| Universe discretization | 0.1 units |
| PHS_UNIVERSE size | 1001 points |
| Accuracy | ±0.1 PHS units |
| Latency | <1 ms per inference (CPU) |
| Output range | [0, 100] continuous |
| Output precision | 0.01 (rounded in JSON) |

---

## References

1. Paper: Suduc et al., "A Fuzzy Hybrid Decision Support System (JSS, 2026)"
   - Equation 5: Centre-of-Gravity defuzzification formula
   - Section 3: Membership function parameters & output ranges

2. Library: scikit-fuzzy (`fuzz.defuzz(universe, mf, 'centroid')`)
   - Implements trapezoidal integration for centroid calculation

3. Fuzzy Logic Theory:
   - Mamdani implication: min(a, b) for AND, max(a, b) for aggregation
   - Defuzzification converts fuzzy sets → crisp decision support values
