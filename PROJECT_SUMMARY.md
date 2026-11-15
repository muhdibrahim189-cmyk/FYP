# Sistem Pemantauan Karbon (SPK): Project Summary

**Final Year Project (FYP), Universiti Teknologi PETRONAS · Department of Computer and Information Sciences**
**Supervisor:** Dr. Noreen Izza Arshad · **Period:** Sep–Nov 2026 (5 Scrum sprints)

## One-line description

A role-based web platform that tracks Scope 1 and Scope 2 greenhouse gas emissions, calculates Malaysian carbon tax exposure, forecasts emissions with a STIRPAT ridge-regression model and answers user questions through an AI advisor that only quotes the figures shown on the user's page.

## The problem

Malaysia announced a carbon tax in Budget 2026 (MYR 15 per tonne CO₂e), and the National Climate Change Bill requires measurement, reporting and verification (MRV). Most organisations still keep emission data in spreadsheets or use one-off calculators (SEDG, MGTC, Maybank). These calculators do not validate inputs, keep a history over time, forecast emissions or work out tax liability across organisations.

## What I built

| Feature | What it does |
|---|---|
| **Emission and tax calculation** | Converts activity data (fuel litres, kWh) to CO₂e using Malaysian SEDG emission factors, then applies the carbon tax rate |
| **Anomaly detection** | Z-score rule (\|z\| > 2.5) against approved history, with a scope-level fallback for new sources and a duplicate-month check. Flagged entries go to an approval queue |
| **Auditable ledger** | Records are never deleted; every submission, approval, rejection and withdrawal is logged, so each total can be traced to its source |
| **Role-based access control** | 3 roles: company user (sees own data only), government officer (all companies, issues tax statements, cannot enter data), IT admin (adds audit log access) |
| **STIRPAT forecasting** | Ridge regression (λ = 0.005) on production, revenue and energy intensity; 6-month forecast; chronological 80/20 train/test split |
| **What-If Simulator** | Sliders for 8 reduction levers (fuel cuts, EV fleet, renewables, efficiency) showing simulated emissions and tax savings |
| **AI advisor (chatbot)** | GPT-OSS 120B via the Groq API. Each question is sent with the figures on the current page, filtered by the user's role, which keeps answers grounded and avoids hallucinated numbers. Retries on rate limits and falls back gracefully when the API is offline |
| **PDF carbon tax statement** | 3-part ReportLab report: company details, monthly emissions with chart, tax invoice with the amount in words |
| **Dashboards** | KPI cards, monthly trend + forecast, company × month heatmap, carbon tax analysis (Plotly) |
| **Data export** | CSV export with formula-injection protection |

## Tech stack

- **Language:** Python 3.12
- **Web framework:** Streamlit (multi-page app with custom navigation)
- **Data and ML:** pandas, NumPy, scikit-learn (Ridge regression)
- **Database:** SQLite
- **Visualisation:** Plotly
- **Reporting:** ReportLab (PDF generation)
- **AI/LLM:** Groq API (OpenAI-compatible), GPT-OSS 120B, prompt engineering, retrieval-style grounding with page data
- **Testing:** 78 unit tests (unittest), black-box system testing, user acceptance testing
- **Process:** Scrum (5 sprints), Git version control

## Dataset

Annual 2021–2025 emission, production, revenue and energy data for 5 oil and gas companies (bp, Chevron, ConocoPhillips, Equinor, ExxonMobil), taken from their published annual and ESG reports and disaggregated into months with the Denton method so the months add up to the reported annual totals. In total: **1,315.94 Mt CO₂e**, equal to **MYR 19.74 billion** in carbon tax at MYR 15/t.

## Key results (numbers to put on a resume)

- **Forecast accuracy:** STIRPAT WAPE of **1.51%** for total emissions on the held-out 2025 data, against **6.81%** for a linear trend baseline (over 75% lower error). Scope 1 1.45%, Scope 2 11.12%, test R² up to 0.999.
- **Unit tests:** **78/78 passed**
- **System testing:** **52 of 56** recorded test cases passed
- **User acceptance testing (20 participants):** **97.3%** of executed test cases passed
- **Usability:** mean **System Usability Scale score of 77.4** (rated "Good" to "Excellent")
- **80%** of users agreed the platform would help an organisation prepare for the carbon tax
- All **12 functional requirements** implemented
- Wrote a **dissertation** and an academic **technical paper** on the project

## Resume bullet points (ready to copy)

**Sistem Pemantauan Karbon: Digital Carbon Accounting Platform** | Python, Streamlit, scikit-learn, SQLite, Groq LLM API

- Built a role-based web platform that calculates Scope 1/2 GHG emissions and Malaysian carbon tax liability from activity data, with an auditable approval ledger for MRV compliance
- Developed a STIRPAT ridge-regression forecasting model that reached 1.51% WAPE on held-out data, 78% lower error than a linear-trend baseline
- Implemented z-score anomaly detection and duplicate checks that route suspicious entries to an approval queue before they affect totals
- Integrated an LLM chatbot (GPT-OSS 120B via Groq) grounded in the user's live dashboard data and limited by role permissions, so it only quotes figures the user can see
- Built a what-if scenario simulator and automated PDF carbon tax statement generation (ReportLab)
- Wrote 78 unit tests (all passing); in user acceptance testing with 20 participants, 97.3% of test cases passed and the mean SUS score was 77.4

**Short version (one line):**
Developed a carbon emission monitoring and carbon tax platform (Python/Streamlit/ML/LLM) with STIRPAT forecasting (1.51% error), anomaly detection, role-based access and a data-grounded AI advisor; SUS usability score of 77.4.

## Skills shown

Full-stack Python development · Machine learning and time-series forecasting · Regression modelling · Data engineering (ETL from company reports) · LLM integration and prompt engineering · Role-based access control and audit logging · Data validation and anomaly detection · Data visualisation · Software testing (unit, system, UAT) · Agile/Scrum · Technical and academic writing · ESG / carbon accounting domain knowledge (GHG Protocol, Scope 1 and 2)
