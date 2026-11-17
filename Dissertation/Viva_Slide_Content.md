# SPK – FYP II Viva Slide Content

Structure follows the Sept '25 viva example (Nur Izzah's deck): title → content overview → section dividers for Introduction, Literature Review, Methodology, Results & Discussion (with product demo), Conclusion → Q&A → Thank you. It also covers the Form 13 presentation items (problem, objectives and scope, literature, methodology, results, conclusion, product demo).

Each slide lists **On slide** (keep it short, examiners read it), **Visual** (file in `Dissertation/Figures/` unless stated) and **Say** (speaker notes). Every figure and number comes from the dissertation (FYP_Dissertation_Ibrahim_22006656.pdf).

Target: about 30 main slides for 20–25 min including the demo. The backup slides go after "Thank you" and are only shown if asked.

---

## 1. Title

**On slide**
- SISTEM PEMANTAUAN KARBON (SPK): Digital Carbon Accounting Platform for Emissions Tracking and Reporting
- By: Muhammad Ibrahim Al-Imran Bin Mohd Isa (22006656)
- Bachelor of Computer Science (Hons)
- SEPT 2026 – FYP II VIVA PRESENTATION
- Supervisor: Dr Noreen Izza Bt Arshad
- Internal Examiner: [name] · External Examiner: [name]

**Visual:** UTP logo; small screenshot of the dashboard (`scr_dashboard.png`) as background or side image.

---

## 2. Content Overview

**On slide**
1. Introduction
2. Literature Review
3. Methodology
4. Results & Discussion (product demo)
5. Conclusion & Future Work
6. Q & A

---

## 3. INTRODUCTION *(section divider)*

Project Background, Problem Statement, Objectives, Scope of Study

---

## 4. Project Background

**On slide** (stat-card layout, like slide 4 of the example)
- **MYR 15 / tonne CO2e**: carbon tax rate under consideration; Budget 2026 targets iron, steel and energy first
- **Climate Change Bill**: introduces an MRV system and makes carbon accounting mandatory
- **28%** of global emissions were under a direct carbon price in 2025 (World Bank)
- **220 Mt CO2e**: emitted by the 5 case oil and gas companies in 2025, about **MYR 3.3 billion** a year at MYR 15/t
- Disclosure pressure: NSRF (2024), IFRS S2 (from 1 Jan 2025), EU CBAM for exporters

**Visual:** `fig1_1_annual_emissions.png`

**Say:** The tax was delayed in mid-2026, but the Ministry of Finance said in June 2026 that the policy is in its final phase. Whatever the final date, companies will need audited Scope 1 and 2 figures, and most still keep them in spreadsheets.

---

## 5. Problem Statement

**On slide** (four boxes)
1. **Fragmented, manual tracking.** Spreadsheets and one-off calculators (SEDG, MGTC, Maybank) work out one footprint at a time, keep no history and never check new values against past ones.
2. **Not auditable.** A reported total cannot be traced back to the invoice, the emission factor, or the person who entered and approved it. MRV needs data that can be verified.
3. **Retrospective only.** Annual reports come out after year end, with no forecast, no what-if scenarios and no carbon tax shown next to emissions.
4. **Hard for non-specialists to interpret.** Officers and managers are not experts in scopes or factors, and LLMs can give plausible but false answers unless they are grounded in real data.

**Say:** Each problem maps to one objective on the next slide.

---

## 6. Objectives

**On slide**
1. Develop an online carbon accounting tool that **ingests activity data and computes Scope 1 and 2 emissions and carbon tax** with Malaysian SEDG factors, with **role-based access** for company, government and IT users.
2. Create a **structured database with an auditable data-lineage ledger and approval workflow**, so every figure can be traced to its submission, emission factor and approval.
3. Build **AI-driven forecasting and scenario modelling**: a STIRPAT ridge-regression forecast six months ahead, a what-if simulator for carbon tax mitigation and an AI advisor chat grounded in platform data.
4. **Verify** the calculations with automated unit tests and **evaluate** usability and usefulness through UAT with the System Usability Scale (SUS).

---

## 7. Scope of Study

**On slide** (four columns: Focus / Data / Users / Boundaries)
- **Focus:** Scope 1 and Scope 2 only. No tax proposal covers Scope 3, and Scope 3 data is the least reliable.
- **Data:** 5 international O&G companies (bp, Chevron, ConocoPhillips, Equinor, ExxonMobil). Annual 2021–2025 data disaggregated into months; 2026 is a synthetic year.
- **Tax:** flat MYR 15/t on Scope 1 + 2, adjustable on the dashboard. Thresholds and sector coverage are not modelled because they have not been announced.
- **Users:** 3 demo roles: Company user, Government officer, IT administrator.
- **Boundaries:** working local prototype (Streamlit + SQLite). No production hosting, SSO or government system integration. UAT with 20 students.

**Say (significance):** For regulators it gives one view of emissions, forecasts and tax exposure across companies, which supports the planned MRV system. For companies it validates data before reporting without the cost of enterprise software. Academically, STIRPAT is normally used at country or province level; here it is applied per company per month.

---

## 8. LITERATURE REVIEW *(section divider)*

Carbon accounting & policy, existing tools, methods, research gap

---

## 9. Literature Review (1/2): Carbon Accounting and Policy

**On slide** (table: Title | Focus / Findings | Relevance to SPK)

| Source | Focus / Findings | Relevance |
|---|---|---|
| GHG Protocol Corporate Standard (WRI & WBCSD, 2004) | Defines Scope 1 (direct), Scope 2 (purchased energy), Scope 3 (value chain) | Sets the scope boundary of SPK |
| SEDG GHG Calculator (Capital Markets Malaysia, 2025); Energy Commission GEF (2024) | Activity × factor method; grid factors 0.774 (Peninsular), 0.525 (Sabah), 0.199 (Sarawak) kg CO2e/kWh | Source of all SPK emission factors |
| Stachelscheid & Dutzi (2025) | 102 companies: Scope 2 location vs market-based reporting is inconsistent | Record the basis of each figure; Chevron is market-based |
| Marlowe & Clarke (2022); McDonald et al. (2024) | Carbon accounting lacks transparency, reliability and comparability | Motivates the auditable ledger |
| Green (2021); Döbbeling-Hildebrandt et al. (2024) | Carbon pricing reduces emissions: 5–21% across 21 schemes | Why tax visibility matters |
| Market.us (2026); Intel Market Research (2026) | Enterprise tools cost > USD 500k; SMEs face cost, integration and skill barriers | Lightweight, browser-based design |

---

## 10. Literature Review (2/2): Methods

**On slide**

| Source | Focus / Findings | Relevance |
|---|---|---|
| Blázquez-García et al. (2021) | Estimation-based outlier detection: each series gets its own threshold (k × σ) | Z-score anomaly rule |
| Dietz & Rosa (1994); York et al. (2003) | STIRPAT: I = a·P^b·A^c·T^d·e; log form gives elasticities; extensible | Forecasting model |
| Rao et al. (2023); Kong et al. (2023) | Ridge-regression STIRPAT handles correlated drivers; λ = 0.005, 80/20 split | Model estimator and settings |
| Hewamalage et al. (2023) | MAPE is unstable when values are near zero | WAPE as the main error measure |
| Denton (1971); Eurostat (2026) | Temporal disaggregation: monthly series that sum to annual totals | Annual reports → monthly data |
| Vaghefi et al. (2023) ChatClimate; Huang et al. (2025) | Grounding an LLM in authoritative data improves accuracy; LLMs hallucinate | Page-grounded AI advisor |

---

## 11. Comparative Study

**On slide** (simplified Table 2.1)

| Feature | SEDG calc. | MGTC SME calc. | Maybank calc. | Company data hubs | SPK |
|---|:-:|:-:|:-:|:-:|:-:|
| Scope 1 & 2 from activity data | ✓ | ✓ | ✓ | ✗ | ✓ |
| Malaysian emission factors | ✓ | ✓ | ✓ | ✗ | ✓ |
| Several organisations in one view | ✗ | ✗ | ✗ | ✗ | ✓ |
| Time series | ✗ | ✗ | – | Annual | Monthly |
| Forecast + what-if scenarios | ✗ | ✗ | – | ✗ | ✓ |
| Carbon tax liability (MYR) | ✗ | Indicative | – | ✗ | ✓ |
| Validation + approval of data | ✗ | ✗ | – | – | ✓ |
| Role-based access + audit log | ✗ | ✗ | – | – | ✓ |
| Conversational AI assistant | ✗ | ✗ | – | ✗ | ✓ |

**Say:** MGTC's own disclaimer says its result "is not verified and cannot be relied upon for regulatory reporting, audit or financial decision making".

---

## 12. Research Gap

**On slide**
1. Malaysian tools produce a footprint for one organisation but **no auditable, validated ledger**, which an MRV system needs.
2. STIRPAT has been validated at **national, provincial and city level on annual data**, rarely at **company level on monthly series**, and has not been built into a monitoring tool.
3. Grounded AI works best on authoritative sources, but it **has not been applied to a carbon dashboard's live data**.

→ SPK addresses all three on one platform.

---

## 13. METHODOLOGY *(section divider)*

Development approach, Gantt chart, tools, system design, core logic, testing

---

## 14. Development Methodology: Agile Scrum

**On slide**

| Sprint | Period | Main deliverable |
|---|---|---|
| S1 | 19–25 Sep 2026 | Python + Streamlit rebuild, login, SQLite data entry, calculator, first unit tests |
| S2 | 6–8 Oct 2026 | Five-company workbook, STIRPAT ridge forecast with train/test metrics, revised levers |
| S3 | 15–23 Oct 2026 | SEDG factors, duplicate rule, Groq chatbot, seeded ledger, PDF tax statement |
| S4 | 24 Oct – 9 Nov 2026 | Company, government and IT roles with row-level filtering; shared Page base class; security fixes |
| S5 | 11–20 Nov 2026 | UAT with 20 respondents, defect fixes |

**Visual:** `fig3_1_agile.png`

**Say:** Scrum suited the project because ingestion, validation, forecasting and the AI advisor are loosely coupled and could be built one sprint at a time. Each sprint was reviewed with the supervisor. Sprint dates come from the Git history.

---

## 15. Gantt Chart (FYP II)

**Visual:** `figA_gantt.png`

**On slide** (milestones strip): Progress Assessment 1 (W6) · Draft dissertation + technical paper (W9) · Soft-bound dissertation (W10) · Project presentation (W12) · Hard-bound dissertation (W14)

---

## 16. What Changed from FYP I to FYP II

**On slide** (two-column "FYP I → FYP II")

| FYP I prototype | FYP II final |
|---|---|
| React + Node.js, state in a JSON file | Python + Streamlit + SQLite (transactional ledger) |
| Synthetic data for 3 facilities | Reported data from 5 O&G companies, 2021–2025 |
| Fixed-ratio plausibility rule (×4 / ÷10) | Adaptive z-score rule + duplicate-month check |
| OLS linear trend forecast | STIRPAT ridge regression (OLS kept as baseline) |
| In-company roles (Clerk, Manager, Executive) | Company, Government officer, IT admin (follows the Climate Change Bill) |
| 3 what-if levers | 8 levers mapped to SEDG emission sources |

**Say:** These changes are why objectives 2 and 3, only partly done at the end of FYP I, are now achieved.

---

## 17. Tools Used

**On slide** (icon row like example slide 13)
- **Python 3.12**: all logic, models and UI in one language
- **Streamlit**: multi-page web UI, session state
- **SQLite**: ledger, approval queue, activity log
- **pandas / NumPy / scikit-learn**: data handling, ridge regression
- **Plotly**: interactive charts and heatmap
- **ReportLab**: PDF carbon tax statement
- **Groq API (GPT-OSS 120B)**: AI advisor
- **unittest, Git/GitHub, VS Code, Microsoft Forms**: testing, version control, UAT questionnaire

---

## 18. System Architecture

**Visual:** `fig3_2_architecture.png`

**On slide** (four layers)
1. **Data Ingestion Layer**: router with login and role check, data-entry form, workbook loader
2. **Application Processing Engine**: Quantification Unit (CO2e, tax, anomaly checks), Predictive Unit (STIRPAT), Prescriptive What-If AI Scenario Engine (levers + Groq)
3. **Database & Reference Lookup**: SQLite ledger (3 tables) + read-only company workbook
4. **Output Dashboard UI**: Main Dashboard, What-If Simulator, Sustainability, Data Centre, plus a floating AI chat

**Say:** The calculation modules do not depend on Streamlit, which is why they can be unit-tested.

---

## 19. End-to-End Data Pipeline

**Visual:** `fig3_3_pipeline.png`

**On slide**
- **Reported path:** company reports → Denton disaggregation to months → workbook → loader checks → dashboard, forecast, simulator
- **Operational path:** company user enters activity data → validated → converted to CO2e → screened against approved history → saved to ledger **or** held for approval
- Manually entered data cannot change any total until it has been screened or approved

---

## 20. Use Case Diagram & Access Control

**Visual:** `fig3_4_usecase.png`

**On slide** (Table 3.5 condensed)

| Capability | Company | Government | IT admin |
|---|:-:|:-:|:-:|
| Companies visible | Own | All | All |
| Submit emission data | ✓ | ✗ | ✓ |
| Approve / reject flagged entries | Own | View only | ✓ |
| Generate PDF tax statement | ✗ | ✓ | ✓ |
| View audit log | ✗ | ✗ | ✓ |

**Say:** Rows are filtered by role *before* any page, export or the chatbot sees them, so a company user's question can never send another company's data to the LLM. Logout clears the whole session.

---

## 21. Emissions & Carbon Tax Calculation

**On slide**
- CO2e (kg) = Activity data × Emission factor
- Tax (MYR) = [CO2e (kg) ÷ 1,000] × Rate (MYR/t)

| Source | Unit | kg CO2e / unit |
|---|---|---|
| Stationary natural gas | GJ | 56.2 |
| Mobile diesel | L | 2.909 |
| Mobile petrol | L | 2.288 |
| Grid electricity, Peninsular (TNB) | kWh | 0.774 |
| Grid electricity, Sarawak | kWh | 0.199 |

**Say:** All 23 factors come from the SEDG calculator guide and are already in CO2e, so the AR6 GWPs are not applied a second time. Fuel counts as Scope 1 and electricity as Scope 2. Worked example: 100 GJ of natural gas = 5,620 kg CO2e = MYR 84.30.

---

## 22. Anomaly Detection & Approval Workflow

**Visual:** `fig3_6_activity.png`

**On slide**
- z = |x − μ| ÷ σ against the **approved history of the same source**
- Flag if **≥ 5 approved records and z > 2.5**
- Fewer than 5 records → compare CO2e with other sources in the same scope (fallback added after UAT)
- Same source + same month already submitted → **duplicate flag**
- Flagged → `pending_submissions` with a written reason → approve / reject
- Nothing is deleted: entries are marked *replaced* or *withdrawn*

**Say:** I chose a transparent z-score rule over a learned detector because each source has only a few history values and every flag has to be explained to the person approving it. Blázquez-García et al. call this an estimation-based method.

---

## 23. Forecasting Model: STIRPAT with Ridge Regression

**Visual:** `fig3_7_stirpat_workflow.png`

**On slide**
- STIRPAT: I = a · P^b · A^c · T^d · e
- Estimated form: ln I = αᵢ + b ln P + c ln A + d ln T + ε
  - I = monthly emissions, P = production, A = revenue, T = energy intensity, αᵢ = company fixed effect
  - Scope 2 model adds a company-specific yearly trend (renewable purchases are not captured by P, A, T)
- Ridge regression, λ = 0.005 (Kong et al.), because the drivers are correlated
- Chronological 80/20 split: **train Jan 2021 – Dec 2024, test 2025**
- Metrics: WAPE (main), MAPE, RMSE, R². Baseline: OLS trend per series
- Forecast Jan–Jun 2027 after refitting on 2021–2025; drivers repeat last year's growth

---

## 24. AI Advisor Chat & What-If Simulator

**Visual:** `fig3_8_sequence_chatbot.png`

**On slide**
- **AI advisor (GPT-OSS 120B via Groq)**
  - Each question carries a plain-text summary of **only what the page shows** for the current filters and role
  - System prompt: quote page numbers only, never invent figures, say when data is missing, keep answers short
  - Rate limit → one retry; failure → safe message, the page keeps working
- **What-If Simulator**: 8 levers (natural gas, diesel, petrol, LPG, fleet EV, electricity reduction, renewable share, efficiency)
  - E_sim = E_base × (1 − mean lever fraction for the record's source)
  - Tax saving = tonnes reduced × tax rate

---

## 25. Testing & Evaluation Approach

**On slide** (three levels)
1. **Unit testing**: 78 automated tests (unittest) on the calculator, auth, analytics, simulation, report and data manager. Database tests run on a temporary SQLite file.
2. **System testing**: 56 black-box test cases run by the developer in a screen-recorded session, each verdict logged against its time in the recording.
3. **User acceptance testing**: 20 respondents, demo accounts, Microsoft Forms questionnaire: 56 test cases (Pass / Fail / Not tested), 10-item SUS, 10 feature statements, satisfaction, 3 open questions.

**On slide (formula):** SUS = 2.5 × [Σ odd (r − 1) + Σ even (5 − r)], benchmark average = 68

---

## 26. RESULTS & DISCUSSION *(section divider)*

Product demo, system interface, forecasting results, testing, UAT

---

## 27. Product Demo

**On slide:** PRODUCT DEMO

**Visual / play:** `Dissertation/Demo Videos/`
- `Demo_1_Company_User.mp4`: data entry, anomaly flag, approval queue
- `Demo_2_Government_Officer.mp4`: all-company dashboard, PDF tax statement, access restriction
- `Demo_3_Administrator.mp4`: activity and audit log
- (backup) `Demo_4_Code_Walkthrough.mp4`

**Say:** If live demo is allowed, run the app (`streamlit run app.py`) and use the videos as a fallback. Suggested live path: log in as a company user → enter 15,100 L diesel → show the anomaly flag → approve → log in as government → generate the PDF → ask the chatbot "which company has the highest Scope 1?".

---

## 28. System Interface (1/3): Login, Access & Dashboard

**Visual:** `scr_login.png` + `scr_restricted.png` | `scr_dashboard.png`

**On slide**
- Login with role-based demo accounts; out-of-role pages show "Access Restricted"
- Main Dashboard: KPI cards (total, Scope 1, Scope 2, carbon tax), monthly trend with a dashed 6-month STIRPAT forecast, company heatmap, tax chart
- Sidebar filters: year, company, scope, tax rate

---

## 29. System Interface (2/3): Data Entry, Anomaly & Approval

**Visual:** `scr_entry.png` | `scr_anomaly.png` | `scr_approval.png`

**On slide**
- Live CO2e, tonnes and tax preview while typing
- Example: 15,100 L diesel (about 10× the usual amount) flagged at **414.1σ** above a mean of 1,507.1 ± 32.8 L
- Approval queue cards: quantity, CO2e, tax exposure, submitter, reason, Approve / Reject

---

## 30. System Interface (3/3): What-If, Data Centre, PDF & AI Advisor

**Visual:** `scr_whatif.png` | `scr_report_pdf.png` | `scr_chatbot.png`

**On slide**
- What-If: 20% less natural gas + 20% fleet EV + 10% less electricity → **−7.7%** emissions, compared with 3.8%, 3.8% and 0.2% for each lever alone
- Data Centre: search, filters, CSV export (formula-injection safe), 3-part PDF carbon tax statement
- AI advisor: "highest Scope 1?" → ExxonMobil, 88.10 Mt (2026), **matches the dashboard**

---

## 31. Dataset Overview

**Visual:** `fig4_1_monthly_panel.png`

**On slide**

| Company | Total (Mt CO2e) | Share | Tax at MYR 15/t |
|---|---:|---:|---:|
| ExxonMobil | 605.69 | 46.0% | MYR 9.09 bn |
| Chevron | 334.51 | 25.4% | MYR 5.02 bn |
| bp | 201.84 | 15.3% | MYR 3.03 bn |
| ConocoPhillips | 108.00 | 8.2% | MYR 1.62 bn |
| Equinor | 65.90 | 5.0% | MYR 0.99 bn |
| **Total 2021–2026** | **1,315.94** | 100% | **MYR 19.74 bn** |

- **94.6%** of emissions are Scope 1, so a first-phase tax on direct emissions would capture most of the footprint
- Combined total fell **4.5%**, from 230.4 Mt (2021) to 220.1 Mt (2025)
- 2026 values are synthetic and labelled as such on the dashboard

---

## 32. Forecasting Results: Accuracy on Held-Out 2025

**Visual:** `fig4_2_stirpat_test.png`

**On slide**

| Measure | Scope 1 | Scope 2 | Total |
|---|---:|---:|---:|
| Test R² | 0.9991 | 0.9843 | 0.9992 |
| **STIRPAT test WAPE** | **1.45%** | **11.12%** | **1.51%** |
| OLS trend WAPE (FYP I method) | 6.40% | 18.33% | 6.81% |
| Seasonal naive WAPE | 4.26% | 12.30% | 3.69% |

- About **77–78% lower error** than the OLS trend for Scope 1 and total, and about 39% lower for Scope 2
- Scope 2 MAPE is 39.29% because Scope 2 values are small, which is why WAPE is the main measure (Hewamalage et al.)

**Say:** The OLS line ignores seasonality and extends the downward trend, so it underestimates every month of 2025. Be upfront here: STIRPAT used the actual 2025 drivers, while the baselines only used past emissions. Its advantage shows how well the drivers explain emissions; a real forecast also depends on forecasting the drivers.

---

## 33. Interpreting the Elasticities & Six-Month Forecast

**Visual:** `fig4_3_stirpat_forecast.png`

**On slide**
- Scope 1: a **1% rise in production → +0.86%** emissions; **1% rise in energy intensity → +0.89%**; revenue has almost no effect (−0.055%)
  - Emissions follow physical activity and energy use, not oil prices. This agrees with Kong et al. (Shandong), where energy factors had the highest elasticities.
- Scope 2 elasticities are larger but offset by the company trend terms, so they should not be read on their own
- **Forecast Jan–Jun 2027: 108.91 Mt CO2e (+1.1%** vs Jan–Jun 2026), with the usual January and March peaks
- ⚠ Monthly data was disaggregated with a shared activity shock and 2026 drivers are synthetic, so the accuracy is optimistic for real monthly data. Both caveats are shown on the dashboard and given to the AI advisor.

---

## 34. Unit & System Testing

**Visual:** `evd_unit_tests.png` | `evd_system_test.png`

**On slide**
- **78 / 78 unit tests passed** (about 3 s): core 7, auth 4, AI helper 3, simulation 9, report 7, analytics 29, data manager 19
- **System test: 52 of 56 passed**, 2 failed, 2 partial (19-minute screen recording)
  - Failed: TC-SUS-07 (power consumption entry flagged as a duplicate), TC-SUS-08 (no undo confirmation)
  - Partial: TC-DC-03 (filters look unticked), TC-DC-07 (no-data case cannot occur with this data)
- The same defects were later reported by UAT respondents, so the system test predicted UAT well

---

## 35. User Acceptance Testing: Respondents & Outcomes

**Visual:** `fig4_respondents.png` | `fig4_uat_outcomes.png`

**On slide**
- **20 respondents**: 6 CS/IT, 4 petroleum eng., 4 chemical eng., 4 business, 2 other. 13 tried all three roles
- Non-specialists: familiarity with Scope 1/2 was 3.05 / 5, with the carbon tax 2.80 / 5
- **1,120 judgements: 97.3% of executed test cases passed** (1,015 pass, 28 fail, 77 not tested)
- **No failures** in authentication & access or the What-If Simulator
- 20 of the 28 fails came from two Sustainability cases (TC-SUS-07: 11, TC-SUS-08: 9)

---

## 36. System Usability Scale & Feature Evaluation

**Visual:** `fig4_sus_scores.png` | `fig4_likert.png`

**On slide**
- **Mean SUS = 77.4** (SD 9.1, median 78.8), above the 68 benchmark, between "Good" and "Excellent" (Bangor et al.). 17 of 20 scored ≥ 68
- Highest agreement:
  - Helps prepare for Malaysia's carbon tax: **4.05, 80% agree**
  - Better than spreadsheets / manual reporting: **3.85, 80% agree**
  - Dashboard charts 3.90 (70%), What-If Simulator 3.85 (70%)
- Lowest: data entry & flagged entries **3.15 (40%)**, trust in figures **3.25 (40%)**
- Overall satisfaction 3.85 / 5 (65% satisfied)

**Say:** The low data-entry score matches where the two main defects are; they affected 15 of the 20 respondents. Moderate trust in the figures is reasonable, because the monthly values are disaggregated and 2026 is synthetic.

---

## 37. Qualitative Feedback

**On slide** (three columns)
- **Most useful:** What-If Simulator (6), because it shows the tax saving of each action; AI chatbot (4), valued by those with little carbon knowledge
- **Confusing:** Sustainability vs Data Centre page (5); re-login opens the last page instead of the dashboard (5); negative tax rate shows a red box with no message (4)
- **Most wanted:** monthly upload from Excel (3); company users download their own tax statement (3); password reset (2); Bahasa Malaysia (2)

---

## 38. Achievement of Objectives

**On slide**

| Objective | Status | Evidence |
|---|---|---|
| 1. Automated Scope 1/2 + tax platform with roles | ✅ Achieved | 12/12 functional requirements; arithmetic unit-tested; 0 fails in 218 executed access tests |
| 2. Auditable ledger + anomaly screening + approval | ✅ Achieved | SQLite ledger with submitter, approver, status; z-score + duplicate rules; activity log |
| 3. STIRPAT, what-if, AI advisor | ✅ Achieved | WAPE 1.51% vs 6.81% (OLS); 0 fails in 138 simulator tests; 124/126 chatbot tests passed |
| 4. Unit tests + UAT evaluation | ✅ Achieved | 78/78 unit tests; 52/56 system tests; 97.3% UAT pass; SUS 77.4 |

**Say (link to theory):** Every output traces back to a published factor and a stated formula, which addresses the opacity problem raised by Marlowe & Clarke. Emission factor choice also has a direct cost: for 1 GWh on the Peninsular grid, SEDG (0.774) and MGTC (0.740) differ by 34 t, or MYR 510. A national MRV system needs one official factor set, and SPK keeps its factors in one module so they can be updated.

---

## 39. CONCLUSION *(section divider)*

Conclusion, Limitations, Future Work

---

## 40. Conclusion, Limitations & Future Work

**On slide** (three columns like example slide 31: System Achievement / Limitations / Future Work)

**System achievement**
- Role-based carbon accounting from activity data with Malaysian SEDG factors
- Auditable ledger with anomaly screening and approval
- STIRPAT forecast (1.51% WAPE), What-If Simulator, grounded AI advisor, PDF tax statement
- 78/78 unit tests · 97.3% UAT pass · SUS 77.4 · 80% say it helps prepare for the carbon tax

**Limitations**
- Accuracy measured on disaggregated monthly data, a synthetic 2026 and known test-year drivers
- 5 non-Malaysian O&G companies; Scope 2 basis differs (Chevron market-based)
- UAT with 20 students, not officers or company staff
- Demo accounts in code; runs locally on SQLite
- AI answer quality checked in tests, not assessed systematically

**Future work (priority order)**
1. Excel/CSV monthly upload with the same validation; self-service tax statement; email alerts
2. Hashed credentials, password reset, SSO + MFA
3. Bahasa Malaysia UI, tooltips, clearer page names
4. Measured monthly data, market-based Scope 2, Scope 3, compare with ML / time-series models
5. Hosted deployment on PostgreSQL; align with the final policy and official factors
6. Systematic accuracy testing of the AI advisor; add Malaysian regulations as a grounded source

---

## 41. References *(key ones only, IEEE numbering as in the dissertation)*

- [2] WRI & WBCSD, *GHG Protocol Corporate Standard*, 2004.
- [6] Bernama, "National Climate Change Bill unveils MRV system…", 2026.
- [25] Capital Markets Malaysia, *SEDG GHG Emissions Calculator User Guide*, 2025.
- [28] J. Marlowe & A. Clarke, "Carbon accounting: A systematic literature review…", *Green Finance*, 2022.
- [33] S. A. Vaghefi et al., "ChatClimate: Grounding conversational AI in climate science", *Commun. Earth Environ.*, 2023.
- [35] D. Kong et al., "Forecasting urban carbon emissions using an Adaboost-STIRPAT model", *Front. Environ. Sci.*, 2023.
- [59] A. Blázquez-García et al., "A review on outlier/anomaly detection in time series data", *ACM Comput. Surv.*, 2021.
- [62] T. Dietz & E. A. Rosa, "Rethinking the environmental impacts of population, affluence and technology", 1994.
- [75] H. Hewamalage et al., "Forecast evaluation for data scientists", *Data Min. Knowl. Disc.*, 2023.
- [76] F. T. Denton, "Adjustment of monthly or quarterly series to annual totals", *JASA*, 1971.
- [83] J. Brooke, "SUS: A 'quick and dirty' usability scale", 1996.

---

## 42. Q & A

## 43. THANK YOU!

---

# Backup slides (after Thank You, show only if asked)

- **B1. ERD**: `fig3_5_erd.png`. `emissions` (the ledger), `pending_submissions`, `activity_log`; rows are never deleted.
- **B2. Full emission factor table**: Appendix D, 23 factors.
- **B3. Full STIRPAT table**: Table 4.2 with train R², MAPE, RMSE and all elasticities.
- **B4. UAT defect table**: Table 4.4 with cause and status. TC-SUS-07 open (the workbook already seeds total energy for every month to Dec 2026, so a new power entry is a duplicate); TC-SUS-08 fixed, to be re-tested; TC-SUS-05 fixed with the scope fallback and covered by a unit test. *Update the statuses if more fixes land before the viva.*
- **B5. Data disaggregation method**: first-difference additive Denton, weighted by days and a seasonal profile, AR(1) activity shock (σ 1%), check sheet confirms months sum to annual totals.
- **B6. Extra screenshots**: `scr_heatmap.png`, `scr_carbontax.png`, `scr_forecast.png`, `scr_ai_scenario.png`, `scr_activity.png`, `scr_datacentre.png`, `scr_report_ui.png`.

---

# Likely viva questions and where the answer is

| Question | Short answer |
|---|---|
| Why only Scope 1 and 2? | No tax proposal covers Scope 3; it is the least reliable data (Klaaßen & Stoll); GHG Protocol does not require it. |
| Why foreign O&G companies instead of Malaysian ones? | They publish annual Scope 1/2 with consistent production, revenue and energy data. Malaysian context comes from SEDG factors and the MYR rate. Listed as a limitation. |
| Isn't 1.51% WAPE too good to be true? | Partly, yes: the monthly data comes from disaggregation with a shared shock, and the test year used actual drivers. It shows the model reproduces annual relationships and seasonality, not that it predicts real measured monthly data within 1.5%. Stated in Section 4.3.3 and on the dashboard. |
| Why ridge and not OLS for STIRPAT? | P, A and T are highly correlated, so OLS coefficients are unstable. Ridge shrinks them (Hoerl & Kennard), λ = 0.005 following Kong et al. |
| Why not machine learning / LSTM? | 5 companies × 60 reported months is small; an interpretable model with elasticities suits regulators. ML comparison is listed as future work (Jin et al., M5 findings). |
| Why z-score, why 2.5, why 5 records? | Transparent and explainable to the approver, with a threshold per source. 2.5σ flags rare values without over-flagging; below 5 records σ is unreliable, so the scope-level fallback is used. |
| Why WAPE over MAPE? | MAPE blows up when values are near zero (Scope 2 MAPE 39.29% vs WAPE 11.12%), as Hewamalage et al. warn. |
| How do you stop the chatbot hallucinating or leaking data? | It receives only the page's figures, filtered by role first. The prompt forbids invented numbers, and the reminder is repeated next to each question. TC-AI-07 (privacy) passed for 19 of 19 who tested it. |
| What happens if the Groq API is down? | One retry on rate limit, then a safe message; the page keeps working (unit-tested, TC-AI-06). |
| Is it secure enough for production? | No. Demo accounts are in code. Constant-time password compare, parameterised SQL, HTML escaping, CSV formula neutralisation and an environment-variable API key are in place; hashed credentials, SSO and MFA are future work. |
| Why did data entry score lowest? | Two defects (TC-SUS-07, TC-SUS-08) hit 15 of 20 respondents. Fixing them would help more than adding any new feature. |
| Why Streamlit + SQLite instead of the FYP I React/Node stack? | Calculations, model and UI in one language; SQLite gives transactional writes with rollback for the ledger. Hosted multi-user use would need PostgreSQL. |
| Does the choice of emission factor matter? | Yes: SEDG 0.774 vs MGTC 0.740 is 34 t (MYR 510) per GWh. MRV needs one official set; SPK keeps them in one module. |
