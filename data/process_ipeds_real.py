"""
EduPredict - Real IPEDS Data Processor
Processes the wide-format IPEDS enrollment CSV (EF survey, 2014-2024)
into clean long-format CSVs and baseline JSON for the forecasting engine.

Input:  data/raw/ipeds_real.csv  (604 institutions, CT/NY/MA, 11 years)
Output:
  data/processed/grad_enrollment_trends.csv   -- long format, year x institution
  data/processed/state_summary.csv            -- state-level yearly totals
  data/processed/state_baselines.json         -- calibrated baselines for forecaster
"""

import csv
import json
import os
import re
from collections import defaultdict, Counter

RAW_PATH = os.path.join(os.path.dirname(__file__), "raw", "ipeds_real.csv")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "processed")

YEARS = list(range(2014, 2025))  # 2014-2024

# Keywords that identify non-degree-granting / vocational institutions
EXCLUDE_KEYWORDS = [
    "cosmetology", "beauty", "barber", "esthetics", "electrolysis",
    "massage", "nail", "hair", "vocational", "technical school",
    "boces", "nursing program", "medical assistant",
    "talmudic", "seminary", "yeshiva", "medrash", "rabbinical",
    "beis", "bnos", "bais", "beth medrash", "bet medrash",
    "funeral", "acting school",
]

# Legitimate degree-granting institutions that match exclude keywords
KEEP_EXCEPTIONS = {
    "yeshiva university",          # full university with grad school
    "jewish theological seminary of america",
    "union theological seminary in the city of new york",
    "gordon-conwell theological seminary",
    "holy apostles college and seminary",
    "new york theological seminary",
    "northeastern seminary",
}


def _is_degree_granting(name: str) -> bool:
    """Return True if this institution should be kept."""
    lower = name.lower()
    if lower in KEEP_EXCEPTIONS:
        return True
    return not any(kw in lower for kw in EXCLUDE_KEYWORDS)


def _parse_columns(header):
    """
    Map column index -> (year, level, metric) for enrollment columns.
    Header format: "Grand total (EF2024B  Graduate  All age categories total)"
    """
    col_map = {}
    year_re = re.compile(r"EF(\d{4})B")
    for idx, col in enumerate(header):
        m = year_re.search(col)
        if not m:
            continue
        year = int(m.group(1))
        level = "Graduate" if "Graduate" in col else "Undergraduate"
        if "Grand total" in col:
            col_map[idx] = (year, level)
    return col_map


def process():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # ------------------------------------------------------------------
    # Pass 1: Read raw CSV, build long-format records
    # ------------------------------------------------------------------
    long_records = []
    state_year_grad = defaultdict(lambda: {"total": 0, "count": 0})
    state_year_ug = defaultdict(lambda: {"total": 0, "count": 0})

    with open(RAW_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)

        # Identify fixed columns
        unitid_idx = header.index("UnitID")
        name_idx = header.index("Institution Name")
        state_idx = next(i for i, c in enumerate(header) if "State abbreviation" in c)

        col_map = _parse_columns(header)

        for row in reader:
            state = row[state_idx].strip()
            if state not in ("CT", "NY", "MA"):
                continue

            unitid = row[unitid_idx].strip()
            name = row[name_idx].strip()

            # Skip non-degree-granting institutions
            if not _is_degree_granting(name):
                continue

            for idx, (year, level) in col_map.items():
                raw_val = row[idx].strip()
                if not raw_val:
                    continue
                try:
                    enrollment = int(raw_val)
                except ValueError:
                    continue

                long_records.append({
                    "unitid": unitid,
                    "institution": name,
                    "state": state,
                    "year": year,
                    "level": level,
                    "enrollment": enrollment,
                })

                key = (state, year)
                if level == "Graduate":
                    state_year_grad[key]["total"] += enrollment
                    state_year_grad[key]["count"] += 1
                else:
                    state_year_ug[key]["total"] += enrollment
                    state_year_ug[key]["count"] += 1

    print(f"Long-format records: {len(long_records)}")

    # ------------------------------------------------------------------
    # Write long-format CSV
    # ------------------------------------------------------------------
    long_path = os.path.join(PROCESSED_DIR, "grad_enrollment_trends.csv")
    with open(long_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["unitid", "institution", "state", "year", "level", "enrollment"])
        writer.writeheader()
        writer.writerows(long_records)
    print(f"Saved: {long_path}")

    # ------------------------------------------------------------------
    # Write state summary CSV
    # ------------------------------------------------------------------
    summary_path = os.path.join(PROCESSED_DIR, "state_summary.csv")
    rows = []
    all_states = ["CT", "NY", "MA"]
    for state in all_states:
        for year in YEARS:
            key = (state, year)
            g = state_year_grad[key]
            u = state_year_ug[key]
            rows.append({
                "state": state,
                "year": year,
                "grad_total": g["total"],
                "grad_institutions": g["count"],
                "grad_avg_per_institution": round(g["total"] / g["count"], 1) if g["count"] else 0,
                "undergrad_total": u["total"],
                "undergrad_institutions": u["count"],
            })

    with open(summary_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved: {summary_path}")

    # ------------------------------------------------------------------
    # Compute state multipliers from real data
    # Use average grad enrollment per institution as demand signal.
    # Normalise to NY = 1.0 (largest market).
    # ------------------------------------------------------------------
    # Use the most recent 3 years for stability
    recent_years = [2022, 2023, 2024]
    state_grad_avg = {}
    for state in all_states:
        totals = []
        for year in recent_years:
            key = (state, year)
            g = state_year_grad[key]
            if g["count"]:
                totals.append(g["total"] / g["count"])
        state_grad_avg[state] = sum(totals) / len(totals) if totals else 1.0

    # Normalise to CT = 1.0 (our reference market)
    ct_avg = state_grad_avg.get("CT", 1.0) or 1.0
    state_multipliers = {s: round(v / ct_avg, 3) for s, v in state_grad_avg.items()}

    # ------------------------------------------------------------------
    # Compute growth trend using CONSISTENT reporters only
    # Problem: institution count alternates year-to-year (different schools
    # report in different years), making naive avg-per-institution unreliable.
    # Fix: only include institutions that reported in ALL of the recent years.
    # ------------------------------------------------------------------

    # Build per-institution yearly grad enrollment
    inst_yearly = {}   # unitid -> {year -> enrollment}
    for rec in long_records:
        if rec["level"] != "Graduate":
            continue
        uid = rec["unitid"]
        yr = int(rec["year"])
        if uid not in inst_yearly:
            inst_yearly[uid] = {}
        inst_yearly[uid][yr] = inst_yearly[uid].get(yr, 0) + rec["enrollment"]

    # Keep only institutions with grad data in ALL three recent years
    consistent_insts = {
        uid: ydata for uid, ydata in inst_yearly.items()
        if all(yr in ydata for yr in recent_years)
    }

    # Rebuild state-level averages from consistent institutions
    state_consistent_avg = defaultdict(lambda: {yr: [] for yr in recent_years})
    for uid, ydata in consistent_insts.items():
        # Find the state for this institution
        state = next((r["state"] for r in long_records if r["unitid"] == uid), None)
        if state not in all_states:
            continue
        for yr in recent_years:
            state_consistent_avg[state][yr].append(ydata[yr])

    state_growth = {}
    for state in all_states:
        yearly_avgs = []
        for yr in sorted(recent_years):
            vals = state_consistent_avg[state][yr]
            if vals:
                yearly_avgs.append(sum(vals) / len(vals))
        if len(yearly_avgs) >= 2:
            rates = [(yearly_avgs[i] - yearly_avgs[i-1]) / yearly_avgs[i-1]
                     for i in range(1, len(yearly_avgs))]
            state_growth[state] = round(sum(rates) / len(rates), 4)
        else:
            state_growth[state] = 0.0

    consistent_count = {s: len([u for u, d in consistent_insts.items()
                                 if any(r["state"] == s for r in long_records if r["unitid"] == u)])
                        for s in all_states}

    # ------------------------------------------------------------------
    # Build baselines JSON
    # Estimated new-program enrollment = avg grad per institution * capture_rate
    # Capture rates calibrated so that CT baseline (reference market) lands
    # near the professor's success target: ~40 students Year 1 for MS AI International.
    # CT avg grad/institution = ~1950 -> 40/1950 ~ 2.05%
    # ------------------------------------------------------------------
    CAPTURE_RATES = {
        "MS in AI":            {"International": 0.0205, "Domestic": 0.0180},
        "BS in AI":            {"International": 0.0130, "Domestic": 0.0230},
        "AI in Cybersecurity": {"International": 0.0160, "Domestic": 0.0200},
    }

    ct_base = state_grad_avg.get("CT", 400)
    baselines = {}
    for student_type in ("International", "Domestic"):
        baselines[student_type] = {}
        for program, rates in CAPTURE_RATES.items():
            rate = rates[student_type]
            val = int(ct_base * rate)
            val = max(val, 10)  # floor at 10
            baselines[student_type][program] = val

    output = {
        "data_source": "IPEDS EF Survey 2014-2024 (real data, degree-granting institutions only)",
        "institutions_count": len(set(r["unitid"] for r in long_records)),
        "consistent_reporters_by_state": consistent_count,
        "states": all_states,
        "years_covered": [min(YEARS), max(YEARS)],
        "state_grad_avg_per_institution": {s: round(v, 1) for s, v in state_grad_avg.items()},
        "state_multipliers": state_multipliers,
        "state_growth_rates": state_growth,
        "baselines": baselines,
    }

    baseline_path = os.path.join(PROCESSED_DIR, "state_baselines.json")
    with open(baseline_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Saved: {baseline_path}")

    # ------------------------------------------------------------------
    # Summary report
    # ------------------------------------------------------------------
    print("\n=== PROCESSING COMPLETE ===")
    print(f"Degree-granting institutions: {output['institutions_count']}")
    print(f"Consistent reporters (all 3 recent years): {consistent_count}")
    print(f"\nState graduate enrollment avg per institution (2022-2024):")
    for s, v in state_grad_avg.items():
        print(f"  {s}: {v:.0f} students/institution  (multiplier: {state_multipliers[s]}x)")
    print(f"\nGrowth trends -- consistent reporters only (YoY avg 2022-2024):")
    for s, g in state_growth.items():
        print(f"  {s}: {g*100:+.1f}%/year")
    print(f"\nCalibrated baselines (new program, Year 1):")
    for st in ("International", "Domestic"):
        for prog, val in baselines[st].items():
            print(f"  {st} {prog}: {val}")

    return output


if __name__ == "__main__":
    process()
