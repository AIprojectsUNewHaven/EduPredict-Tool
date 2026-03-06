"""
EduPredict MVP - Ultra Professional Dashboard
Executive Decision Tool for College Deans with 3D Visualizations

Features:
- 3D interactive charts and visualizations
- Glass morphism design
- Animated transitions
- Professional executive styling
- Real-time scenario comparison
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
import json
import sys
import os
from datetime import datetime
from fpdf import FPDF

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.forecasting import ForecastInput, EnrollmentForecaster
from models.roi_calculator import ROIInput, ROICalculator
from models.job_market import JobMarketAnalyzer

# Page configuration
st.set_page_config(
    page_title="EduPredict Pro | AI Degree Planning",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ultra Professional CSS with 3D effects and animations
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Pink and white theme with better spacing */
    .stApp {
        background: linear-gradient(135deg, #fdf2f8 0%, #fce7f3 100%);
    }
    
    .main {
        background: #ffffff;
        border-radius: 24px;
        margin: 1.5rem;
        padding: 2.5rem;
        box-shadow: 0 10px 25px -5px rgba(236, 72, 153, 0.15), 0 8px 10px -6px rgba(236, 72, 153, 0.1);
        border: 1px solid #fbcfe8;
    }
    
    /* Better spacing between sections */
    .stMarkdown {
        margin-bottom: 0.5rem !important;
    }
    
    /* Improve metric display */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #be185d !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        color: #9d174d !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Pink header */
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #ec4899 0%, #be185d 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }
    
    .sub-header {
        font-size: 1.25rem;
        color: #4a5568;
        font-weight: 400;
        margin-bottom: 2rem;
        letter-spacing: 0.5px;
    }
    
    /* Pink section headers */
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #831843;
        padding: 0.5rem 0;
        border-bottom: 2px solid #ec4899;
        margin-bottom: 1.5rem;
    }
    
    /* Pink metric cards - visible style */
    .glass-card {
        background: linear-gradient(135deg, #ffffff 0%, #fdf2f8 100%);
        border-radius: 16px;
        border: 2px solid #f472b6;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(236, 72, 153, 0.2);
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #ec4899 0%, #be185d 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.25rem;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: #be185d;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }
    
    /* Pink recommendation badges */
    .rec-strong-go {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 16px;
        text-align: center;
        font-size: 1.4rem;
        font-weight: 700;
        box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.3);
    }
    
    .rec-go {
        background: linear-gradient(135deg, #ec4899 0%, #be185d 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 16px;
        text-align: center;
        font-size: 1.4rem;
        font-weight: 700;
        box-shadow: 0 4px 6px -1px rgba(236, 72, 153, 0.3);
    }
    
    .rec-conditional {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 16px;
        text-align: center;
        font-size: 1.4rem;
        font-weight: 700;
        box-shadow: 0 4px 6px -1px rgba(245, 158, 11, 0.3);
    }
    
    .rec-reconsider {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 16px;
        text-align: center;
        font-size: 1.4rem;
        font-weight: 700;
        box-shadow: 0 4px 6px -1px rgba(239, 68, 68, 0.3);
    }
    
    /* Clean ROI Display */
    .roi-display {
        font-size: 2rem;
        font-weight: 700;
        color: #0f172a;
    }
    
    /* Pink insight box */
    .insight-box {
        background: linear-gradient(135deg, #fdf2f8 0%, #fce7f3 100%);
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid #fbcfe8;
        box-shadow: 0 2px 4px 0 rgba(236, 72, 153, 0.1);
    }
    
    /* Pink buttons */
    .stButton>button {
        background: linear-gradient(135deg, #ec4899 0%, #be185d 100%);
        color: white;
        font-weight: 600;
        font-size: 1rem;
        padding: 0.75rem 1.5rem;
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 6px -1px rgba(236, 72, 153, 0.3);
        transition: all 0.2s ease;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #db2777 0%, #9d174d 100%);
        box-shadow: 0 6px 8px -1px rgba(236, 72, 153, 0.4);
        transform: translateY(-1px);
    }
    
    /* Modern Select Boxes */
    .stSelectbox>div>div {
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        background: rgba(255, 255, 255, 0.8);
        transition: all 0.3s ease;
    }
    
    .stSelectbox>div>div:hover {
        border-color: #667eea;
        box-shadow: 0 4px 6px -1px rgba(102, 126, 234, 0.2);
    }
    
    /* Pink state badges */
    .state-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 700;
        box-shadow: 0 2px 4px 0 rgba(236, 72, 153, 0.1);
        transition: all 0.2s ease;
    }
    
    .state-badge:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(236, 72, 153, 0.2);
    }
    
    .state-ct { 
        background: linear-gradient(135deg, #fce7f3 0%, #fbcfe8 100%);
        color: #831843;
        border: 1px solid #f9a8d4;
    }
    .state-ny { 
        background: linear-gradient(135deg, #fdf2f8 0%, #fce7f3 100%);
        color: #9d174d;
        border: 1px solid #f9a8d4;
    }
    .state-ma { 
        background: linear-gradient(135deg, #fdf2f8 0%, #fce7f3 100%);
        color: #be185d;
        border: 1px solid #f9a8d4;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #a0aec0;
        font-size: 0.875rem;
        padding: 2rem 0;
        margin-top: 2rem;
        border-top: 1px solid #e2e8f0;
    }
    
    /* Tables with glass effect */
    .stTable {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Divider with gradient */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, #764ba2, transparent);
        margin: 2rem 0;
    }
    
    
</style>
""", unsafe_allow_html=True)


def get_recommendation(roi_ratio, confidence_score, launch_rec="proceed"):
    """Generate recommendation based on ROI, confidence, and launch assessment."""
    # Honor the ROI calculator's recommendation first
    if launch_rec == "delay" or roi_ratio < 0.5:
        return "DO NOT LAUNCH", "rec-reconsider"
    elif roi_ratio >= 1.5 and confidence_score > 0.75:
        return "STRONG GO", "rec-strong-go"
    elif roi_ratio >= 1.0 and confidence_score >= 0.60:
        return "GO", "rec-go"
    elif roi_ratio >= 0.7 or confidence_score >= 0.50:
        return "CONDITIONAL", "rec-conditional"
    else:
        return "RECONSIDER", "rec-reconsider"


def create_3d_forecast_surface(program, student_type, state):
    """Create 3D surface chart for scenario analysis."""
    forecaster = EnrollmentForecaster()
    
    scenarios = ["Conservative", "Baseline", "Optimistic"]
    terms = ["FA26", "SP27", "FA28"]
    
    z_data = []
    for scenario in scenarios:
        row = []
        for term in terms:
            forecast_input = ForecastInput(
                program_type=program,
                student_type=student_type,
                start_term=term,
                scenario=scenario,
                state=state
            )
            forecast = forecaster.forecast(forecast_input)
            row.append(forecast.year1_enrollment)
        z_data.append(row)
    
    fig = go.Figure(data=[go.Surface(
        z=z_data,
        x=terms,
        y=scenarios,
        colorscale='Viridis',
        showscale=True,
        colorbar=dict(title="Enrollment", titleside="right")
    )])
    
    fig.update_layout(
        title=dict(
            text=f"<b>3D Scenario Analysis</b><br><sub>{program} - {state}</sub>",
            font=dict(size=16)
        ),
        scene=dict(
            xaxis_title="Academic Term",
            yaxis_title="Scenario",
            zaxis_title="Year 1 Enrollment",
            camera=dict(eye=dict(x=1.5, y=1.5, z=1)),
            aspectratio=dict(x=1, y=1, z=0.7)
        ),
        height=500,
        margin=dict(l=0, r=0, b=0, t=50)
    )
    
    return fig


def create_3d_state_comparison(program, student_type, scenario, term):
    """Create 3D scatter chart comparing states."""
    forecaster = EnrollmentForecaster()
    
    states = ["CT", "NY", "MA"]
    years = [1, 2, 3]
    colors = ['#ec4899', '#be185d', '#9d174d']  # Pink shades
    
    fig = go.Figure()
    
    for i, state in enumerate(states):
        forecast_input = ForecastInput(
            program_type=program,
            student_type=student_type,
            start_term=term,
            scenario=scenario,
            state=state
        )
        forecast = forecaster.forecast(forecast_input)
        enrollments = [forecast.year1_enrollment, forecast.year2_enrollment, forecast.year3_enrollment]
        
        fig.add_trace(go.Scatter3d(
            x=years,
            y=[i] * 3,
            z=enrollments,
            mode='lines+markers',
            name=state,
            line=dict(color=colors[i], width=8),
            marker=dict(
                size=12,
                color=colors[i],
                symbol='circle'
            ),
            hovertemplate=f'<b>{state}</b><br>Year: %{{x}}<br>Enrollment: %{{z}}<extra></extra>'
        ))
    
    fig.update_layout(
        title=dict(
            text=f"<b>3D State Comparison</b><br><sub>{program} - {scenario}</sub>",
            font=dict(size=16, color='#831843')
        ),
        scene=dict(
            xaxis=dict(
                title="Academic Year",
                ticktext=["Year 1", "Year 2", "Year 3"],
                tickvals=[1, 2, 3],
                titlefont=dict(color='#9d174d'),
                tickfont=dict(color='#831843')
            ),
            yaxis=dict(
                title="State",
                ticktext=states,
                tickvals=[0, 1, 2],
                titlefont=dict(color='#9d174d'),
                tickfont=dict(color='#831843')
            ),
            zaxis=dict(
                title="Enrollment",
                titlefont=dict(color='#9d174d'),
                tickfont=dict(color='#831843')
            ),
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2)),
            bgcolor='#ffffff'
        ),
        height=500,
        paper_bgcolor='#ffffff',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            font=dict(color='#831843')
        ),
        margin=dict(l=0, r=0, b=0, t=50)
    )
    
    return fig


def create_animated_enrollment_chart(years, enrollment, scenario, program_type):
    """Create animated enrollment forecast chart."""
    fig = go.Figure()
    
    # Main line - pink theme with animation
    fig.add_trace(go.Scatter(
        x=years,
        y=enrollment,
        mode='lines+markers+text',
        name='Projected Enrollment',
        line=dict(
            color='#ec4899',
            width=4,
            shape='spline',
            smoothing=0.3
        ),
        marker=dict(
            size=16,
            color='#ec4899',
            line=dict(color='white', width=3)
        ),
        text=[f'<b>{e}</b>' for e in enrollment],
        textposition="top center",
        textfont=dict(size=14, color='#831843'),
        fill='tozeroy',
        fillcolor='rgba(236, 72, 153, 0.15)'
    ))
    
    # Scenario bands - pink theme
    if scenario == "Baseline":
        optimistic = [int(e * 1.25) for e in enrollment]
        conservative = [int(e * 0.75) for e in enrollment]
        
        fig.add_trace(go.Scatter(
            x=years + years[::-1],
            y=optimistic + enrollment[::-1],
            fill='toself',
            fillcolor='rgba(244, 114, 182, 0.2)',
            line=dict(color='rgba(0,0,0,0)'),
            name='Optimistic',
            showlegend=True
        ))
        
        fig.add_trace(go.Scatter(
            x=years + years[::-1],
            y=enrollment + conservative[::-1],
            fill='toself',
            fillcolor='rgba(251, 207, 232, 0.3)',
            line=dict(color='rgba(0,0,0,0)'),
            name='Conservative',
            showlegend=True
        ))
    
    fig.update_layout(
        title=dict(
            text=f"<b>{program_type}</b> - {scenario} Scenario",
            font=dict(size=18, color='#831843'),
            x=0.5
        ),
        xaxis=dict(
            title="Academic Year",
            titlefont=dict(size=13, color='#9d174d'),
            tickfont=dict(size=12, color='#831843'),
            gridcolor='#fce7f3',
            showline=True,
            linecolor='#fbcfe8'
        ),
        yaxis=dict(
            title="Projected Enrollment (Students)",
            titlefont=dict(size=13, color='#9d174d'),
            tickfont=dict(size=12, color='#831843'),
            gridcolor='#fce7f3',
            showline=True,
            linecolor='#fbcfe8'
        ),
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        height=450,
        showlegend=False,
        margin=dict(t=70, b=50, l=60, r=40),
        # Add smooth animation
        transition=dict(duration=1000, easing='cubic-in-out')
    )
    
    return fig


def create_3d_roi_visualization(roi_ratio):
    """Create 3D-style ROI indicator."""
    theta = np.linspace(0, 2*np.pi, 100)
    r = np.ones(100)
    
    fig = go.Figure()
    
    # Background ring
    fig.add_trace(go.Scatterpolar(
        r=r,
        theta=theta * 180/np.pi,
        mode='lines',
        line=dict(color='#e2e8f0', width=20),
        fill='toself',
        fillcolor='rgba(226, 232, 240, 0.3)',
        showlegend=False
    ))
    
    # ROI arc
    roi_angle = min(roi_ratio / 5, 1) * 360
    roi_theta = np.linspace(0, roi_angle, 100)
    
    # Color based on ROI
    if roi_ratio >= 1.5:
        color = '#48bb78'
    elif roi_ratio >= 1.0:
        color = '#4299e1'
    elif roi_ratio >= 0.7:
        color = '#ed8936'
    else:
        color = '#f56565'
    
    fig.add_trace(go.Scatterpolar(
        r=np.ones(100),
        theta=roi_theta,
        mode='lines',
        line=dict(color=color, width=20),
        showlegend=False
    ))
    
    # Center text
    fig.add_trace(go.Scatterpolar(
        r=[0],
        theta=[0],
        mode='text',
        text=[f'<b>{roi_ratio:.2f}x</b>'],
        textfont=dict(size=36, color='#2d3748', family='Inter'),
        showlegend=False
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=False, range=[0, 1.2]),
            angularaxis=dict(visible=False),
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        height=350,
        margin=dict(t=20, b=20, l=20, r=20),
        showlegend=False
    )
    
    return fig


def generate_pdf_report(program_type, student_type, term_code, scenario, state_code, 
                       forecast, roi, job_signal, demand_score, rec_text):
    """Generate a professional PDF report."""
    
    class EduPredictPDF(FPDF):
        def header(self):
            # Logo/Title
            self.set_font('Arial', 'B', 24)
            self.set_text_color(236, 72, 153)  # Pink color
            self.cell(0, 20, '🎓 EduPredict Pro', 0, 1, 'C')
            self.set_font('Arial', '', 12)
            self.set_text_color(100, 100, 100)
            self.cell(0, 10, 'AI Degree Program Planning & Analysis Report', 0, 1, 'C')
            self.line(10, 45, 200, 45)
            self.ln(10)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f'Page {self.page_no()} | Generated on {datetime.now().strftime("%B %d, %Y at %H:%M")}', 0, 0, 'C')
    
    pdf = EduPredictPDF()
    pdf.add_page()
    
    # Executive Summary Box
    pdf.set_fill_color(253, 242, 248)  # Light pink background
    pdf.set_draw_color(236, 72, 153)  # Pink border
    pdf.set_line_width(0.5)
    pdf.rect(10, 55, 190, 50, 'DF')
    
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(131, 24, 67)  # Dark pink
    pdf.cell(0, 15, 'EXECUTIVE SUMMARY', 0, 1, 'C')
    
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f'Program: {program_type}', 0, 1, 'C')
    pdf.cell(0, 8, f'Target: {student_type} Students | Launch: {term_code} | Location: {state_code}', 0, 1, 'C')
    pdf.cell(0, 8, f'Scenario: {scenario}', 0, 1, 'C')
    
    pdf.ln(15)
    
    # Key Metrics Section
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(236, 72, 153)
    pdf.cell(0, 12, '📊 KEY METRICS', 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Metrics in a grid
    pdf.set_font('Arial', 'B', 11)
    pdf.set_fill_color(255, 255, 255)
    
    metrics = [
        ("Year 1 Enrollment", f"{forecast.year1_enrollment} students"),
        ("3-Year Pool", f"{forecast.projected_pool} students"),
        ("Confidence Score", f"{int(forecast.confidence_score * 100)}%"),
        ("Annual Growth", f"+{int(forecast.growth_rate * 100)}%")
    ]
    
    col_width = 45
    for i, (label, value) in enumerate(metrics):
        if i % 2 == 0 and i > 0:
            pdf.ln(20)
        
        x = 15 + (i % 2) * 95
        y = pdf.get_y()
        
        # Draw box
        pdf.set_draw_color(236, 72, 153)
        pdf.set_line_width(0.3)
        pdf.rect(x, y, 90, 18, 'D')
        
        # Label
        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(100, 100, 100)
        pdf.set_xy(x + 5, y + 3)
        pdf.cell(80, 6, label, 0, 0, 'L')
        
        # Value
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(236, 72, 153)
        pdf.set_xy(x + 5, y + 9)
        pdf.cell(80, 8, value, 0, 0, 'L')
    
    pdf.ln(25)
    
    # ROI Analysis Section
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(236, 72, 153)
    pdf.cell(0, 12, '💰 FINANCIAL ANALYSIS', 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(0, 0, 0)
    
    financial_data = [
        ["Starting Salary", f"${roi.starting_salary:,}"],
        ["5-Year Salary", f"${roi.salary_5year:,}"],
        ["3-Year Tuition Revenue", f"${roi.total_tuition_revenue:,}"],
        ["Program Costs", f"${roi.program_cost_estimate:,}"],
        ["Net Return", f"${roi.total_tuition_revenue - roi.program_cost_estimate:,}"],
        ["ROI Ratio", f"{roi.roi_ratio:.2f}x"],
        ["Payback Period", f"{roi.payback_period_years} years"],
        ["Break-Even Point", f"{roi.break_even_enrollment} students"]
    ]
    
    # Table
    pdf.set_fill_color(253, 242, 248)
    pdf.set_draw_color(236, 72, 153)
    pdf.set_font('Arial', 'B', 10)
    
    for metric, value in financial_data:
        pdf.cell(70, 10, metric, 1, 0, 'L', True)
        pdf.set_font('Arial', '', 10)
        pdf.cell(120, 10, value, 1, 1, 'R')
        pdf.set_font('Arial', 'B', 10)
    
    pdf.ln(10)
    
    # Workforce Outlook Section
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(236, 72, 153)
    pdf.cell(0, 12, '💼 WORKFORCE OUTLOOK', 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f'• Job Growth (5-year): {job_signal.job_growth_rate}%', 0, 1, 'L')
    pdf.cell(0, 8, f'• Demand Level: {job_signal.demand_level}', 0, 1, 'L')
    pdf.cell(0, 8, f'• Demand Score: {demand_score}/100', 0, 1, 'L')
    pdf.cell(0, 8, f'• Open Positions: ~{job_signal.open_positions_estimate:,}', 0, 1, 'L')
    
    pdf.ln(10)
    
    # Recommendation Section (New Page if needed)
    if pdf.get_y() > 230:
        pdf.add_page()
    
    pdf.set_fill_color(253, 242, 248)
    pdf.set_draw_color(236, 72, 153)
    pdf.set_line_width(1)
    pdf.rect(10, pdf.get_y(), 190, 40, 'DF')
    
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(131, 24, 67)
    pdf.cell(0, 15, '✅ RECOMMENDATION', 0, 1, 'C')
    
    # Color based on recommendation
    if 'STRONG GO' in rec_text:
        pdf.set_text_color(16, 185, 129)  # Green
    elif 'GO' in rec_text:
        pdf.set_text_color(59, 130, 246)  # Blue
    elif 'CONDITIONAL' in rec_text:
        pdf.set_text_color(245, 158, 11)  # Orange
    else:
        pdf.set_text_color(239, 68, 68)  # Red
    
    pdf.set_font('Arial', 'B', 24)
    pdf.cell(0, 15, rec_text, 0, 1, 'C')
    
    pdf.ln(15)
    
    # Data Sources
    pdf.set_font('Arial', 'I', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, 'Data Sources: BLS Occupational Employment Statistics 2023 | IPEDS Institutional Data 2023-2024 | Industry Job Market Reports', 0, 1, 'C')
    pdf.cell(0, 8, 'This report is for educational and planning purposes. Enrollment projections are estimates based on historical data and market analysis.', 0, 1, 'C')
    
    # Return PDF as bytes
    return pdf.output(dest='S').encode('latin-1')


def main():
    """Main dashboard application with 3D visualizations."""
    
    # Header with enhanced styling
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<p class="main-header">🎓 EduPredict Pro</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Advanced AI Degree Program Planning & Decision Intelligence</p>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div style='text-align: right; color: #be185d; font-size: 0.9rem; font-weight: 600; margin-top: 1rem;'>v2.0 Pro</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: right; margin-top: 0.5rem;'><span class='state-badge state-ct'>CT</span> <span class='state-badge state-ny'>NY</span> <span class='state-badge state-ma'>MA</span></div>", unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Create three columns for layout
    left_col, center_col, right_col = st.columns([1, 2.2, 1])
    
    # LEFT PANEL - User Controls
    with left_col:
        st.markdown('<p class="section-header">📋 Input Parameters</p>', unsafe_allow_html=True)
        
        # Program Type
        program_type = st.selectbox(
            "🎓 Program Type",
            ["MS in AI", "BS in AI", "AI in Cybersecurity"],
            help="Select the AI degree program to evaluate"
        )
        
        # Student Type
        student_type = st.selectbox(
            "👥 Student Type",
            ["International", "Domestic"],
            help="Target student population"
        )
        
        # Academic Start Term
        start_term = st.selectbox(
            "📅 Academic Start Term",
            ["FA26 (Fall 2026)", "SP27 (Spring 2027)", "FA28 (Fall 2028)"],
            help="When will the program launch?"
        )
        term_code = start_term.split()[0]
        
        # Scenario
        scenario = st.selectbox(
            "📊 Forecast Scenario",
            ["Baseline", "Optimistic", "Conservative"],
            help="Select planning scenario"
        )
        
        # State
        state = st.selectbox(
            "🗺️ Target State",
            ["CT (Connecticut)", "NY (New York)", "MA (Massachusetts)"],
            help="Target state for program launch"
        )
        state_code = state.split()[0]
        
        # Generate button
        generate_clicked = st.button("🚀 Generate Forecast", use_container_width=True)
        
        # Info section
        with st.expander("ℹ️ About This Tool"):
            st.markdown("""
            **EduPredict Pro** helps College Deans make data-driven decisions about launching AI degree programs.
            
            **Key Features:**
            - 🎯 3-year enrollment forecasting
            - 📊 3D scenario analysis
            - 💼 State-level workforce analysis
            - 💰 ROI calculations with 3D visualization
            - ✅ Go/No-Go recommendations
            
            **Data Sources:**
            - BLS Occupational Employment Statistics
            - IPEDS Institutional Data
            - Industry Job Market Reports
            
            **Coverage:** CT, NY, MA (MVP Scope)
            """)
    
    # CENTER + RIGHT PANELS - Output
    if generate_clicked:
        # Initialize models
        forecaster = EnrollmentForecaster()
        roi_calc = ROICalculator()
        job_analyzer = JobMarketAnalyzer()
        
        # Create inputs
        forecast_input = ForecastInput(
            program_type=program_type,
            student_type=student_type,
            start_term=term_code,
            scenario=scenario,
            state=state_code
        )
        
        # Run forecasts
        forecast = forecaster.forecast(forecast_input)
        
        # Run ROI calculation with confidence context
        roi_input = ROIInput(
            program_type=program_type,
            state=state_code,
            year1_enrollment=forecast.year1_enrollment,
            year2_enrollment=forecast.year2_enrollment,
            year3_enrollment=forecast.year3_enrollment
        )
        roi = roi_calc.calculate(roi_input, student_type, forecast.confidence_score)
        
        # Get job market signal
        job_signal = job_analyzer.get_signal(state_code)
        demand_score = job_analyzer.get_demand_score(state_code)
        
        # Get recommendation (respects ROI calculator's launch assessment)
        rec_text, rec_class = get_recommendation(roi.roi_ratio, forecast.confidence_score, roi.launch_recommendation)
        
        # CENTER PANEL - Main Output
        with center_col:
            # Main Forecast Chart
            st.markdown('<p class="section-header">📈 Enrollment Projection</p>', unsafe_allow_html=True)
            
            years = ["Year 1", "Year 2", "Year 3"]
            enrollment = [
                forecast.year1_enrollment,
                forecast.year2_enrollment,
                forecast.year3_enrollment
            ]
            
            fig = create_animated_enrollment_chart(years, enrollment, scenario, program_type)
            st.plotly_chart(fig, use_container_width=True)
            
            # Metrics - using st.metric for better visibility
            metric_cols = st.columns(4)
            
            with metric_cols[0]:
                st.metric(
                    label="YEAR 1 STUDENTS",
                    value=f"{forecast.year1_enrollment}",
                    delta=f"Range: {forecast.year1_low}-{forecast.year1_high}"
                )
            
            with metric_cols[1]:
                st.metric(
                    label="3-YEAR POOL",
                    value=f"{forecast.projected_pool}",
                    delta=None
                )
            
            with metric_cols[2]:
                confidence_color = "normal" if forecast.confidence_score >= 0.70 else "off" if forecast.confidence_score >= 0.50 else "inverse"
                st.metric(
                    label="CONFIDENCE",
                    value=f"{int(forecast.confidence_score * 100)}%",
                    delta=forecast.recommendation_confidence.upper(),
                    delta_color=confidence_color
                )
            
            with metric_cols[3]:
                growth_pct = int(forecast.growth_rate * 100)
                st.metric(
                    label="YoY GROWTH",
                    value=f"+{growth_pct}%",
                    delta=None
                )
            
            # WARNING FLAGS SECTION
            if forecast.warning_flags or roi.financial_warnings:
                st.markdown("---")
                
                # Forecast warnings
                if forecast.warning_flags:
                    risk_emoji = "🟢" if forecast.risk_level == "low" else "🟡" if forecast.risk_level == "medium" else "🔴"
                    with st.expander(f"{risk_emoji} Forecast Uncertainty ({len(forecast.warning_flags)} flags)", expanded=forecast.risk_level=="high"):
                        for flag in forecast.warning_flags:
                            if "HIGH RISK" in flag or "WEAK RECOMMENDATION" in flag:
                                st.error(f"⚠️ {flag}")
                            elif "Conservative" in flag or "Optimistic" in flag or "Spring" in flag:
                                st.info(f"ℹ️ {flag}")
                            else:
                                st.warning(f"⚡ {flag}")
                        
                        st.caption(f"**Risk Level:** {forecast.risk_level.upper()} | **Confidence:** {forecast.recommendation_confidence.upper()}")
                
                # Financial warnings
                if roi.financial_warnings:
                    with st.expander(f"💰 Financial Risks ({len(roi.financial_warnings)} flags)", expanded=roi.roi_risk_level=="high"):
                        for warning in roi.financial_warnings:
                            if "CRITICAL" in warning or "WARNING" in warning or "Do not launch" in warning:
                                st.error(f"🚨 {warning}")
                            elif "Caution" in warning:
                                st.warning(f"⚠️ {warning}")
                            else:
                                st.info(f"ℹ️ {warning}")
                        
                        st.caption(f"**Financial Risk:** {roi.roi_risk_level.upper()} | **Recommendation:** {roi.launch_recommendation.upper()}")
                        st.caption(f"**Reason:** {roi.recommendation_reason}")
            
            # EXECUTIVE SUMMARY CARD (Printable)
            st.markdown('<p class="section-header">📋 Executive Summary Card</p>', unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #fdf2f8 0%, #fce7f3 100%); padding: 1.5rem; border-radius: 16px; border: 2px solid #ec4899; box-shadow: 0 4px 6px -1px rgba(236, 72, 153, 0.2);'>
                <h3 style='margin-top: 0; color: #831843; text-align: center; font-size: 1.4rem;'>🎓 EduPredict Pro - Analysis Report</h3>
                <p style='text-align: center; color: #9d174d; font-size: 0.9rem; margin-bottom: 1.5rem;'>{datetime.now().strftime("%B %d, %Y")}</p>
                
                <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;'>
                    <div style='background: white; padding: 1rem; border-radius: 8px; text-align: center;'>
                        <p style='margin: 0; font-size: 0.85rem; color: #666;'>PROGRAM</p>
                        <p style='margin: 0; font-size: 1.1rem; font-weight: 600; color: #831843;'>{program_type}</p>
                    </div>
                    <div style='background: white; padding: 1rem; border-radius: 8px; text-align: center;'>
                        <p style='margin: 0; font-size: 0.85rem; color: #666;'>LOCATION</p>
                        <p style='margin: 0; font-size: 1.1rem; font-weight: 600; color: #831843;'>{state}</p>
                    </div>
                </div>
                
                <div style='display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.75rem; margin-bottom: 1.5rem;'>
                    <div style='background: white; padding: 0.75rem; border-radius: 8px; text-align: center;'>
                        <p style='margin: 0; font-size: 1.5rem; font-weight: 700; color: #ec4899;'>{forecast.year1_enrollment}</p>
                        <p style='margin: 0; font-size: 0.75rem; color: #666;'>Year 1 Students</p>
                    </div>
                    <div style='background: white; padding: 0.75rem; border-radius: 8px; text-align: center;'>
                        <p style='margin: 0; font-size: 1.5rem; font-weight: 700; color: #ec4899;'>{forecast.projected_pool}</p>
                        <p style='margin: 0; font-size: 0.75rem; color: #666;'>3-Year Pool</p>
                    </div>
                    <div style='background: white; padding: 0.75rem; border-radius: 8px; text-align: center;'>
                        <p style='margin: 0; font-size: 1.5rem; font-weight: 700; color: #ec4899;'>{roi.roi_ratio:.2f}x</p>
                        <p style='margin: 0; font-size: 0.75rem; color: #666;'>ROI Ratio</p>
                    </div>
                </div>
                
                <div style='background: {'#d1fae5' if 'STRONG GO' in rec_text else '#dbeafe' if 'GO' in rec_text else '#fed7aa' if 'CONDITIONAL' in rec_text else '#fecaca'}; padding: 1rem; border-radius: 12px; text-align: center; border: 2px solid {'#10b981' if 'STRONG GO' in rec_text else '#3b82f6' if 'GO' in rec_text else '#f97316' if 'CONDITIONAL' in rec_text else '#ef4444'};'>
                    <p style='margin: 0; font-size: 0.85rem; color: #666;'>RECOMMENDATION</p>
                    <p style='margin: 0; font-size: 1.6rem; font-weight: 700; color: {'#047857' if 'STRONG GO' in rec_text else '#1d4ed8' if 'GO' in rec_text else '#c2410c' if 'CONDITIONAL' in rec_text else '#b91c1c'};'>{rec_text}</p>
                </div>
                
                <p style='text-align: center; color: #9d174d; font-size: 0.8rem; margin-top: 1rem; margin-bottom: 0;'>
                    📊 Data: BLS 2023 | IPEDS 2023-24 | Industry Reports
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.caption("💡 This summary card is optimized for screenshots and printing")
            
            # 3D Analysis Tabs
            st.markdown('<p class="section-header">🔮 3D Analysis & Visualizations</p>', unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["🌊 3D Scenario Surface", "📊 3D State Comparison"])
            
            with tab1:
                fig_3d = create_3d_forecast_surface(program_type, student_type, state_code)
                st.plotly_chart(fig_3d, use_container_width=True)
                st.caption("Interactive 3D surface showing enrollment projections across all scenarios and terms. Drag to rotate!")
            
            with tab2:
                fig_3d_compare = create_3d_state_comparison(program_type, student_type, scenario, term_code)
                st.plotly_chart(fig_3d_compare, use_container_width=True)
                st.caption("3D bar chart comparing enrollment projections across CT, NY, and MA.")
            
            # Financial Analysis with 3D ROI
            st.markdown('<p class="section-header">💰 Financial Analysis</p>', unsafe_allow_html=True)
            
            roi_cols = st.columns([1, 1.5])
            
            with roi_cols[0]:
                fig_roi = create_3d_roi_visualization(roi.roi_ratio)
                st.plotly_chart(fig_roi, use_container_width=True)
                st.markdown(f"<center><span style='font-size: 1.2rem; font-weight: 700; color: {'#48bb78' if roi.roi_ratio >= 1 else '#e53e3e'}'>ROI: {roi.roi_ratio:.2f}x</span></center>", unsafe_allow_html=True)
            
            with roi_cols[1]:
                fin_data = {
                    "Metric": [
                        "💵 Starting Salary",
                        "📈 5-Year Salary",
                        "💰 3-Year Revenue",
                        "💸 Program Costs",
                        "📊 Net Return",
                        "⏱️ Payback Period",
                        "🎯 Break-Even"
                    ],
                    "Value": [
                        f"${roi.starting_salary:,}",
                        f"${roi.salary_5year:,}",
                        f"${roi.total_tuition_revenue:,}",
                        f"${roi.program_cost_estimate:,}",
                        f"${roi.total_tuition_revenue - roi.program_cost_estimate:,}",
                        f"{roi.payback_period_years} years",
                        f"{roi.break_even_enrollment} students"
                    ]
                }
                
                st.table(fin_data)
        
        # RIGHT PANEL - Executive Summary
        with right_col:
            st.markdown('<p class="section-header">🎯 Executive Summary</p>', unsafe_allow_html=True)
            
            # Recommendation box with enhanced messaging
            if rec_text == "DO NOT LAUNCH":
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); 
                           color: white; padding: 1.5rem; border-radius: 16px; 
                           text-align: center; font-size: 1.4rem; font-weight: 700;
                           box-shadow: 0 4px 6px -1px rgba(239, 68, 68, 0.3);
                           border: 3px solid #b91c1c;'>
                    🚫 {rec_text}
                </div>
                <div style='background: #fef2f2; border: 2px solid #fecaca; border-radius: 8px; 
                           padding: 1rem; margin-top: 0.5rem; color: #991b1b; font-size: 0.9rem;'>
                    <b>Why:</b> {roi.recommendation_reason}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="{rec_class}">{rec_text}</div>', unsafe_allow_html=True)
            
            # Key metrics in insight box
            st.markdown('<div class="insight-box">', unsafe_allow_html=True)
            
            st.markdown("**📊 Program Overview**")
            st.markdown(f"• **Program:** {program_type}")
            st.markdown(f"• **Target:** {student_type}")
            st.markdown(f"• **Launch:** {start_term}")
            st.markdown(f"• **Location:** {state}")
            st.markdown(f"• **Scenario:** {scenario}")
            
            st.markdown("")
            
            # Workforce signal
            st.markdown("**💼 Workforce Outlook**")
            st.markdown(f"• Job Growth: **{job_signal.job_growth_rate}%** (5yr)")
            st.markdown(f"• Demand: **{job_signal.demand_level}**")
            st.markdown(f"• Score: **{demand_score}/100**")
            st.markdown(f"• Openings: **~{job_signal.open_positions_estimate:,}**")
            
            st.markdown("")
            
            # ROI summary
            st.markdown("**💰 ROI Summary**")
            roi_color = "#48bb78" if roi.roi_ratio >= 1.0 else "#e53e3e"
            st.markdown(f"• ROI Ratio: <span style='color: {roi_color}; font-weight: 800; font-size: 1.3rem;'>{roi.roi_ratio:.2f}x</span>", unsafe_allow_html=True)
            st.markdown(f"• Salary: **${roi.starting_salary:,}**")
            st.markdown(f"• Revenue: **${roi.total_tuition_revenue:,}**")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Scenario comparison
            st.markdown('<p class="section-header">🔍 All Scenarios</p>', unsafe_allow_html=True)
            
            scenarios = ["Conservative", "Baseline", "Optimistic"]
            scenario_data = []
            
            for scen in scenarios:
                temp_input = ForecastInput(
                    program_type=program_type,
                    student_type=student_type,
                    start_term=term_code,
                    scenario=scen,
                    state=state_code
                )
                temp_forecast = forecaster.forecast(temp_input)
                scenario_data.append({
                    "Scenario": scen,
                    "Y1": temp_forecast.year1_enrollment,
                    "Pool": temp_forecast.projected_pool
                })
            
            st.table(scenario_data)
            
            # AI Insight - Honest about uncertainty
            if roi.launch_recommendation == "delay":
                st.error(f"""
                **🚨 AI Insight - DO NOT LAUNCH**
                
                This configuration shows **poor viability**:
                - ROI of {roi.roi_ratio:.2f}x is below sustainable threshold
                - Forecast confidence is {int(forecast.confidence_score * 100)}%
                - {roi.recommendation_reason}
                
                **Recommendation:** Gather more data or consider alternative program configurations.
                """)
            elif forecast.confidence_score < 0.60:
                st.warning(f"""
                **⚠️ AI Insight - UNCERTAIN PREDICTION**
                
                With **{forecast.year1_enrollment}** students projected (range: {forecast.year1_low}-{forecast.year1_high}) and **{roi.roi_ratio:.2f}x ROI**, this program shows {'potential' if roi.roi_ratio >= 1.0 else 'risk'}.
                
                **However:** Confidence is only {int(forecast.confidence_score * 100)}%. {forecast.recommendation_confidence.capitalize()} recommendation strength.
                
                Consider validating with pilot data before committing resources.
                """)
            else:
                st.success(f"""
                **💡 AI Insight**
                
                With **{forecast.year1_enrollment}** students Year 1 and **{roi.roi_ratio:.2f}x ROI**, this program shows {'exceptional' if roi.roi_ratio >= 1.5 else 'strong' if roi.roi_ratio >= 1.0 else 'moderate'} viability in {state_code}.
                
                Forecast confidence: {int(forecast.confidence_score * 100)}% ({forecast.recommendation_confidence} recommendation)
                
                The {job_signal.demand_level} demand for AI talent supports program launch.
                """)
            
            # DOWNLOAD SECTION - PDF REPORT
            st.markdown('<p class="section-header">📥 Download Professional Report</p>', unsafe_allow_html=True)
            
            st.info("💡 Generate a professional PDF report suitable for presentations, printing, or sharing with stakeholders.")
            
            # Generate PDF
            pdf_bytes = generate_pdf_report(
                program_type, student_type, term_code, scenario, state_code,
                forecast, roi, job_signal, demand_score, rec_text
            )
            
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_bytes,
                file_name=f"EduPredict_Report_{state_code}_{term_code}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
            st.caption("✅ The PDF includes: Executive Summary, Key Metrics, Financial Analysis, Workforce Outlook, and Recommendation")
    
    else:
        # Default state - show welcome screen
        with center_col:
            # Welcome message
            st.warning("👈 **Click 'Generate Forecast'** to see 3D visualizations!")
            
            # Feature cards
            st.markdown('<p class="section-header">✨ Features</p>', unsafe_allow_html=True)
            
            st.info("🌊 **3D Scenario Analysis** - Surface plots for all scenarios")
            st.info("📊 **3D State Comparison** - Compare CT, NY, MA projections")  
            st.info("💼 **Workforce Intelligence** - AI job market data")
            st.info("💰 **ROI Analysis** - Circular ROI visualization")
            
            # Success criteria
            st.markdown('<p class="section-header">✓ Validated</p>', unsafe_allow_html=True)
            cov_col1, cov_col2 = st.columns(2)
            
            with cov_col1:
                st.success("📚 **Programs**\n\n• MS in AI\n• BS in AI\n• AI in Cybersecurity")
            
            with cov_col2:
                st.success("🗓️ **Terms**\n\n• Fall 2026 (FA26)\n• Spring 2027 (SP27)\n• Fall 2028 (FA28)")
        
        with right_col:
            st.markdown('<p class="section-header">📈 Data Sources</p>', unsafe_allow_html=True)
            
            st.write("🏛️ **BLS** - Occupational Employment")
            st.write("🎓 **IPEDS** - Enrollment Data")
            st.write("💼 **Industry** - Job Reports")
            st.write("💵 **Salary** - Benchmarks")
    
    # Footer
    st.markdown("""
    <div class="footer">
        <b>EduPredict Pro</b> | Advanced AI Degree Planning Platform<br>
        Powered by Streamlit, Plotly 3D & Python | Data: BLS 2023, IPEDS 2023-2024<br>
        <span style="font-size: 0.75rem;">Professional Edition | For Higher Education Leadership</span>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
