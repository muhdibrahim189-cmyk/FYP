# SPK Viva Slides – Content

Structure follows the Nur Izzah viva deck (section dividers: Introduction → Literature Review → Methodology → Result & Discussion → Conclusion → Q&A), with the Parcel2Go deck's comparative table and per-role "how it works" flow.
Each slide lists: **On slide** (text to place), **Visual** (file in `Dissertation/Figures/` or `Demo Videos/`), **Say** (speaker note).
Target: ~28 slides, 15–20 minutes.

---

## 1. Title

**On slide**
- SISTEM PEMANTAUAN KARBON (SPK): DIGITAL CARBON ACCOUNTING PLATFORM FOR EMISSIONS TRACKING AND REPORTING
- By: Muhammad Ibrahim Al-Imran Bin Mohd Isa (22006656)
- Bachelor of Computer Science (Hons)
- Sept 2026 – FYP II Viva Presentation
- Supervisor: Dr Noreen Izza Bt Arshad
- Internal Examiner: ____________
- External Examiner: ____________

---

## 2. Content Overview

**On slide**
1. Introduction
2. Literature Review
3. Methodology
4. Result & Discussion
5. Conclusion & Future Work
6. Q & A

---

## 3. Section divider – INTRODUCTION

Project Background, Problem Statement, Objectives, Scope of Study

---

## 4. Project Background

**On slide** (three big-number callouts + one short paragraph)
- **MYR 15 / tonne CO2e**: proposed Malaysian carbon tax rate (iron, steel and energy first) [5]
- **220 Mt CO2e**: Scope 1 + 2 emitted by the five case companies in 2025 (about **MYR 3.3 bn / year** at MYR 15/t)
- **Mandatory carbon accounting**: the Climate Change Bill sets up an MRV system [6], [7]

Paragraph: Budget 2026 confirmed a carbon tax, and NSRF / IFRS S2 and EU CBAM are making emissions disclosure stricter. Most organisations, especially SMEs, still track emissions in spreadsheets or one-off calculators.

**Visual:** `fig1_1_annual_emissions.png`
**Say:** Policy is moving faster than practice. Once a tax applies, the emission figures turn into a cost, so they have to be accurate and traceable.

---

## 5. Problem Statement

**On slide** (four boxes)
1. **Fragmented manual records.** Spreadsheets spread across departments. Free calculators (SEDG, MGTC, Maybank) give a one-off footprint with no history and no checks [21], [25]–[27]
2. **Not auditable.** A reported total cannot be traced back to the bill, the emission factor or the person who entered and approved it [28]
3. **Retrospective only.** Annual reports come after the year ends, with no forecast, no what-if scenarios and no tax figure next to the emissions [29]–[31]
4. **Hard for non-specialists.** Managers and officers are not experts in scopes or factors, and plain LLMs can hallucinate figures [32], [33]

**Proposed solution (banner):** SPK is a role-based web platform. It calculates Scope 1 and 2 emissions and carbon tax, screens every entry, keeps an audit ledger, forecasts six months ahead and explains the figures through a grounded AI advisor.

---

## 6. Objectives

**On slide**
| # | Keyword | Objective |
|---|---|---|
| 01 | DEVELOP | Build a carbon accounting tool that computes Scope 1 and 2 emissions and carbon tax with Malaysian SEDG factors, with role-based access for company, government and IT users |
| 02 | TRACE | Create a structured database with an auditable data-lineage ledger and an approval workflow |
| 03 | PREDICT | Build STIRPAT (ridge) forecasting six months ahead, a what-if simulator and a grounded AI advisor |
| 04 | EVALUATE | Verify the calculations with unit tests and assess usability with UAT and the System Usability Scale |

---

## 7. Scope of Study

**On slide** (four quadrants, as in the Nur Izzah deck)
- **FOCUS AREA:** Scope 1 and Scope 2 only (no tax proposal covers Scope 3, and Scope 3 data is the least reliable [34])
- **CASE DATA:** 5 oil & gas companies (bp, Chevron, ConocoPhillips, Equinor, ExxonMobil). Annual data for 2021–2025 disaggregated to months; 2026 is a synthetic year
- **USERS:** Company user, Government officer, IT administrator (demo accounts)
- **DELIVERABLES:** Local working prototype (Python, Streamlit, SQLite); flat MYR 15/t tax, adjustable; UAT with 20 students
- **Out of scope:** production hosting, SSO, integration with government systems

---

## 8. Section divider – LITERATURE REVIEW

---

## 9. Literature Review – Key Findings

**On slide**
| Area | Key finding | Relevance to SPK |
|---|---|---|
| GHG Protocol & SEDG [2], [25] | Scope 1/2/3 boundaries; CO2e = activity × factor | Calculation basis; SEDG factors used |
| Emission factor choice [16], [26], [27], [39] | Peninsular grid factor is 0.774 (SEDG), 0.740 (MGTC) or 0.78 (Maybank) depending on the calculator | One documented factor set; record the edition |
| Carbon software adoption [22], [47] | Cost, integration and skills shortages block SMEs (enterprise deployments > USD 500k) | Lightweight, browser-based, no integration needed |
| Anomaly detection [59]–[61] | Thresholds based on standard deviation adapt to each series | Transparent z-score rule that an approver can read |
| STIRPAT + ridge [35], [36], [62], [66] | Driver-based forecasting; ridge handles correlated drivers | Applied at company-month level, which is rarely done |
| Temporal disaggregation [76]–[78] | Denton method gives monthly values that sum to annual totals | Monthly series from annual reports |
| Grounded AI [33] | ChatClimate: grounding improves answer accuracy | Advisor answers only from data on the user's page |

---

## 10. Comparative Study

**On slide** (Table 2.1)
| Feature | SEDG calc | MGTC SME calc | Maybank calc | Company data hubs | SPK |
|---|---|---|---|---|---|
| Scope 1 & 2 from activity data | ✓ | ✓ | ✓ | ✗ | ✓ |
| Malaysian emission factors | ✓ | ✓ | ✓ | ✗ | ✓ |
| Several organisations in one view | ✗ | ✗ | ✗ | ✗ | ✓ |
| Monthly time series | ✗ | ✗ | – | Annual | ✓ |
| Forecast | ✗ | ✗ | – | ✗ | ✓ |
| What-if scenarios | ✗ | ✗ | – | ✗ | ✓ |
| Carbon tax in MYR | ✗ | Indicative | – | ✗ | ✓ |
| Validation & approval | ✗ | ✗ | – | – | ✓ |
| Role-based access & audit log | ✗ | ✗ | – | – | ✓ |
| Conversational AI | ✗ | ✗ | – | ✗ | ✓ |

**Research gap (footer):** (1) no auditable, validated ledger in Malaysian tools; (2) STIRPAT is rarely applied at company-month level; (3) no grounded AI over live carbon dashboard data.

---

## 11. Section divider – METHODOLOGY

Methodology, Timeline, Tools, System Diagrams

---

## 12. Agile Scrum – Five Sprints

**On slide**
| Sprint | Period | Deliverable |
|---|---|---|
| S1 | 19–25 Sep | Rebuild in Python, Streamlit and SQLite: login, data entry, calculator, first unit tests |
| S2 | 6–8 Oct | Five-company workbook; STIRPAT ridge forecast; revised what-if levers |
| S3 | 15–23 Oct | SEDG factors; duplicate rule; Groq AI chatbot; seeded ledger; PDF tax statement |
| S4 | 24 Oct – 9 Nov | Company / government / IT roles with row-level filtering; security fixes |
| S5 | 11–20 Nov | UAT with 20 respondents; defect fixes |

**FYP I → FYP II changes:** React/Node + JSON → Python/Streamlit/SQLite · synthetic facilities → real reported data from 5 companies · in-company roles → company / government / IT · fixed-ratio rule → z-score · OLS trend → STIRPAT

**Visual:** `fig3_1_agile.png`

---

## 13. Project Timeline (Gantt Chart)

**Visual:** `figA_gantt.png` (full slide)
**On slide (milestones strip):** Wk 6 Progress Assessment 1 · Wk 9 Draft dissertation & technical paper · Wk 10 Soft-bound dissertation · Wk 12 Presentation / PA2 · Wk 14 Hard-bound dissertation
**Say:** The supervisor asked for the timeline. Sprint dates come from the git history.

---

## 14. Tools Used

**On slide** (icon row)
| Tool | Role |
|---|---|
| Python 3.12 | Calculation, analytics and forecasting logic |
| Streamlit | Web interface, routing, session state |
| SQLite | Ledger, approval queue, activity log (transactional) |
| pandas / NumPy / scikit-learn | Data handling; ridge regression |
| Plotly | Interactive line, bar, area and heatmap charts |
| ReportLab | PDF carbon tax statement |
| Groq API (GPT-OSS 120B) | AI advisor chat |
| unittest, VS Code, Git/GitHub | Testing, development, version control |

---

## 15. System Architecture

**Visual:** `fig3_2_architecture.png`
**On slide (four layers)**
- **Data Ingestion:** login router, data entry form, workbook loader
- **Application Processing Engine:** Quantification Unit (CO2e, tax, anomaly check) · Predictive Unit (STIRPAT) · Prescriptive What-If AI Scenario Engine
- **Database & Reference Lookup:** SQLite ledger (3 tables) + read-only company workbook
- **Output Dashboard UI:** Main Dashboard, What-If Simulator, Sustainability, Data Centre, plus a floating AI chat
**Say:** The logic modules do not import Streamlit, which is why they can be unit-tested.

---

## 16. Use Case & Role Permissions

**Visual:** `fig3_4_usecase.png`
**On slide** (Table 3.5)
| Capability | Company | Government | IT admin |
|---|---|---|---|
| Companies visible | Own | All | All |
| Submit emission data | ✓ | ✗ | ✓ |
| Approve / reject flagged entries | Own | View only | ✓ |
| Generate PDF tax statement | ✗ | ✓ | ✓ |
| View audit log | ✗ | ✗ | ✓ |

---

## 17. Data Pipeline & Database

**Visual:** `fig3_3_pipeline.png` (left) + `fig3_5_erd.png` (right)
**On slide**
- Two input paths: **reported data** (annual reports → Denton disaggregation → workbook) and **operational entry** (form → validate → CO2e → screen → ledger or approval queue)
- No manually entered value changes a dashboard total until it is screened or approved
- Tables: `emissions` (ledger) · `pending_submissions` · `activity_log`. Rows are never deleted; replaced and withdrawn entries keep their status

---

## 18. Core Logic – Calculation, Anomaly Screening, Forecast

**On slide**
- **Emissions:** CO2e (kg) = Activity × SEDG factor · **Tax:** MYR = CO2e ÷ 1000 × rate
- **Anomaly rule:** z = |x − μ| ÷ σ; flag if z > 2.5 (≥ 5 approved records); otherwise fall back to the same scope; one entry per source per month (duplicate rule)
- **STIRPAT:** ln I = αᵢ + b ln P + c ln A + d ln T (+ company trend for Scope 2), ridge λ = 0.005
  - P = production · A = revenue · T = energy intensity
  - Train on 2021–2024, test on 2025, refit on 2021–2025, forecast Jan–Jun 2027

**Visual:** `fig3_6_activity.png` or `fig3_7_stirpat_workflow.png`

---

## 19. Grounded AI Advisor

**Visual:** `fig3_8_sequence_chatbot.png`
**On slide**
- The page builds a plain-text summary of exactly what it shows: KPIs, totals, forecast and accuracy
- The summary is built from rows the user's role is allowed to see, so no other company's data reaches the model
- System prompt: quote page numbers only, never invent figures, say when data is missing, keep answers short
- A rate-limited request is retried once; a failed request returns a safe message

---

## 20. Section divider – RESULT & DISCUSSION

Product Demo, System Interface, Forecast Accuracy, Testing, UAT

---

## 21. Product Demo

**On slide:** "How it works": one short clip per role
- Demo 1: Company User (`Demo Videos/Demo_1_Company_User.mp4`)
- Demo 2: Government Officer (`Demo_2_Government_Officer.mp4`)
- Demo 3: IT Administrator (`Demo_3_Administrator.mp4`)
**Say:** Have the clips ready offline. Fall back to the screenshots on the next slides if playback fails.

---

## 22. System Interface – Login, Dashboard, Restricted Access

**Visual:** `scr_login.png`, `scr_dashboard.png`, `scr_restricted.png`
**On slide (captions)**
- LOGIN PAGE: demo accounts for the three roles
- MAIN DASHBOARD: KPI cards (Total, Scope 1, Scope 2, Carbon Tax), monthly trend with dashed STIRPAT forecast
- ACCESS RESTRICTED: a government officer cannot open Data Entry

---

## 23. System Interface – Data Entry, Anomaly, Approval

**Visual:** `scr_entry.png`, `scr_anomaly.png`, `scr_approval.png`
**On slide (captions)**
- DATA ENTRY: live CO2e and tax estimate (100 GJ natural gas = 5,620 kg CO2e = MYR 84.30)
- ANOMALY FLAG: 15,100 L of diesel flagged at **414.1σ** above its mean of 1,507 L
- APPROVAL QUEUE: approve or reject, with the reason shown

---

## 24. System Interface – What-If, AI Advisor, Data Centre & PDF

**Visual:** `scr_whatif.png`, `scr_chatbot.png`, `scr_report_pdf.png` (optional: `scr_heatmap.png`, `scr_activity.png`)
**On slide (captions)**
- WHAT-IF: 20% less natural gas + 20% fleet EV + 10% less electricity → **−7.7%** emissions, with the tax saving shown
- AI ADVISOR: "Highest Scope 1?" → ExxonMobil, 88.10 Mt (matches the dashboard)
- PDF STATEMENT: company details, monthly emissions, carbon tax invoice
- AUDIT LOG (IT only): every login, submission, approval and withdrawal

---

## 25. Dataset Overview

**Visual:** `fig4_1_monthly_panel.png`
**On slide**
- 5 companies × 72 months = 360 rows (2021–2025 disaggregated, 2026 synthetic)
- Combined total fell from 230.4 Mt (2021) to 220.1 Mt (2025), a **4.5%** decrease
- **94.6%** of emissions are Scope 1, so a direct-emissions tax would capture most of the footprint
- ExxonMobil = 46.0% of the total · 2021–2026 = 1,315.94 Mt = **MYR 19.74 bn** at MYR 15/t

---

## 26. Forecasting Results – STIRPAT vs OLS Baseline

**Visual:** `fig4_2_stirpat_test.png` (+ `fig4_3_stirpat_forecast.png` small)
**On slide**
| Test year 2025 | Scope 1 | Scope 2 | Total |
|---|---|---|---|
| STIRPAT WAPE | **1.45%** | **11.12%** | **1.51%** |
| OLS trend WAPE | 6.40% | 18.33% | 6.81% |
| Seasonal naive WAPE | 4.26% | 12.30% | 3.69% |
| Test R² | 0.9991 | 0.9843 | 0.9992 |

- Elasticities (Scope 1): production **0.86**, energy intensity **0.89**, revenue **−0.06**. Emissions follow physical activity, not oil prices
- Forecast Jan–Jun 2027: **108.91 Mt** (+1.1% on Jan–Jun 2026)
- ⚠ Caveat: the monthly data is disaggregated and the test year uses actual drivers, so real-world accuracy will be lower
**Say:** WAPE is the main metric because Scope 2 values close to zero inflate MAPE (39%).

---

## 27. Unit & System Testing

**Visual:** `evd_unit_tests.png` + `evd_system_test.png`
**On slide**
| Module | Passed |
|---|---|
| test_core | 7/7 |
| test_auth | 4/4 |
| test_ai_helper | 3/3 |
| test_simulation | 9/9 |
| test_report | 7/7 |
| test_analytics | 29/29 |
| test_data_manager | 19/19 |
| **Total** | **78/78 (~3 s)** |

- Recorded system test (19 min, 56 black-box cases): **52 pass, 2 fail, 2 partial**
- Failures: TC-SUS-07 (power entry flagged as duplicate), TC-SUS-08 (no undo confirmation)

---

## 28. User Acceptance Testing – Results

**Visual:** `fig4_respondents.png`, `fig4_uat_outcomes.png`, `fig4_sus_scores.png`
**On slide**
- **SETTINGS:** 20 respondents (CS/IT, petroleum, chemical, business and others); 56 test cases in 6 modules; 10-item SUS; 10 feature statements; 3 open questions
- **97.3%** of executed test cases passed (1,015 pass / 28 fail / 77 not tested)
- **SUS mean 77.4** (SD 9.1), above the benchmark of 68, between "Good" and "Excellent"; 17 of 20 respondents scored ≥ 68
- **80%** agree SPK helps prepare for Malaysia's carbon tax · **80%** say it is better than spreadsheets
- Lowest scores: data entry & flagged entries (3.15), trust in the figures (3.25)

---

## 29. UAT – Defects & Qualitative Feedback

**Visual:** `fig4_likert.png`
**On slide**
| Theme | Feedback |
|---|---|
| STRENGTHS | What-If Simulator (6), AI chatbot (4): "shows the tax saving of each action" |
| CONFUSION | Sustainability vs Data Centre unclear (5); re-login opens the last page (5) |
| WANTED | Excel upload of monthly data (3); company users download their own statement (3) |

| Defect | Fails | Status |
|---|---|---|
| TC-SUS-07 power entry flagged as duplicate | 11 | Open |
| TC-SUS-08 undo has no confirmation | 9 | Fixed, to be re-tested |
| TC-SUS-05 ten-times value not flagged | 1 | Fixed (scope-level fallback + unit test) |

---

## 30. Section divider – CONCLUSION

Conclusion, Future Work, References

---

## 31. Conclusion & Future Work

**On slide** (three columns, as in the Nur Izzah deck)
- **ACHIEVEMENT (all 4 objectives met):**
  - Role-based Scope 1 & 2 + carbon tax platform (12/12 FRs)
  - Auditable SQLite ledger with z-score screening and approval
  - STIRPAT forecast (1.51% WAPE vs 6.81% OLS), what-if simulator, grounded AI advisor
  - 78/78 unit tests, 97.3% UAT pass, SUS 77.4
- **IMPACT:**
  - Regulators get one view of emissions, forecasts and tax exposure across companies
  - Companies can validate data before reporting and test reduction actions without enterprise software
  - Academic: STIRPAT applied at company-month level
- **LIMITATIONS:**
  - Disaggregated / synthetic data
  - 5 non-Malaysian companies
  - Student testers
  - Local demo accounts
- **FUTURE WORK:**
  - Excel/CSV upload and self-service statements
  - Hashed passwords, SSO, MFA
  - Bahasa Malaysia and tooltips
  - Measured monthly data, Scope 3, ML comparison
  - Hosted PostgreSQL
  - Systematic evaluation of the AI advisor

---

## 32. References (selected)

[2] WRI & WBCSD, *GHG Protocol Corporate Standard*, 2004.
[5] The Star, "Carbon tax rate of RM15 a tonne being considered," Nov. 2025.
[6] Bernama, "National Climate Change Bill unveils MRV system…," Mar. 2026.
[16] Suruhanjaya Tenaga, "Grid emission factor (GEF) in Malaysia," 2024.
[25] Capital Markets Malaysia, *SEDG GHG Emissions Calculator User Guide*, 2025.
[26] MGTC, "SME carbon footprint calculator," 2026.
[33] S. A. Vaghefi et al., "ChatClimate: Grounding conversational AI in climate science," *Commun. Earth Environ.*, 2023.
[35] D. Kong et al., "Forecasting urban carbon emissions using an Adaboost-STIRPAT model," *Front. Environ. Sci.*, 2023.
[36] C. Rao et al., "…STIRPAT extended model with ridge regression…," *Environ. Sci. Pollut. Res.*, 2023.
[62] T. Dietz & E. A. Rosa, "Rethinking the environmental impacts of population, affluence and technology," *Hum. Ecol. Rev.*, 1994.
[76] F. T. Denton, "Adjustment of monthly or quarterly series to annual totals…," *J. Amer. Statist. Assoc.*, 1971.
[83] J. Brooke, "SUS: A 'quick and dirty' usability scale," in *Usability Evaluation in Industry*, 1996.

---

## 33. Q & A

## 34. THANK YOU!

---

## Appendix – likely examiner questions (prep, not slides)

1. **Why STIRPAT and not ML/LSTM?** 5 companies × 60 reported months is too little data for ML; STIRPAT is interpretable (elasticities) and established [35], [36], [69], [72].
2. **Isn't 1.5% WAPE too good?** Yes, and the dissertation says so. The disaggregation used a shared activity shock and the test year used actual drivers. It shows the model fits the annual relationships, not true monthly accuracy.
3. **Why z-score over an ML anomaly detector?** Few historical points per source, and every flag has to be explainable to the person approving it [59].
4. **Why non-Malaysian companies?** They publish consistent Scope 1/2, production, revenue and energy data every year. The Malaysian context comes from the SEDG factors and the MYR rate.
5. **How do you stop the AI from hallucinating?** It is grounded in the page's own numbers, gets role-filtered data only, and its prompt forbids invented figures; 124/126 chatbot test executions passed. A systematic evaluation is future work.
6. **Security?** Row-level filtering before any page or the chatbot sees data, constant-time password compare, parameterised SQL, HTML escaping, CSV formula neutralisation, API key in an environment variable. Demo accounts in code are a stated limitation.
7. **Why does emission factor choice matter?** SEDG 0.774 vs MGTC 0.740 differs by 34 t per GWh (MYR 510). An MRV system needs one official factor set.
8. **What is still open?** TC-SUS-07 (the seeded energy rows cause duplicate flags), plus three minor UI issues.
