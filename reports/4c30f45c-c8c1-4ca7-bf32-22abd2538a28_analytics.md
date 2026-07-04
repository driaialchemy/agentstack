# Governed Analytics Report (Synthetic Demo)

**Workflow:** Structured data analytics
**Data source:** Synthetic structured database
**Accountability owner:** dr mike

## Findings
- EDA: The synthetic dataset contains 8 structured records and 12 monthly observations. Revenue shows an upward demo trend across the monthly series. This is synthetic data for governed demonstration only.
- Regression: Revenue increases by about $2,970 per period in this synthetic demo series (R-squared=0.96). This is a simple linear fit for demonstration, not a production forecasting model.
- Forecast: Projected 3 future periods using a simple seasonal/cyclical demo model. This Fourier-style projection demonstrates seasonality and cyclical patterns on synthetic data. It is not guaranteed prediction and must not be treated as a production forecast.

## Governance notes
- Workflow executed through governed skills, policy engine, and gate engine.
- Accountability owner: dr mike.
- All agent steps logged to audit_log.jsonl.

## Limitations
- Synthetic demo data only.
- Single-feature linear model; real drivers are not modeled.
- Do not use for business decisions.
- This Fourier-style projection demonstrates seasonality and cyclical patterns on synthetic data. It is not guaranteed prediction and must not be treated as a production forecast.
- Model complexity is intentionally minimal for governance demonstration.
- Synthetic structured data only.
- Governed demo workflow; not client-ready analysis.

_This report was generated from synthetic structured data as a governed demonstration._