"""
EduPredict MVP - Configuration
Centralized constants and settings.
"""

from typing import Dict, List


# MVP Scope Configuration
MVP_STATES: List[str] = ["CT", "NY", "MA"]

PROGRAM_TYPES: List[str] = [
    "MS in AI",
    "BS in AI",
    "AI in Cybersecurity"
]

STUDENT_TYPES: List[str] = ["International", "Domestic"]

ACADEMIC_TERMS: Dict[str, str] = {
    "FA26": "Fall 2026",
    "SP27": "Spring 2027",
    "FA28": "Fall 2028"
}

SCENARIOS: List[str] = ["Baseline", "Optimistic", "Conservative"]

# State display names
STATE_NAMES: Dict[str, str] = {
    "CT": "Connecticut",
    "NY": "New York",
    "MA": "Massachusetts"
}

# Data source URLs (for reference)
DATA_SOURCES = {
    "IPEDS": "https://nces.ed.gov/ipeds/",
    "BLS": "https://www.bls.gov/",
    "Census": "https://www.census.gov/"
}

# Application settings
APP_TITLE = "EduPredict MVP"
APP_SUBTITLE = "Data-Driven Decision Tool for AI Degree Planning"

# Forecasting settings
DEFAULT_SCENARIO = "Baseline"
DEFAULT_STATE = "CT"
DEFAULT_PROGRAM = "MS in AI"
DEFAULT_STUDENT_TYPE = "International"
DEFAULT_TERM = "FA26"

# UI Settings
PAGE_TITLE = "EduPredict MVP"
PAGE_ICON = "🎓"
LAYOUT = "wide"

# File paths
DATA_RAW_PATH = "data/raw"
DATA_PROCESSED_PATH = "data/processed"
MODELS_PATH = "models"
UI_PATH = "ui"