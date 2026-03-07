# EduPredict Pro

**AI Degree Program Planning & Decision Intelligence Tool**

A professional dashboard for College Deans to evaluate launching AI degree programs. Built with Streamlit, Plotly 3D, and Python.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31-FF4B4B?logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Live Demo

| Platform | Link |
|----------|------|
| **Streamlit Cloud** | [Launch App](https://edupredict-pro.streamlit.app) |
| **GitHub Codespaces** | [Open in Codespaces](https://github.com/codespaces/new?repo=GaneshMunagala714%2FEdupredict-Pro) |
| **AWS EC2** | [Deployment Guide](AWS-DEPLOY.md) |

---

## What It Does

EduPredict helps higher education leadership make data-driven decisions about launching AI degree programs:

- **3-Year Enrollment Forecasting** with prediction intervals and confidence scores
- **ROI Analysis** with financial risk flags and break-even calculations
- **Workforce Intelligence** -- state-level AI job market data (CT, NY, MA)
- **Honest Recommendations** -- STRONG GO / GO / CONDITIONAL / RECONSIDER / DO NOT LAUNCH
- **Uncertainty Quantification** -- the model admits when it's uncertain
- **Professional PDF Reports** -- downloadable executive summaries

---

## Inputs (5 Dropdowns)

| Input | Options |
|-------|---------|
| Program Type | MS in AI, BS in AI, AI in Cybersecurity |
| Student Type | International, Domestic |
| Academic Term | FA26 (Fall 2026), SP27 (Spring 2027), FA28 (Fall 2028) |
| Scenario | Baseline, Optimistic, Conservative |
| State | CT (Connecticut), NY (New York), MA (Massachusetts) |

**162 total input combinations**, all validated.

---

## Outputs

- **Enrollment Projection** -- 3-year forecast with prediction ranges (e.g., "40 students, range: 15-65")
- **Confidence Score** -- 0-100% with risk level (low/medium/high)
- **Warning Flags** -- model explains when and why it's uncertain
- **ROI Ratio** -- return on investment with financial risk assessment
- **Workforce Outlook** -- job growth, demand level, salary data
- **Recommendation** -- STRONG GO / GO / CONDITIONAL / RECONSIDER / DO NOT LAUNCH
- **3D Visualizations** -- interactive scenario surfaces and state comparisons
- **PDF Report** -- downloadable executive summary

---

## Key Feature: Honest Predictions

Unlike typical forecasting tools, EduPredict **admits when it's uncertain**:
- Shows prediction ranges, not just point estimates
- Flags scenarios with low confidence
- Tells you "DO NOT LAUNCH" when ROI is poor
- Explains why predictions are risky

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit |
| Visualizations | Plotly (3D surfaces, interactive charts) |
| Data Processing | Pandas, NumPy |
| Reports | FPDF2 (PDF generation) |
| Data Sources | BLS 2023, IPEDS 2023-2024 |
| Deployment | Streamlit Cloud, AWS EC2, Docker |

---

## Run Locally

```bash
git clone https://github.com/GaneshMunagala714/Edupredict-Pro.git
cd Edupredict-Pro
pip install -r requirements.txt
streamlit run ui/app.py
```

Opens at `http://localhost:8501`

---

## Deploy

### Option 1: Streamlit Cloud (Recommended -- Free & Permanent)

1. Fork or push this repo to your GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select repo: `Edupredict-Pro`, branch: `main`, file: `ui/app.py`
5. Click Deploy

### Option 2: AWS EC2 (Student Account)

See [AWS-DEPLOY.md](AWS-DEPLOY.md) for the full step-by-step guide.

Quick version: Launch a t2.micro, paste the user-data script, open port 8501. App auto-deploys in ~3 minutes.

### Option 3: Docker

```bash
docker build -t edupredict-pro .
docker run -p 8501:8501 edupredict-pro
```

### Option 4: GitHub Codespaces

Click "Create codespace on main" from the repo page. The app auto-starts.

---

## Project Structure

```
Edupredict-Pro/
├── ui/app.py                  # Main Streamlit dashboard
├── models/
│   ├── forecasting.py         # Enrollment forecasting engine
│   ├── roi_calculator.py      # ROI and financial analysis
│   └── job_market.py          # Workforce intelligence
├── data/raw/                  # CSV data files (BLS, IPEDS)
├── tests/                     # Validation tests
├── .streamlit/config.toml     # Streamlit theme config
├── Dockerfile                 # Docker deployment
├── ec2-userdata.sh            # AWS EC2 auto-deploy script
├── index.html                 # GitHub Pages landing page
└── requirements.txt           # Python dependencies
```

---

## Success Criteria

**Test:** MS in AI + International + FA26 + Baseline + CT

| Metric | Expected |
|--------|----------|
| Year 1 Enrollment | ~40 students (range: ~15-65) |
| Confidence | ~65% (Moderate) |
| 3-Year Pool | ~131 students |
| ROI | ~3.43x |
| Recommendation | STRONG GO |

---

## Data Sources

- **BLS Occupational Employment Statistics** (May 2023)
- **IPEDS Institutional Data** (2023-2024)
- **Industry Job Market Reports**

---

## Author

**Ganesh Munagala** -- [GitHub](https://github.com/GaneshMunagala714) | [Portfolio](https://ganeshmunagala714.github.io/Ganesh-Portfolio)

Built for higher education leadership decision-making.
