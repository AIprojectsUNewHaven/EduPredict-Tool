#  EduPredict Pro

**AI Degree Program Planning & Decision Intelligence Tool**

A professional dashboard for College Deans to evaluate launching AI degree programs.

![EduPredict Dashboard](https://img.shields.io/badge/Streamlit-Live%20App-FF4B4B?logo=streamlit)

---

## What It Does

EduPredict helps higher education leadership make data-driven decisions about launching AI degree programs:

- **3-Year Enrollment Forecasting** - Project student enrollment across scenarios
- **ROI Analysis** - Calculate tuition revenue vs. program costs
- **Workforce Intelligence** - State-level AI job market data
- **Go/No-Go Recommendations** - Data-driven decision support
- **Professional Reports** - Downloadable PDF reports for presentations

---

##  Live Demo

**Try it live:** [Insert Streamlit Cloud URL here after deployment]

---

##  Inputs (5 Simple Dropdowns)

1. **Program Type:** MS in AI, BS in AI, AI in Cybersecurity
2. **Student Type:** International or Domestic
3. **Academic Term:** FA26 (Fall 2026), SP27 (Spring 2027), FA28 (Fall 2028)
4. **Scenario:** Baseline, Optimistic, Conservative
5. **State:** CT (Connecticut), NY (New York), MA (Massachusetts)

---

##  Outputs

- **Enrollment Projection:** 3-year forecast with **prediction intervals** (e.g., "40 students, range: 15-65")
- **Confidence Score:** 0-100% with risk level (low/medium/high)
- **Warning Flags:** Model tells you when it's uncertain
- **3-Year Pool:** Total projected candidate pool
- **ROI Ratio:** Return on investment with financial risk assessment
- **Workforce Outlook:** Job growth, demand level, salary data
- **Recommendation:** STRONG GO / GO / CONDITIONAL / RECONSIDER / **DO NOT LAUNCH**

##  Key Feature: Honest Predictions

Unlike typical forecasting tools, EduPredict **admits when it's uncertain**:
- Shows prediction ranges, not just point estimates
- Flags scenarios with low confidence
- Tells you "DO NOT LAUNCH" when ROI is poor
- Explains why predictions are risky

---

##  Technology Stack

- **Frontend:** Streamlit
- **Visualizations:** Plotly (3D charts, interactive graphs)
- **Data Processing:** Pandas, NumPy
- **Reports:** FPDF2 (PDF generation)
- **Data Sources:** BLS 2023, IPEDS 2023-2024

---

##  Run from GitHub (No Installation Required)

### Option 1: GitHub Codespaces (Recommended - Runs in Browser)

1. Go to your repo: `https://github.com/GaneshMunagala714/Edupredict-Pro`
2. Click the ** green "<> Code" button**
3. Select **"Codespaces"** tab
4. Click **"Create codespace on main"**
5. Wait 1-2 minutes for setup
6. The app auto-starts at port 8501
7. Click **"Open in Browser"** when prompted

 **Done!** The app runs entirely in GitHub's cloud - no local setup needed.

### Option 2: Run Locally

```bash
# Clone the repository
git clone https://github.com/GaneshMunagala714/Edupredict-Pro.git
cd Edupredict-Pro

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run ui/app.py
```

The app will open at `http://localhost:8501`

---

##  Deployment

### Deploy to Streamlit Cloud (Recommended)

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Select `ui/app.py` as the main file
5. Deploy!

---

##  Success Criteria

**Test Scenario:** MS in AI + International + FA26 + Baseline + CT

**Expected Output:**
- Year 1: 40 students (range: ~15-65)
- Confidence: ~65% (Moderate)
- 3-Year Pool: 131 students
- ROI: 3.43x
- Recommendation: **STRONG GO**

**Low Confidence Test:** BS in AI + Domestic + SP27 + Optimistic + CT
- Should show: Confidence < 55%, Warning flags, CAUTION recommendation

---

##  Professional Reports

Generate and download PDF reports including:
- Executive Summary
- Key Metrics (Enrollment, ROI, Confidence)
- Financial Analysis (Revenue, Costs, Payback)
- Workforce Outlook
- Recommendation

---

##  For Professors

This tool demonstrates:
- Data-driven decision making
- Financial modeling for higher education
- Workforce market analysis
- Interactive data visualization
- Professional reporting

---

##  Data Sources

- **BLS Occupational Employment Statistics** (May 2023)
- **IPEDS Institutional Data** (2023-2024)
- **Industry Job Market Reports**

---

*Built with ❤️ for higher education leadership*
