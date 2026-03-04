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

- **Enrollment Projection:** 3-year forecast with Year 1, 2, 3 breakdown
- **3-Year Pool:** Total projected candidate pool
- **ROI Ratio:** Return on investment calculation
- **Workforce Outlook:** Job growth, demand level, salary data
- **Recommendation:** STRONG GO / GO / CONDITIONAL / RECONSIDER

---

##  Technology Stack

- **Frontend:** Streamlit
- **Visualizations:** Plotly (3D charts, interactive graphs)
- **Data Processing:** Pandas, NumPy
- **Reports:** FPDF2 (PDF generation)
- **Data Sources:** BLS 2023, IPEDS 2023-2024

---

##  Running Locally

```bash
# Clone the repository
git clone https://github.com/GaneshMunagala714/Edupredict.git
cd Edupredict

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
- Year 1: 40 students
- 3-Year Pool: 131 students
- ROI: 3.43x
- Recommendation: **STRONG GO**

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
