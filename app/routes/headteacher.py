from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.utils.analytics import calculate_school_stats, get_performance_data

bp = Blueprint('headteacher', __name__, url_prefix='/headteacher')

@bp.route("/")
@login_required
def headteacher():
    if current_user.role != 'headteacher':
        return redirect(url_for('auth.admin_login'))
    
    stats = calculate_school_stats()
    performance_data = get_performance_data()
    return render_template('headteacher.html', **stats, performance_data=performance_data)

@bp.route("/student_dashboard")
@login_required
def student_dashboard():
    if current_user.role != 'headteacher':
        return redirect(url_for('auth.admin_login'))
    return render_template('student_dashboard.html', message="Student Dashboard Placeholder")