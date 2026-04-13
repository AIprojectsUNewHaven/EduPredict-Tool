# EduPredict MVP - Data Dictionary

Documentation of all data sources and fields.

## bls_salary_data.csv

**Description:** Bureau of Labor Statistics salary data for tech occupations

**Source:** [BLS Occupational Employment and Wage Statistics (May 2023)](https://www.bls.gov/oes/)

### Fields

- `state`: State abbreviation (CT, NY, MA)
- `occupation_code`: BLS SOC code (15-1250 = Computer Occupations, 15-1256 = Data Scientists)
- `occupation_name`: Job title/description
- `median_salary`: Median annual wage (USD)
- `mean_salary`: Mean annual wage (USD)
- `year`: Data year (2023)

---

## ipeds_institutions.csv

**Description:** List of 4-year institutions in CT, NY, MA

**Source:** [IPEDS Institutional Characteristics](https://nces.ed.gov/ipeds/)

### Fields

- `unitid`: IPEDS unique institution identifier
- `institution_name`: Official institution name
- `state`: State abbreviation
- `institution_type`: Public or Private
- `sector`: Institution sector (4-year only for MVP)

---

## ipeds_real.csv

**Description:** Real IPEDS-derived enrollment extract for the tri-state universe (processed by `data/process_ipeds_real.py`).

**Source:** [IPEDS Data Center](https://nces.ed.gov/ipeds/)

See `data/process_ipeds_real.py` for column expectations and outputs under `data/processed/`.

---

## job_market_data.csv

**Description:** AI/tech job market indicators by state

**Source:** [BLS Employment Projections + industry analysis](https://www.bls.gov/emp/)

### Fields

- `state`: State abbreviation
- `ai_job_growth_5yr`: Projected AI job growth percentage (2023-2028)
- `tech_job_growth_5yr`: Projected tech job growth percentage
- `demand_level`: Qualitative demand assessment
- `open_positions_sample`: Sample count of open AI-related positions
- `top_employers`: Major employers hiring for AI roles

---

