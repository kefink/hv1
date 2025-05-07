from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import Teacher
from app import limiter
from app.forms import LoginForm  # Import LoginForm

bp = Blueprint('auth', __name__)

@bp.route("/")
def index():
    return render_template("login.html")

@bp.route("/admin_login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def admin_login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        teacher = Teacher.query.filter_by(username=username, role="headteacher").first()
        if teacher and teacher.check_password(password):
            login_user(teacher)  # Log in with Flask-Login
            session['role'] = 'headteacher'  # Still store role in session for role-based access
            session.permanent = True
            return redirect(url_for("headteacher.headteacher"))
        return render_template("admin_login.html", form=form, error="Invalid credentials")
    return render_template("admin_login.html", form=form)

@bp.route("/teacher_login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def teacher_login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        teacher = Teacher.query.filter_by(username=username, role="teacher").first()
        if teacher and teacher.check_password(password):
            login_user(teacher)  # Log in with Flask-Login
            session['role'] = 'teacher'
            session.permanent = True
            return redirect(url_for("teacher.teacher"))
        return render_template("teacher_login.html", form=form, error="Invalid credentials")
    return render_template("teacher_login.html", form=form)

@bp.route("/classteacher_login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def classteacher_login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        teacher = Teacher.query.filter_by(username=username, role="classteacher").first()
        if teacher and teacher.check_password(password):
            login_user(teacher)  # Log in with Flask-Login
            session['teacher_id'] = teacher.id
            session['role'] = 'classteacher'  # Make sure this matches what we check in manage.py
            session.permanent = True
            return redirect(url_for("classteacher.classteacher"))
        return render_template("classteacher_login.html", form=form, error="Invalid credentials")
    return render_template("classteacher_login.html", form=form)

@bp.route("/dashboard")
@login_required  # Require login for dashboard
def dashboard_redirect():
    role = session.get('role')
    if role == 'headteacher':
        return redirect(url_for('headteacher.student_dashboard'))
    elif role == 'teacher':
        return redirect(url_for('teacher.teacher'))
    elif role == 'classteacher':
        return redirect(url_for('classteacher.classteacher'))
    return redirect(url_for('auth.index'))

@bp.route("/logout")
def logout():
    logout_user()  # Log out with Flask-Login
    session.clear()
    return redirect(url_for('auth.index'))