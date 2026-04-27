"""
EduPredict Pro - Flask Application
AI Degree Program Planning & Decision Intelligence Tool

No Streamlit. Pure Flask + HTML/CSS/JS.
Hosted on AWS EC2 with Gunicorn.
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import sys
import re
import csv
from io import BytesIO
from datetime import datetime

try:
    import anthropic as _anthropic
    ANTHROPIC_AVAILABLE = bool(os.environ.get("ANTHROPIC_API_KEY"))
except ImportError:
    _anthropic = None
    ANTHROPIC_AVAILABLE = False

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def validate_email(email):
    """Validate email format."""
    if not email:
        return False
    return EMAIL_REGEX.match(email.strip()) is not None

# Add models to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.forecasting import ForecastInput, EnrollmentForecaster, quick_forecast
from models.roi_calculator import ROIInput, ROICalculator, quick_roi
from models.job_market import JobMarketAnalyzer, quick_ai_report, AIOccupationDatabase

# PDF generation
try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False
    print("Warning: FPDF not available. PDF export disabled.")

app = Flask(__name__)

_secret_key = os.environ.get('SECRET_KEY')
if not _secret_key:
    import secrets as _secrets
    _secret_key = _secrets.token_hex(32)
    print("WARNING: SECRET_KEY not set. Sessions will not persist across restarts. Set SECRET_KEY env var for production.")
app.config['SECRET_KEY'] = _secret_key

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///edupredict.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access the dashboard.'
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "60 per hour"],
    storage_uri="memory://",
)

# Database Models
class User(UserMixin, db.Model):
    """User model for authentication with email."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=True)  # Kept for backwards compatibility
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        """Override to return email as identifier for Flask-Login."""
        return str(self.id)

class ForecastHistory(db.Model):
    """Store forecast history for audit trail."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    program = db.Column(db.String(50), nullable=False)
    student_type = db.Column(db.String(20), nullable=False)
    term = db.Column(db.String(10), nullable=False)
    scenario = db.Column(db.String(20), nullable=False)
    state = db.Column(db.String(5), nullable=False)
    year1_enrollment = db.Column(db.Integer)
    projected_pool = db.Column(db.Integer)
    roi_ratio = db.Column(db.Float)
    confidence = db.Column(db.Float)
    recommendation = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='forecasts')

class ActivityLog(db.Model):
    """General activity logging."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.String(255))
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='activities')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize models
forecaster = EnrollmentForecaster()
roi_calc = ROICalculator()
job_analyzer = JobMarketAnalyzer()
ai_db = AIOccupationDatabase()

# Configuration
PROGRAMS = ["MS in AI", "BS in AI", "AI in Cybersecurity"]
STUDENT_TYPES = ["International", "Domestic"]
TERMS = ["SP26", "SU26", "FA26", "SP27", "SU27", "FA27", "SP28", "SU28", "FA28"]
SCENARIOS = ["Baseline", "Optimistic", "Conservative"]
STATES = ["CT", "NY", "MA"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
# Geo map CSVs (employers_2024.csv, institutions_programs_2024.csv) live under data/raw when provided
GEO_DATA_DIR = os.environ.get("EDUPREDICT_GEO_DATA_DIR") or DATA_RAW_DIR

# Curated official sources (APIs and downloads -- not scraped third-party sites)
OFFICIAL_DATA_STACK = [
    {
        "id": "bls-oes",
        "name": "BLS Occupational Employment & Wage Statistics",
        "publisher": "U.S. Bureau of Labor Statistics",
        "used_for": "State-level wages and tech occupation structure (CT, NY, MA).",
        "portal_url": "https://www.bls.gov/oes/",
        "api_url": "https://www.bls.gov/developers/",
    },
    {
        "id": "bls-ep",
        "name": "BLS Employment Projections",
        "publisher": "U.S. Bureau of Labor Statistics",
        "used_for": "Long-run demand and growth context for modeled scenarios.",
        "portal_url": "https://www.bls.gov/emp/",
        "api_url": None,
    },
    {
        "id": "ipeds",
        "name": "IPEDS Data Center",
        "publisher": "NCES / U.S. Department of Education",
        "used_for": "Institution universe, program signals, and (when loaded) completions by CIP.",
        "portal_url": "https://nces.ed.gov/ipeds/",
        "api_url": None,
    },
    {
        "id": "anthropic-econ",
        "name": "Anthropic Economic Index & research",
        "publisher": "Anthropic",
        "used_for": "Observed AI exposure, coverage gap, and hiring-risk framing in the model narrative.",
        "portal_url": "https://www.anthropic.com/research",
        "api_url": None,
    },
]

# Product-grade upgrade path (shown in UI; aligns with professor / enterprise expectations)
DATA_IMPROVEMENT_ROADMAP = [
    {
        "priority": "P0",
        "title": "IPEDS Completions by CIP (11.xx / 14.xx)",
        "detail": "Load official completions for AI/CS-related CIPs for CT, NY, MA to replace enrollment proxies.",
        "effort": "Medium",
    },
    {
        "priority": "P0",
        "title": "Automated BLS refresh",
        "detail": "Schedule pulls via the public BLS API for OES series you depend on, with versioned CSV snapshots.",
        "effort": "Low",
    },
    {
        "priority": "P1",
        "title": "Peer institution benchmark pack",
        "detail": "Curated comparator set (tuition, launch year, outcomes) with manual QA from catalogs, not scraped paywalls.",
        "effort": "Medium",
    },
    {
        "priority": "P1",
        "title": "Employer map data governance",
        "detail": "Document hire estimates, source per row, and refresh cadence; treat as directional not ground truth.",
        "effort": "Low",
    },
    {
        "priority": "P2",
        "title": "Audit log & reproducible runs",
        "detail": "Bind each forecast to data snapshot IDs (file hash + date) for accreditation-style review.",
        "effort": "Medium",
    },
]


def _artifact_meta(label: str, rel_path: str) -> dict:
    path = os.path.join(DATA_RAW_DIR, rel_path)
    out = {
        "label": label,
        "relative_path": rel_path,
        "present": os.path.isfile(path),
        "modified": None,
        "size_kb": None,
        "rows": None,
    }
    if not out["present"]:
        return out
    try:
        st = os.stat(path)
        out["modified"] = datetime.utcfromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M UTC")
        out["size_kb"] = round(st.st_size / 1024, 1)
    except OSError:
        pass
    if rel_path.endswith(".csv"):
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                out["rows"] = max(0, sum(1 for _ in f) - 1)
        except OSError:
            pass
    return out


def build_app_meta() -> dict:
    """Structured metadata for professional data-lineage UI."""
    research = {}
    ref_path = os.path.join(DATA_RAW_DIR, "research_references.json")
    if os.path.isfile(ref_path):
        try:
            with open(ref_path, encoding="utf-8") as f:
                research = json.load(f)
        except (json.JSONDecodeError, OSError):
            research = {}

    highlights = []
    for item in (research.get("enrollment_research") or [])[:5]:
        highlights.append({
            "title": item.get("title"),
            "source": item.get("source"),
            "url": item.get("url"),
            "year": item.get("year"),
        })

    artifacts = [
        _artifact_meta("BLS salary / OES extract", "bls_salary_data.csv"),
        _artifact_meta("Job market rollup", "job_market_data.csv"),
        _artifact_meta("IPEDS institutions", "ipeds_institutions.csv"),
        _artifact_meta("Research reference index", "research_references.json"),
        _artifact_meta("Employer map (geo)", "employers_2024.csv"),
        _artifact_meta("Institution program flags (geo)", "institutions_programs_2024.csv"),
        _artifact_meta("Employer-to-program overrides", "employer_program_map.csv"),
        _artifact_meta("IPEDS enrollment extract", "ipeds_real.csv"),
    ]

    geo_dir_ok = os.path.isdir(GEO_DATA_DIR)
    return {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "product_tagline": "Tri-state decision intelligence for AI and cybersecurity program launches.",
        "policy_note": (
            "EduPredict Pro is designed around official statistical releases and documented downloads. "
            "We do not rely on scraping paywalled or terms-restricted sites."
        ),
        "official_sources": OFFICIAL_DATA_STACK,
        "artifacts": artifacts,
        "roadmap": DATA_IMPROVEMENT_ROADMAP,
        "research_catalog_updated": research.get("last_updated"),
        "research_highlights": highlights,
        "geo_bundle": {
            "geo_data_dir_present": geo_dir_ok,
            "employers_csv": os.path.isfile(os.path.join(GEO_DATA_DIR, "employers_2024.csv")),
        },
    }


@app.route("/api/meta")
@login_required
def api_meta():
    """App metadata: sources, file freshness, roadmap (for professional lineage UI)."""
    return jsonify(build_app_meta())


# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with email authentication."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        
        # Validate email format
        if not email or '@' not in email:
            flash('Please enter a valid email address', 'error')
            return render_template('login.html')
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact an administrator.', 'error')
                return render_template('login.html')
            
            login_user(user, remember=True)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Log activity
            log_activity(user.id, 'login', f'User logged in from {request.remote_addr}')
            
            flash(f'Welcome back! You are logged in as {email}', 'info')
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout user."""
    log_activity(current_user.id, 'logout', 'User logged out')
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def admin_users():
    """Admin panel to manage users (admin only)."""
    if not current_user.is_admin:
        flash('Admin access required', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'on'
        
        # Validate email
        if not validate_email(email):
            flash('Invalid email format', 'error')
            return redirect(url_for('admin_users'))
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('admin_users'))
        
        # Create new user
        try:
            new_user = User(
                email=email,
                username=email.split('@')[0],  # Use local part as username
                is_admin=is_admin,
                is_active=True
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            
            log_activity(current_user.id, 'create_user', f'Created user {email}')
            flash(f'User {email} created successfully', 'info')
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'error')
    
    # Get all users for display
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users)


@app.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@login_required
def toggle_user(user_id):
    """Toggle user active status."""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin required'}), 403
    
    user = User.query.get_or_404(user_id)
    
    # Prevent deactivating yourself
    if user.id == current_user.id:
        return jsonify({'success': False, 'error': 'Cannot deactivate yourself'}), 400
    
    user.is_active = not user.is_active
    db.session.commit()
    
    log_activity(current_user.id, 'toggle_user', f'{"Activated" if user.is_active else "Deactivated"} user {user.email}')
    
    return jsonify({
        'success': True, 
        'is_active': user.is_active,
        'message': f'User {"activated" if user.is_active else "deactivated"}'
    })


@app.route('/admin/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
def reset_password(user_id):
    """Reset user password."""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin required'}), 403
    
    user = User.query.get_or_404(user_id)
    new_password = request.json.get('password')
    
    if not new_password or len(new_password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
    
    user.set_password(new_password)
    db.session.commit()
    
    log_activity(current_user.id, 'reset_password', f'Reset password for {user.email}')
    
    return jsonify({'success': True, 'message': 'Password reset successfully'})


# Helper function for logging
def log_activity(user_id, action, details=None):
    """Log user activity."""
    try:
        log = ActivityLog(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()


# Main Application Routes
@app.route('/')
@login_required
def index():
    """Landing page."""
    return render_template('index.html')


@app.route('/dashboard')
@login_required
def dashboard():
    """Forecast dashboard."""
    return render_template('dashboard.html',
                         programs=PROGRAMS,
                         student_types=STUDENT_TYPES,
                         terms=TERMS,
                         scenarios=SCENARIOS,
                         states=STATES)


@app.route('/api/forecast', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def api_forecast():
    """API endpoint for enrollment forecast."""
    data = request.get_json()
    
    program = data.get('program', 'MS in AI')
    student_type = data.get('student_type', 'International')
    term = data.get('term', 'FA26')
    scenario = data.get('scenario', 'Baseline')
    state = data.get('state', 'CT')
    
    # Get forecast
    forecast = quick_forecast(program, student_type, term, scenario, state)
    
    # Get ROI
    roi = quick_roi(program, state,
                   forecast.year1_enrollment,
                   forecast.year2_enrollment,
                   forecast.year3_enrollment,
                   student_type)
    
    # Get job market data
    job_signal = job_analyzer.get_signal(state, program)
    ai_exposure = ai_db.get_program_exposure(program)
    
    # Get recommendation
    rec = job_analyzer.get_program_recommendation(state, program)
    
    # Calculate overall recommendation
    if roi.roi_ratio >= 1.5 and forecast.confidence_score >= 0.75:
        recommendation = "STRONG GO"
        rec_class = "strong-go"
    elif roi.roi_ratio >= 1.0 and forecast.confidence_score >= 0.60:
        recommendation = "GO"
        rec_class = "go"
    elif roi.roi_ratio >= 0.7 or forecast.confidence_score >= 0.50:
        recommendation = "CONDITIONAL"
        rec_class = "conditional"
    else:
        recommendation = "RECONSIDER"
        rec_class = "reconsider"
    
    if roi.launch_recommendation == "delay":
        recommendation = "DO NOT LAUNCH"
        rec_class = "do-not-launch"
    
    # Log forecast to database
    try:
        history = ForecastHistory(
            user_id=current_user.id,
            program=program,
            student_type=student_type,
            term=term,
            scenario=scenario,
            state=state,
            year1_enrollment=forecast.year1_enrollment,
            projected_pool=forecast.projected_pool,
            roi_ratio=roi.roi_ratio,
            confidence=forecast.confidence_score,
            recommendation=recommendation
        )
        db.session.add(history)
        db.session.commit()
        
        # Log activity
        log_activity(current_user.id, 'forecast', 
                    f'{program} for {state} - {recommendation} (ROI: {roi.roi_ratio}x)')
    except Exception:
        db.session.rollback()

    return jsonify({
        'success': True,
        'forecast': {
            'year1': forecast.year1_enrollment,
            'year2': forecast.year2_enrollment,
            'year3': forecast.year3_enrollment,
            'year1_low': forecast.year1_low,
            'year1_high': forecast.year1_high,
            'pool': forecast.projected_pool,
            'confidence': forecast.confidence_score,
            'confidence_pct': int(forecast.confidence_score * 100),
            'risk_level': forecast.risk_level,
            'recommendation_confidence': forecast.recommendation_confidence,
            'warning_flags': forecast.warning_flags
        },
        'roi': {
            'ratio': roi.roi_ratio,
            'starting_salary': roi.starting_salary,
            'salary_5year': roi.salary_5year,
            'revenue': roi.total_tuition_revenue,
            'costs': roi.program_cost_estimate,
            'payback_years': roi.payback_period_years,
            'break_even': roi.break_even_enrollment,
            'financial_warnings': roi.financial_warnings
        },
        'job_market': {
            'growth_rate': job_signal.job_growth_rate,
            'open_positions': job_signal.open_positions_estimate,
            'demand_level': job_signal.demand_level,
            'demand_score': job_analyzer.get_demand_score(state, program),
            'ai_exposure': ai_exposure.observed_exposure,
            'ai_exposure_pct': int(ai_exposure.observed_exposure * 100),
            'risk_level': ai_exposure.risk_level.value,
            'coverage_gap': ai_exposure.coverage_gap,
            'bls_impact': ai_exposure.bls_growth_projection_2034,
            'young_worker_impact': ai_exposure.young_worker_hiring_impact,
            'key_finding': ai_exposure.key_finding
        },
        'recommendation': {
            'text': recommendation,
            'class': rec_class,
            'demand_score': rec['demand_score'],
            'rationale': rec['rationale'],
            'warnings': rec['warnings'],
            'opportunities': rec['opportunities'],
            'bls_10yr_growth_pct': rec.get('bls_10yr_growth_pct', 0),
            'bls_annual_openings': rec.get('bls_annual_openings', 0),
            'metro_count': rec.get('metro_count', 0),
            'total_metro_ai_postings': rec.get('total_metro_ai_postings', 0),
        },
        'inputs': {
            'program': program,
            'student_type': student_type,
            'term': term,
            'scenario': scenario,
            'state': state
        }
    })


@app.route('/api/scenarios', methods=['POST'])
@login_required
def api_scenarios():
    """Get all scenario comparisons."""
    data = request.get_json()
    
    program = data.get('program', 'MS in AI')
    student_type = data.get('student_type', 'International')
    term = data.get('term', 'FA26')
    state = data.get('state', 'CT')
    
    scenarios_data = []
    for scen in SCENARIOS:
        forecast = quick_forecast(program, student_type, term, scen, state)
        scenarios_data.append({
            'scenario': scen,
            'year1': forecast.year1_enrollment,
            'pool': forecast.projected_pool,
            'confidence': forecast.confidence_score
        })
    
    return jsonify({'scenarios': scenarios_data})


@app.route('/api/states', methods=['POST'])
@login_required
def api_states():
    """Get state comparison data."""
    data = request.get_json()
    
    program = data.get('program', 'MS in AI')
    student_type = data.get('student_type', 'International')
    scenario = data.get('scenario', 'Baseline')
    term = data.get('term', 'FA26')
    
    states_data = []
    for st in STATES:
        forecast = quick_forecast(program, student_type, term, scenario, st)
        job_signal = job_analyzer.get_signal(st, program)
        states_data.append({
            'state': st,
            'year1': forecast.year1_enrollment,
            'year2': forecast.year2_enrollment,
            'year3': forecast.year3_enrollment,
            'pool': forecast.projected_pool,
            'growth_rate': job_signal.job_growth_rate,
            'demand_score': job_analyzer.get_demand_score(st, program)
        })
    
    return jsonify({'states': states_data})


def _read_csv_rows(path):
    if not os.path.exists(path):
        return []
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


# Map UI program -> tag used in optional employer_program_map.csv (programs column)
_GEO_PROGRAM_TAG = {
    "BS in AI": "BS",
    "MS in AI": "MS",
    "AI in Cybersecurity": "CYBER",
}

# AI-sector employers that are especially relevant on the cyber program map (name hints)
_CYBER_PROGRAM_NAME_HINTS = (
    "CYBER", "CISO", "SECURITY", "LOCKHEED", "SIKORSKY", "RAYTHEON", "RTX", "LEIDOS",
    "GDIT", "BOOZ", "MANDIANT", "PALO ALTO", "CROWDSTRIKE", "PALANTIR",
)


def _load_employer_program_overrides() -> dict:
    """company_name -> set of tags BS, MS, CYBER from data/raw/employer_program_map.csv"""
    path = os.path.join(DATA_RAW_DIR, "employer_program_map.csv")
    out = {}
    for row in _read_csv_rows(path):
        name = (row.get("company_name") or "").strip()
        raw = (row.get("programs") or "").upper().replace(" ", "")
        if not name:
            continue
        tags = {t.strip() for t in raw.split(",") if t.strip() in ("BS", "MS", "CYBER")}
        if tags:
            out[name] = tags
    return out


def _employer_matches_program(e: dict, program: str, overrides: dict) -> bool:
    """Filter employers by degree/program track (heuristic + optional CSV overrides)."""
    if program not in PROGRAMS:
        program = "MS in AI"
    name = (e.get("company_name") or "").strip()
    tag = _GEO_PROGRAM_TAG.get(program, "MS")
    if name in overrides:
        return tag in overrides[name]

    sec = (e.get("sector") or "AI").strip()
    hires = (e.get("hires_new_grads") or "").strip()
    ctype = (e.get("company_type") or "").strip()
    uname = name.upper()

    if program == "MS in AI":
        return True

    if program == "BS in AI":
        if sec == "AI":
            return True
        if sec == "Cybersecurity":
            return hires == "Yes"
        return False

    if program == "AI in Cybersecurity":
        if sec == "Cybersecurity":
            return True
        if sec == "AI":
            if ctype == "Defense":
                return True
            return any(h in uname for h in _CYBER_PROGRAM_NAME_HINTS)
        return False

    return True


def _institution_ready_for_program(program: str, prog_row: dict) -> bool:
    if program == "BS in AI":
        return prog_row.get("has_bs_ai") == "Yes"
    if program == "MS in AI":
        return prog_row.get("has_ms_ai") == "Yes"
    if program == "AI in Cybersecurity":
        return prog_row.get("has_ai_cybersecurity") == "Yes"
    return (
        prog_row.get("has_ms_ai") == "Yes"
        or prog_row.get("has_bs_ai") == "Yes"
        or prog_row.get("has_ai_cybersecurity") == "Yes"
    )


@app.route('/api/geo-insights')
@login_required
def api_geo_insights():
    """Serve employer and institution-map data from shared team folder."""
    program = request.args.get("program") or "MS in AI"
    if program not in PROGRAMS:
        program = "MS in AI"

    employers_path = os.path.join(GEO_DATA_DIR, "employers_2024.csv")
    programs_path = os.path.join(GEO_DATA_DIR, "institutions_programs_2024.csv")
    ipeds_path = os.path.join(BASE_DIR, "data", "raw", "ipeds_institutions.csv")

    employers_rows = _read_csv_rows(employers_path)
    programs_rows = _read_csv_rows(programs_path)
    ipeds_rows = _read_csv_rows(ipeds_path)
    overrides = _load_employer_program_overrides()

    # Keep only the states used in this project and rows with coordinates
    employers_all = []
    for r in employers_rows:
        st = (r.get("state") or "").strip()
        lat = r.get("lat")
        lng = r.get("lng") or r.get("lon")
        if st not in STATES or not lat or not lng:
            continue
        employers_all.append({
            "company_name": r.get("company_name", ""),
            "city": r.get("city", ""),
            "state": st,
            "sector": r.get("sector", "AI"),
            "company_type": r.get("company_type", ""),
            "hires_new_grads": r.get("hires_new_grads", ""),
            "approx_annual_new_grad_hires": r.get("approx_annual_new_grad_hires", ""),
            "lat": float(lat),
            "lng": float(lng),
        })

    employers = [e for e in employers_all if _employer_matches_program(e, program, overrides)]

    filter_notes = {
        "MS in AI": "Showing full tri-state AI + cybersecurity employer set (typical MS pipeline).",
        "BS in AI": "BS-focused view: all AI-sector employers plus cybersecurity firms that hire new graduates.",
        "AI in Cybersecurity": "Cyber-focused view: cybersecurity employers plus defense / security-heavy AI employers.",
    }

    # Program availability counts by state (matches selected program track)
    programs_by_state = {s: {"total": 0, "ready": 0} for s in STATES}
    for row in ipeds_rows:
        st = (row.get("state") or "").strip()
        if st in programs_by_state:
            programs_by_state[st]["total"] += 1

    prog_by_name = {r.get("institution_name", "").strip(): r for r in programs_rows}
    for inst in ipeds_rows:
        st = (inst.get("state") or "").strip()
        if st not in programs_by_state:
            continue
        prow = prog_by_name.get((inst.get("institution_name") or "").strip(), {})
        if _institution_ready_for_program(program, prow):
            programs_by_state[st]["ready"] += 1

    return jsonify({
        "employers": employers,
        "employers_total": len(employers_all),
        "employers_shown": len(employers),
        "program": program,
        "employer_filter_note": filter_notes.get(program, ""),
        "programs_by_state": programs_by_state,
        "institution_map_note": (
            f"Institutions with a confirmed {program} (or matching track) in institutions_programs_2024.csv."
        ),
        "source_ok": {
            "employers_2024": os.path.exists(employers_path),
            "institutions_programs_2024": os.path.exists(programs_path),
            "ipeds_institutions": os.path.exists(ipeds_path),
            "employer_program_map": os.path.exists(os.path.join(DATA_RAW_DIR, "employer_program_map.csv")),
        }
    })


@app.route('/api/validate')
@login_required
def api_validate():
    """Validate all 162 combinations."""
    results = []
    passed = 0
    failed = 0
    
    for program in PROGRAMS:
        for student_type in STUDENT_TYPES:
            for term in TERMS:
                for scenario in SCENARIOS:
                    for state in STATES:
                        try:
                            forecast = quick_forecast(program, student_type, term, scenario, state)
                            roi = quick_roi(program, state,
                                          forecast.year1_enrollment,
                                          forecast.year2_enrollment,
                                          forecast.year3_enrollment,
                                          student_type)
                            
                            # Basic sanity checks
                            assert forecast.year1_enrollment >= 0
                            assert forecast.year2_enrollment >= forecast.year1_enrollment * 0.8
                            assert roi.roi_ratio >= 0
                            
                            passed += 1
                        except Exception as e:
                            failed += 1
                            results.append({
                                'combination': f"{program} + {student_type} + {term} + {scenario} + {state}",
                                'error': str(e)
                            })
    
    return jsonify({
        'total': passed + failed,
        'passed': passed,
        'failed': failed,
        'success_rate': passed / (passed + failed) * 100,
        'errors': results[:10]  # First 10 errors only
    })


@app.route('/api/ai-report/<program>')
@login_required
def api_ai_report(program):
    """Get AI exposure report for a program."""
    report = quick_ai_report(program)
    return jsonify(report)


@app.route('/health')
def health():
    """Health check endpoint for AWS."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


@app.route('/api/report', methods=['POST'])
@login_required
def api_report():
    """Generate and download PDF report."""
    if not FPDF_AVAILABLE:
        return jsonify({'success': False, 'error': 'PDF generation not available'}), 503
    
    data = request.get_json()
    
    program = data.get('program', 'MS in AI')
    student_type = data.get('student_type', 'International')
    term = data.get('term', 'FA26')
    scenario = data.get('scenario', 'Baseline')
    state = data.get('state', 'CT')
    
    # Get all data
    forecast = quick_forecast(program, student_type, term, scenario, state)
    roi = quick_roi(program, state,
                   forecast.year1_enrollment,
                   forecast.year2_enrollment,
                   forecast.year3_enrollment,
                   student_type)
    job_signal = job_analyzer.get_signal(state, program)
    ai_exposure = ai_db.get_program_exposure(program)
    rec = job_analyzer.get_program_recommendation(state, program)
    
    # Determine recommendation
    if roi.roi_ratio >= 1.5 and forecast.confidence_score >= 0.75:
        recommendation = "STRONG GO"
    elif roi.roi_ratio >= 1.0 and forecast.confidence_score >= 0.60:
        recommendation = "GO"
    elif roi.roi_ratio >= 0.7 or forecast.confidence_score >= 0.50:
        recommendation = "CONDITIONAL"
    else:
        recommendation = "RECONSIDER"
    
    if roi.launch_recommendation == "delay":
        recommendation = "DO NOT LAUNCH"
    
    # Generate PDF
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font('Arial', 'B', 24)
    pdf.set_text_color(236, 72, 153)
    pdf.cell(0, 20, 'EduPredict Pro', 0, 1, 'C')
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, 'AI Degree Program Planning Report', 0, 1, 'C')
    pdf.cell(0, 10, f'Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}', 0, 1, 'C')
    pdf.ln(10)
    
    # Executive Summary Box
    pdf.set_fill_color(253, 242, 248)
    pdf.rect(10, pdf.get_y(), 190, 35, 'F')
    pdf.set_xy(15, pdf.get_y() + 5)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(131, 24, 67)
    pdf.cell(0, 10, 'EXECUTIVE SUMMARY', 0, 1)
    pdf.set_xy(15, pdf.get_y())
    pdf.set_font('Arial', '', 11)
    pdf.cell(95, 8, f'Program: {program}', 0, 0)
    pdf.cell(95, 8, f'State: {state}', 0, 1)
    pdf.set_xy(15, pdf.get_y())
    pdf.cell(95, 8, f'Student Type: {student_type}', 0, 0)
    pdf.cell(95, 8, f'Scenario: {scenario}', 0, 1)
    pdf.set_xy(15, pdf.get_y())
    pdf.cell(95, 8, f'Launch Term: {term}', 0, 1)
    pdf.ln(20)
    
    # Recommendation
    pdf.set_font('Arial', 'B', 16)
    if recommendation == "STRONG GO":
        pdf.set_text_color(16, 185, 129)
    elif recommendation == "GO":
        pdf.set_text_color(236, 72, 153)
    elif recommendation == "CONDITIONAL":
        pdf.set_text_color(245, 158, 11)
    else:
        pdf.set_text_color(239, 68, 68)
    pdf.cell(0, 15, f'Recommendation: {recommendation}', 0, 1, 'C')
    pdf.ln(5)
    
    # Key Metrics
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Key Metrics', 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 11)
    metrics = [
        ("Year 1 Enrollment", f"{forecast.year1_enrollment} students (range: {forecast.year1_low}-{forecast.year1_high})"),
        ("3-Year Student Pool", f"{forecast.projected_pool} students"),
        ("Forecast Confidence", f"{int(forecast.confidence_score * 100)}% ({forecast.recommendation_confidence.upper()} confidence)"),
        ("ROI Ratio", f"{roi.roi_ratio}x"),
        ("Starting Salary", f"${roi.starting_salary:,}"),
        ("Program Revenue (3yr)", f"${roi.total_tuition_revenue:,}"),
        ("Break-Even Enrollment", f"{roi.break_even_enrollment} students"),
        ("Payback Period", f"{roi.payback_period_years} years"),
    ]
    
    for label, value in metrics:
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(80, 8, label + ':', 0, 0)
        pdf.set_font('Arial', '', 10)
        pdf.cell(110, 8, value, 0, 1)
    
    pdf.ln(10)
    
    # AI Labor Market Analysis
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'AI Labor Market Analysis', 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 11)
    pdf.cell(80, 8, 'AI Exposure:', 0, 0)
    pdf.cell(110, 8, f"{int(ai_exposure.observed_exposure * 100)}% ({ai_exposure.risk_level.value.upper()} risk)", 0, 1)
    pdf.cell(80, 8, 'Coverage Gap:', 0, 0)
    pdf.cell(110, 8, f"{int(ai_exposure.coverage_gap * 100)}% (theory vs. reality)", 0, 1)
    pdf.cell(80, 8, 'BLS 2034 Impact:', 0, 0)
    pdf.cell(110, 8, f"{ai_exposure.bls_growth_projection_2034:.1f} percentage points", 0, 1)
    pdf.cell(80, 8, 'Job Market Growth:', 0, 0)
    pdf.cell(110, 8, f"{job_signal.job_growth_rate}% annually", 0, 1)
    pdf.ln(5)
    pdf.set_font('Arial', 'I', 9)
    pdf.multi_cell(0, 5, f"Key Finding: {ai_exposure.key_finding}")
    pdf.ln(10)
    
    # 3-Year Enrollment Projection
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '3-Year Enrollment Projection', 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(60, 10, 'Year', 1, 0, 'C')
    pdf.cell(65, 10, 'Enrollment', 1, 0, 'C')
    pdf.cell(65, 10, 'Confidence Range', 1, 1, 'C')
    
    pdf.set_font('Arial', '', 11)
    years = [
        ("Year 1", forecast.year1_enrollment, f"{forecast.year1_low}-{forecast.year1_high}"),
        ("Year 2", forecast.year2_enrollment, "-"),
        ("Year 3", forecast.year3_enrollment, f"{forecast.year3_low}-{forecast.year3_high}"),
    ]
    for year, enrollment, range_str in years:
        pdf.cell(60, 10, year, 1, 0, 'C')
        pdf.cell(65, 10, f"{enrollment} students", 1, 0, 'C')
        pdf.cell(65, 10, range_str, 1, 1, 'C')
    pdf.ln(10)
    
    # Warnings and Opportunities
    if forecast.warning_flags or roi.financial_warnings:
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(220, 38, 38)
        pdf.cell(0, 10, 'Warnings & Considerations', 0, 1)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', '', 10)
        for warning in forecast.warning_flags[:3]:
            pdf.cell(10, 6, '-', 0, 0)
            pdf.multi_cell(180, 6, warning)
        for warning in roi.financial_warnings[:3]:
            pdf.cell(10, 6, '-', 0, 0)
            pdf.multi_cell(180, 6, warning)
        pdf.ln(10)
    
    if rec['opportunities']:
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(22, 163, 74)
        pdf.cell(0, 10, 'Opportunities', 0, 1)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', '', 10)
        for opp in rec['opportunities'][:3]:
            pdf.cell(10, 6, '+', 0, 0)
            pdf.multi_cell(180, 6, opp)
        pdf.ln(10)
    
    # Footer
    pdf.set_y(-30)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 10, f'EduPredict Pro | Data: BLS 2023, Anthropic Economic Index 2026, IPEDS 2023-2024 | Report generated {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 0, 'C')
    
    # Save to buffer
    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'EduPredict_Report_{state}_{term}_{program.replace(" ", "_")}.pdf'
    )


@app.route('/api/chat', methods=['POST'])
@login_required
@limiter.limit("20 per minute")
def api_chat():
    """Stream an AI explanation of the current forecast results."""
    if not ANTHROPIC_AVAILABLE:
        return jsonify({'error': 'AI chat not configured. Set ANTHROPIC_API_KEY.'}), 503

    body = request.get_json(silent=True) or {}
    user_message = (body.get('message') or '').strip()
    context = body.get('context') or {}
    history = body.get('history') or []

    if not user_message:
        return jsonify({'error': 'message is required'}), 400

    # Build a rich context block from the forecast data the user already ran
    def _fmt_context(ctx):
        if not ctx:
            return "No forecast has been run yet."
        inp = ctx.get('inputs', {})
        fc = ctx.get('forecast', {})
        roi = ctx.get('roi', {})
        jm = ctx.get('job_market', {})
        rec = ctx.get('recommendation', {})
        return (
            f"Program: {inp.get('program','?')} | State: {inp.get('state','?')} | "
            f"Student type: {inp.get('student_type','?')} | Term: {inp.get('term','?')} | "
            f"Scenario: {inp.get('scenario','?')}\n"
            f"Enrollment - Year 1: {fc.get('year1','?')}, Year 2: {fc.get('year2','?')}, "
            f"Year 3: {fc.get('year3','?')} (pool: {fc.get('pool','?')}, "
            f"confidence: {fc.get('confidence_pct','?')}%, risk: {fc.get('risk_level','?')})\n"
            f"ROI - ratio: {roi.get('ratio','?')}x, revenue: ${roi.get('revenue','?'):,}, "
            f"costs: ${roi.get('costs','?'):,}, payback: {roi.get('payback_years','?')} yrs\n"
            f"Job market - demand: {jm.get('demand_level','?')}, growth: {jm.get('growth_rate','?')}%, "
            f"open positions: {jm.get('open_positions','?')}, AI exposure: {jm.get('ai_exposure_pct','?')}%\n"
            f"Recommendation: {rec.get('text','?')} (demand score: {rec.get('demand_score','?')})\n"
            f"Rationale: {rec.get('rationale','?')}"
        )

    system_prompt = (
        "You are EduPredict Advisor, an expert AI assistant embedded in EduPredict Pro - "
        "a decision-intelligence platform for university deans and academic planners. "
        "You explain enrollment forecasts, ROI calculations, and labor market signals in plain language. "
        "Be concise, direct, and data-driven. When numbers are available, reference them. "
        "Never fabricate data - only use the context provided. "
        "If the user asks something outside the scope of the current forecast, say so clearly.\n\n"
        "Current forecast context:\n"
        f"{_fmt_context(context)}"
    )

    # Build message list: history + new user message
    messages = []
    for turn in history[-10:]:  # cap at 10 prior turns
        role = turn.get('role')
        content = turn.get('content', '')
        if role in ('user', 'assistant') and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})

    client = _anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def generate():
        with client.messages.stream(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=[{
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"}
            }],
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                # SSE format
                yield f"data: {json.dumps({'delta': text})}\n\n"
        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )


def init_db():
    """Initialize database and create default admin user."""
    with app.app_context():
        db.create_all()
        
        # Create default admin user if none exists.
        # Credentials can be injected via env for safer deploys.
        admin_email = os.environ.get('EDUPREDICT_ADMIN_EMAIL', 'admin@edupredict.local').strip().lower()
        admin_password = os.environ.get('EDUPREDICT_ADMIN_PASSWORD')
        is_production = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('PORT')
        if not admin_password:
            if is_production:
                raise RuntimeError('EDUPREDICT_ADMIN_PASSWORD env var must be set in production.')
            import secrets as _secrets
            admin_password = _secrets.token_urlsafe(16)
            print(f"WARNING: EDUPREDICT_ADMIN_PASSWORD not set. Generated password: {admin_password}")
            print("Set EDUPREDICT_ADMIN_PASSWORD env var before deploying to production.")
        if not User.query.filter_by(email=admin_email).first():
            admin = User(
                email=admin_email,
                username='admin',
                is_admin=True,
                last_login=datetime.utcnow()
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print(f"Default admin user created: {admin_email}")


if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Development server
    port = int(os.environ.get("PORT", 8080))
    debug_enabled = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true", "yes", "on")
    app.run(host='0.0.0.0', port=port, debug=debug_enabled)
