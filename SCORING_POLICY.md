# RMI Scoring Policy

Authoritative reference for how scores, caps, and evidence rules are applied.
The code in `backend/scoring_engine_v2.py` implements this policy. If they
disagree, **this document wins** — file a bug.

---

## 1. Framework

Five domains, three subdomains each. Overall RMI is a weighted mean of domain
scores; domain scores are unweighted means of their subdomains.

| Domain | Name | Default weight |
|---|---|---|
| WC | Workforce Capability | 0.20 |
| LC | Leadership & Culture | 0.20 |
| WM | Work Management | 0.20 |
| AI | Asset Information | 0.20 |
| SG | Strategy & Governance | 0.20 |

Industry modules override these (see `INDUSTRY_WEIGHTS` in `scoring_engine_v2.py`).

## 2. Score scale

| Range | Level | Label |
|---|---|---|
| 1.00–1.99 | 1 | Reactive |
| 2.00–2.99 | 2 | Emerging |
| 3.00–3.59 | 3 | Systematic |
| 3.60–4.29 | 4 | Proactive |
| 4.30–5.00 | 5 | Prescriptive |

## 3. Role weighting

Responses are weighted by the respondent's role. The sum of role weights is
1.00.

| Role | Weight |
|---|---|
| Technician | 0.35 |
| Supervisor | 0.20 |
| Manager | 0.15 |
| Planner | 0.15 |
| Reliability Engineer | 0.15 |

Question weight (`question.weight`, default 1.0) multiplies the role weight.

## 4. Evidence policy

A response with `numeric_score >= 4` on a question where `evidence_required`
is true contributes its score to the subdomain only if `evidence_status` is
`ACCEPTED`. Otherwise the score is **soft-capped at 3.0** for the purpose of
that response's contribution.

| `evidence_status` | High score (>=4) effect |
|---|---|
| `accepted` | Score counts as-is |
| `pending_verification` | Capped at 3.0 |
| `pending_evidence` | Capped at 3.0 |
| `rejected` | Capped at 3.0 |
| `not_required` | Should not appear when `evidence_required=True`; treated as cap |

Low scores (< 4) are unaffected by the evidence cap.

### Evidence grade multiplier

If an `evidence_grade` (A–D) is set, the score is multiplied:

| Grade | Multiplier |
|---|---|
| A | 1.00 |
| B | 0.95 |
| C | 0.85 |
| D | 0.75 |

## 5. Weakest-link caps

A single critical failure can cap an entire domain. Defined in
`CRITICAL_CAPS`. Triggers:

| Question | Trigger | Domain cap | Reason |
|---|---|---|---|
| LC.2-01 | score == 1 | LC ≤ 2.0 | No stop-work authority |
| WM.3-03 | score ≤ 2 | WM ≤ 3.0 | LOTO compliance failure |
| AI.1-01 | score == 1 | AI ≤ 1.5 | No CMMS |
| SG.1-01 | score == 1 | SG ≤ 2.0 | No written AM policy |
| WC.1-01 | score == 1 | WC ≤ 2.5 | No equipment training |

## 6. Cross-domain caps

| If… | Then cap… | Cap | Reason |
|---|---|---|---|
| AI < 2.0 | WC, LC, WM, SG | 4.0 | Cannot verify maturity without data systems |
| LC < 2.0 | WM, WC | 3.5 | Poor leadership undermines work management & training |
| SG < 2.0 | Overall RMI | 3.5 | No strategy means no sustained improvement |

## 7. Confidence band

Confidence starts at 1.0 and is reduced by:

| Factor | Penalty |
|---|---|
| QuickScan mode | -0.25 |
| Evidence gaps (responses pending evidence) | up to -0.30 |
| Cultural blind spot (variance ≥ 2.0) | -0.30 per |
| Cultural blind spot (variance ≥ 1.5) | -0.15 per |

Floor at 0.30. The confidence band shown in reports is
`overall ± (1 - confidence)`.

## 8. Cultural blind spot detection

For each subdomain with responses from at least two distinct roles, compare
role-mean scores. A spread of ≥1.5 is logged as a warning blind spot; ≥2.0 is
critical.

## 9. Maturity velocity

Compares this assessment's overall RMI to the most recent prior assessment
for the same site (matched by `site_name`). Reported as RMI per month and
classified as Stable / Improving / Rapid Improvement / Declining / Rapid Decline.

## 10. Hard caps not in this document

If you find a magic number in the code that is not documented here, **that is
a bug** — open a PR that either removes it or adds it to this doc.
