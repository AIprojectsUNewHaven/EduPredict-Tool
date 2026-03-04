"""
EduPredict MVP - Job Market Signals
State-level workforce demand indicators.
"""

import csv
import os
from pathlib import Path
from typing import Dict
from dataclasses import dataclass


@dataclass
class JobMarketSignal:
    """Job market data for a state."""
    state: str
    job_growth_rate: float  # Annual growth %
    open_positions_estimate: int
    demand_level: str  # High, Medium, Low
    trend_direction: str  # Growing, Stable, Declining


class JobMarketAnalyzer:
    """
    Provides AI job market signals for states.
    
    Loads from CSV data (data/raw/job_market_data.csv)
    Falls back to hardcoded values if CSV not found.
    """
    
    # Fallback data (same as CSV)
    STATE_DATA = {
        "CT": {
            "job_growth_rate": 28.5,  # 5-year growth %
            "open_positions_base": 1200,
            "demand_level": "Medium-High",
            "trend_direction": "Growing",
            "top_employers": "United Technologies, Pratt & Whitney, Hartford Insurance"
        },
        "NY": {
            "job_growth_rate": 35.8,
            "open_positions_base": 8500,
            "demand_level": "Very High",
            "trend_direction": "Growing",
            "top_employers": "Google NYC, Meta, Bloomberg, JPMorgan Chase"
        },
        "MA": {
            "job_growth_rate": 42.3,
            "open_positions_base": 6200,
            "demand_level": "Very High",
            "trend_direction": "Growing",
            "top_employers": "MIT, Harvard, Google Cambridge, Amazon Boston, Biogen"
        }
    }
    
    def __init__(self, data_path: str = None):
        """
        Initialize job market analyzer.
        
        Args:
            data_path: Path to job_market_data.csv (optional)
        """
        self.data_path = data_path or self._find_data_file()
        self.state_data = self._load_data()
    
    def _find_data_file(self) -> str:
        """Find the job market data file."""
        # Try common locations
        possible_paths = [
            "data/raw/job_market_data.csv",
            "../data/raw/job_market_data.csv",
            "../../data/raw/job_market_data.csv",
            "/Users/munagalatarakanagaganesh/Documents/Notes/01_Projects/EduPredict-MVP/data/raw/job_market_data.csv"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _load_data(self) -> Dict:
        """Load data from CSV or use fallback."""
        if not self.data_path or not os.path.exists(self.data_path):
            print("Job market: Using fallback data (CSV not found)")
            return self.STATE_DATA
        
        try:
            data = {}
            with open(self.data_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    state = row['state']
                    data[state] = {
                        'job_growth_rate': float(row['ai_job_growth_5yr']),
                        'open_positions_base': int(row['open_positions_sample']),
                        'demand_level': row['demand_level'],
                        'trend_direction': 'Growing',  # All growing in current data
                        'top_employers': row.get('top_employers', '')
                    }
            print(f"Job market: Loaded data for {len(data)} states from CSV")
            return data
        except Exception as e:
            print(f"Job market: Error loading CSV: {e}")
            return self.STATE_DATA
    
    def get_signal(self, state: str) -> JobMarketSignal:
        """
        Get job market signal for a state.
        
        Args:
            state: CT, NY, or MA
            
        Returns:
            JobMarketSignal with workforce data
        """
        if state not in self.state_data:
            raise ValueError(f"State {state} not supported in MVP")
        
        data = self.state_data[state]
        
        return JobMarketSignal(
            state=state,
            job_growth_rate=data["job_growth_rate"],
            open_positions_estimate=data["open_positions_base"],
            demand_level=data["demand_level"],
            trend_direction=data["trend_direction"]
        )
    
    def get_demand_score(self, state: str) -> int:
        """
        Get numeric demand score (0-100).
        
        Args:
            state: State abbreviation
            
        Returns:
            Demand score 0-100
        """
        signal = self.get_signal(state)
        
        # Base score from level
        base_scores = {
            "Very High": 85,
            "High": 75,
            "Medium-High": 65,
            "Medium": 50,
            "Low": 25
        }
        base = base_scores.get(signal.demand_level, 50)
        
        # Adjust for growth rate
        growth_bonus = min(signal.job_growth_rate / 2, 15)  # Cap at 15
        
        return int(base + growth_bonus)
    
    def format_signal(self, signal: JobMarketSignal) -> Dict[str, str]:
        """Format signal for display."""
        return {
            "State": signal.state,
            "5-Year Growth": f"{signal.job_growth_rate}%",
            "Open Positions": f"~{signal.open_positions_estimate:,}",
            "Demand Level": signal.demand_level,
            "Trend": signal.trend_direction
        }
    
    def get_all_states(self) -> Dict[str, Dict]:
        """Get data for all states."""
        return self.state_data


def get_workforce_outlook(state: str) -> Dict[str, str]:
    """
    Quick workforce outlook for a state.
    
    Example:
        outlook = get_workforce_outlook("MA")
    """
    analyzer = JobMarketAnalyzer()
    signal = analyzer.get_signal(state)
    return analyzer.format_signal(signal)


if __name__ == "__main__":
    # Test the analyzer
    analyzer = JobMarketAnalyzer()
    
    for state in ["CT", "NY", "MA"]:
        signal = analyzer.get_signal(state)
        print(f"\n{state}:")
        for key, value in analyzer.format_signal(signal).items():
            print(f"  {key}: {value}")
        print(f"  Demand Score: {analyzer.get_demand_score(state)}")
