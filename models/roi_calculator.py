"""
EduPredict MVP - ROI Calculator
Computes tuition revenue, salary projections, and ROI ratios.

Loads salary data from BLS CSV (data/raw/bls_salary_data.csv)
Falls back to hardcoded values if CSV not found.
"""

import csv
import os
from pathlib import Path
from typing import Dict, Tuple
from dataclasses import dataclass


@dataclass
class ROIInput:
    """Input for ROI calculations."""
    program_type: str
    state: str
    year1_enrollment: int
    year2_enrollment: int
    year3_enrollment: int


@dataclass
class ROIOutput:
    """ROI calculation results."""
    starting_salary: int
    salary_5year: int
    total_tuition_revenue: int
    program_cost_estimate: int
    roi_ratio: float
    payback_period_years: float
    break_even_enrollment: int


class ROICalculator:
    """
    Calculates return on investment for AI degree programs.
    """
    
    # Annual tuition by program type (estimated)
    TUITION_RATES = {
        "MS in AI": {
            "International": 35000,
            "Domestic": 25000
        },
        "BS in AI": {
            "International": 32000,
            "Domestic": 18000
        },
        "AI in Cybersecurity": {
            "International": 34000,
            "Domestic": 24000
        }
    }
    
    # Program duration in years
    PROGRAM_DURATION = {
        "MS in AI": 2,
        "BS in AI": 4,
        "AI in Cybersecurity": 2  # Assuming MS level
    }
    
    # Fallback salaries (if CSV not found)
    FALLBACK_SALARIES = {
        "MS in AI": {
            "CT": 95000,
            "NY": 110000,
            "MA": 115000
        },
        "BS in AI": {
            "CT": 75000,
            "NY": 85000,
            "MA": 90000
        },
        "AI in Cybersecurity": {
            "CT": 98000,
            "NY": 112000,
            "MA": 118000
        }
    }
    
    # 5-year salary growth rate
    SALARY_GROWTH_RATE = 0.08  # 8% annual growth
    
    # Program operational costs
    OPERATIONAL_COST_PER_STUDENT = {
        "MS in AI": 12000,
        "BS in AI": 10000,
        "AI in Cybersecurity": 13000
    }
    
    # Fixed program startup costs
    STARTUP_COSTS = {
        "MS in AI": 500000,
        "BS in AI": 750000,
        "AI in Cybersecurity": 550000
    }
    
    def __init__(self, salary_data_path: str = None):
        """
        Initialize ROI calculator.
        
        Args:
            salary_data_path: Path to bls_salary_data.csv (optional)
        """
        self.salary_data_path = salary_data_path or self._find_salary_file()
        self.starting_salaries = self._load_salary_data()
    
    def _find_salary_file(self) -> str:
        """Find the BLS salary data file."""
        possible_paths = [
            "data/raw/bls_salary_data.csv",
            "../data/raw/bls_salary_data.csv",
            "../../data/raw/bls_salary_data.csv",
            "/Users/munagalatarakanagaganesh/Documents/Notes/01_Projects/EduPredict-MVP/data/raw/bls_salary_data.csv"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _load_salary_data(self) -> Dict:
        """
        Load salary data from BLS CSV.
        
        Maps BLS occupation codes to program types:
        - 15-1256 (Data Scientists) -> MS in AI
        - 15-1250 (Computer Occupations) -> BS in AI, AI in Cybersecurity
        """
        if not self.salary_data_path or not os.path.exists(self.salary_data_path):
            print("ROI: Using fallback salary data (CSV not found)")
            return self.FALLBACK_SALARIES
        
        try:
            # Build salary lookup from CSV
            salary_lookup = {}  # {state: {occupation: salary}}
            
            with open(self.salary_data_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    state = row['state']
                    occupation = row['occupation_code']  # 15-1250 or 15-1256
                    median_salary = int(row['median_salary'])
                    
                    if state not in salary_lookup:
                        salary_lookup[state] = {}
                    salary_lookup[state][occupation] = median_salary
            
            # Map to program types
            program_salaries = {
                "MS in AI": {},
                "BS in AI": {},
                "AI in Cybersecurity": {}
            }
            
            for state in ["CT", "NY", "MA"]:
                state_data = salary_lookup.get(state, {})
                
                # MS in AI uses Data Scientist salaries (15-1256)
                ds_salary = state_data.get('15-1256', self.FALLBACK_SALARIES["MS in AI"][state])
                # Adjust down slightly for new graduates vs experienced
                program_salaries["MS in AI"][state] = int(ds_salary * 0.85)
                
                # BS in AI uses general Computer Occupations (15-1250)
                cs_salary = state_data.get('15-1250', self.FALLBACK_SALARIES["BS in AI"][state])
                program_salaries["BS in AI"][state] = int(cs_salary * 0.75)  # Entry level
                
                # AI in Cybersecurity premium over general CS
                program_salaries["AI in Cybersecurity"][state] = int(cs_salary * 0.90)
            
            print(f"ROI: Loaded salary data from CSV for {len(salary_lookup)} states")
            return program_salaries
            
        except Exception as e:
            print(f"ROI: Error loading CSV: {e}")
            return self.FALLBACK_SALARIES
    
    def calculate(self, inputs: ROIInput, student_type: str = "International") -> ROIOutput:
        """
        Calculate ROI for a program.
        
        Args:
            inputs: ROIInput with enrollment projections
            student_type: International or Domestic (affects tuition)
            
        Returns:
            ROIOutput with all calculations
        """
        program = inputs.program_type
        state = inputs.state
        
        # Get starting salary (from CSV or fallback)
        starting_salary = self.starting_salaries[program][state]
        
        # Calculate 5-year salary (compound growth)
        salary_5year = int(starting_salary * (1 + self.SALARY_GROWTH_RATE) ** 5)
        
        # Calculate tuition revenue
        annual_tuition = self.TUITION_RATES[program][student_type]
        program_years = self.PROGRAM_DURATION[program]
        
        # Revenue from each cohort
        year1_revenue = inputs.year1_enrollment * annual_tuition * program_years
        year2_revenue = inputs.year2_enrollment * annual_tuition * program_years
        year3_revenue = inputs.year3_enrollment * annual_tuition * program_years
        
        total_tuition_revenue = year1_revenue + year2_revenue + year3_revenue
        
        # Calculate costs
        startup_cost = self.STARTUP_COSTS[program]
        total_students = inputs.year1_enrollment + inputs.year2_enrollment + inputs.year3_enrollment
        operational_cost = total_students * self.OPERATIONAL_COST_PER_STUDENT[program]
        
        program_cost_estimate = startup_cost + operational_cost
        
        # ROI calculation
        net_return = total_tuition_revenue - program_cost_estimate
        roi_ratio = round(net_return / program_cost_estimate, 2) if program_cost_estimate > 0 else 0
        
        # Payback period
        annual_avg_revenue = total_tuition_revenue / 3
        if annual_avg_revenue > 0:
            payback_period_years = startup_cost / annual_avg_revenue
        else:
            payback_period_years = float('inf')
        
        # Break-even enrollment
        break_even_enrollment = int(startup_cost / (annual_tuition * program_years))
        
        return ROIOutput(
            starting_salary=starting_salary,
            salary_5year=salary_5year,
            total_tuition_revenue=total_tuition_revenue,
            program_cost_estimate=program_cost_estimate,
            roi_ratio=roi_ratio,
            payback_period_years=round(payback_period_years, 1),
            break_even_enrollment=break_even_enrollment
        )
    
    def get_summary_metrics(self, roi_output: ROIOutput) -> Dict[str, str]:
        """Get formatted summary for display."""
        return {
            "Starting Salary": f"${roi_output.starting_salary:,}",
            "5-Year Salary": f"${roi_output.salary_5year:,}",
            "Tuition Revenue (3yr)": f"${roi_output.total_tuition_revenue:,}",
            "Program Costs": f"${roi_output.program_cost_estimate:,}",
            "ROI Ratio": f"{roi_output.roi_ratio}x",
            "Payback Period": f"{roi_output.payback_period_years} years",
            "Break-even Enrollment": f"{roi_output.break_even_enrollment} students"
        }


def quick_roi(
    program: str,
    state: str,
    year1: int,
    year2: int,
    year3: int,
    student_type: str = "International"
) -> ROIOutput:
    """
    Quick ROI calculation.
    
    Example:
        result = quick_roi("MS in AI", "CT", 50, 60, 72, "International")
    """
    calc = ROICalculator()
    inputs = ROIInput(
        program_type=program,
        state=state,
        year1_enrollment=year1,
        year2_enrollment=year2,
        year3_enrollment=year3
    )
    return calc.calculate(inputs, student_type)


if __name__ == "__main__":
    # Test the calculator
    calc = ROICalculator()
    
    for program in ["MS in AI", "BS in AI", "AI in Cybersecurity"]:
        for state in ["CT", "NY", "MA"]:
            result = quick_roi(program, state, 40, 50, 60, "International")
            print(f"\n{program} in {state}:")
            print(f"  Starting Salary: ${result.starting_salary:,}")
            print(f"  ROI Ratio: {result.roi_ratio}x")
