# Interrupted Time-Series Findings — Oregon Measure 110

Segmented-regression ITS testing whether quarterly outcomes changed at **Measure 110**
(effective ~2021 Q1). Model: `Y_t = β0 + β1·time + β2·post + β3·time_since_post`, with
Newey-West (HAC) standard errors (4 lags) to handle autocorrelation.
- **β1 (`time`)** = pre-policy quarterly trend
- **β2 (`post`)** = immediate level change at the policy
- **β3 (`time_since_post`)** = change in slope after the policy

## Fentanyl overdose death rate (per 100,000 / quarter)

| term | coef | p-value | reading |
|---|---|---|---|
| `time` (β1) | 0.101 | **0.001** | already rising ~0.10/qtr **before** the policy |
| `post` (β2) | 2.015 | **0.011** | level jump of ~2.0 at 2021 Q1 |
| `time_since_post` (β3) | 0.144 | 0.186 | slope steepened (0.10→0.24/qtr) but **not significant** |

*Fit:* R² = 0.82. *Autocorrelation:* Durbin-Watson = 0.79.

### What the model shows
1. **A significant pre-existing upward trend.** Fentanyl deaths were already climbing
   before Measure 110 — the surge did not begin at the policy.
2. **A significant level jump at the policy date** (β2), and
3. **No significant change in slope** afterward (β3).

### Why this is *not* evidence of a Measure 110 effect
The significant level jump is tempting to attribute to the policy, but two things prevent
that conclusion:

- **Confounding by the fentanyl supply shock.** The national fentanyl wave reached Oregon's
  drug supply at essentially the same time. A single-series ITS cannot separate the effect of
  the *policy* from the effect of the *supply change* — both produce a discontinuity at the
  same date. Without a control group (e.g., a comparison state or synthetic control), the
  level jump is not attributable to Measure 110.
- **Model misspecification (linear fit to an exponential curve).** The fentanyl series grows
  roughly exponentially; forcing straight-line segments onto an accelerating curve can
  *manufacture* an apparent level jump. A log-transformed model (`log(rate)`) would test
  whether β2 survives — if it shrinks toward zero, the "jump" was largely a curvature artifact.

### Diagnostics (and why they matter)
- **R² = 0.82** — the two segments fit the trajectory well.
- **Durbin-Watson = 0.79** — well below 2, indicating **strong positive residual
  autocorrelation**. This confirms the HAC standard errors were necessary: with naive OLS
  errors the uncertainty would have been badly understated and β3 might have looked
  "significant." The correction kept the inference honest.

### Limitations
- **Small n** (28 quarters) — treat p-values as directional, not definitive.
- **Single-series design, no control** — results are associations, not causal effects.
- **HAC is asymptotic** — the autocorrelation correction is approximate at this sample size.

### Bottom line
> A rigorous interrupted time-series finds a pre-existing upward trend and a level shift
> coincident with Measure 110, **but the shift is confounded by the national fentanyl supply
> surge (and possibly a linear-fit artifact), so there is no defensible evidence that Measure
> 110 altered the fentanyl overdose-death trajectory.** The disciplined null — and a clear
> account of *why* causal attribution isn't warranted — is the finding.

## Buprenorphine & naloxone (treatment / harm-reduction response)

*(to be added once those models are run — this is the "response" side, where a policy effect
is more plausible; note the Medicaid-unwinding confound on buprenorphine post-2023.)*
