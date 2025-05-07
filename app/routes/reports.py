# app/routes/reports.py
from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from app.models import Grade, Stream, Term, AssessmentType, Student, Mark, Subject
from app import db
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

bp = Blueprint('reports', __name__, url_prefix='/reports')

def get_performance_category(percentage):
    """Shared helper function for performance categories"""
    if percentage >= 75:
        return "Excellent"
    elif 50 <= percentage < 75:
        return "Good"
    elif 30 <= percentage < 50:
        return "Average"
    else:
        return "Below Expectations"

def generate_class_report_data(grade, stream, term, assessment_type):
    """Shared function to generate class report data"""
    stream_obj = Stream.query.join(Grade).filter(Grade.level == grade, Stream.name == stream[-1]).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

    if not (stream_obj and term_obj and assessment_type_obj):
        return None, "Invalid grade, stream, term, or assessment type"

    students = Student.query.filter_by(stream_id=stream_obj.id).all()
    subjects = Subject.query.all()
    class_data = []
    total_marks = 0

    for student in students:
        student_marks = {}
        for subject in subjects:
            mark = Mark.query.filter_by(
                student_id=student.id,
                subject_id=subject.id,
                term_id=term_obj.id,
                assessment_type_id=assessment_type_obj.id
            ).first()
            student_marks[subject.name] = mark.mark if mark else 0
            if mark:
                total_marks = mark.total_marks
        total = sum(student_marks.values())
        avg_percentage = (total / (len(subjects) * total_marks)) * 100 if total_marks > 0 else 0
        class_data.append({
            'student': student.name,
            'marks': student_marks,
            'total_marks': total,
            'average_percentage': avg_percentage
        })

    if not class_data:
        return None, "No data available for this report"

    # Add ranking and performance categories
    class_data.sort(key=lambda x: x['total_marks'], reverse=True)
    indexed_class_data = []
    for idx, student_data in enumerate(class_data, 1):
        student_data_copy = student_data.copy()
        student_data_copy['index'] = idx
        student_data_copy['performance_category'] = get_performance_category(student_data['average_percentage'])
        student_data_copy['rank'] = idx
        indexed_class_data.append(student_data_copy)

    # Calculate statistics
    stats = {'exceeding': 0, 'meeting': 0, 'approaching': 0, 'below': 0}
    for student_data in class_data:
        avg = student_data['average_percentage']
        if avg >= 75:
            stats['exceeding'] += 1
        elif 50 <= avg < 75:
            stats['meeting'] += 1
        elif 30 <= avg < 50:
            stats['approaching'] += 1
        else:
            stats['below'] += 1

    return {
        'class_data': indexed_class_data,
        'stats': stats,
        'grade': grade,
        'stream': stream,
        'term': term,
        'assessment_type': assessment_type,
        'total_marks': total_marks,
        'subjects': [subject.name for subject in subjects],
        'current_date': datetime.now().strftime("%Y-%m-%d")
    }, None

@bp.route("/preview_class_report/<grade>/<stream>/<term>/<assessment_type>")
@login_required
def preview_class_report(grade, stream, term, assessment_type):
    report_data, error = generate_class_report_data(grade, stream, term, assessment_type)
    if error:
        flash(error, "error")
        return redirect(url_for('classteacher.classteacher'))

    from app.utils.constants import SUBJECT_ABBREVIATIONS
    subjects = Subject.query.all()
    abbreviated_subjects = [SUBJECT_ABBREVIATIONS.get(subject.name, subject.name[:4].upper()) for subject in subjects]

    return render_template(
        "preview_class_report.html",
        abbreviated_subjects=abbreviated_subjects,
        **report_data
    )

@bp.route("/edit_class_report/<grade>/<stream>/<term>/<assessment_type>", methods=["GET", "POST"])
@login_required
def edit_class_report(grade, stream, term, assessment_type):
    # ... [keep your existing edit_class_report implementation] ...
    pass

@bp.route("/grade_marksheet/<grade>/<term>/<assessment_type>/<action>")
@login_required
def generate_grade_marksheet(grade, term, assessment_type, action):
    """
    Enhanced grade marksheet generator with better error handling and structure
    """
    try:
        # Validate inputs
        stream_objs = Stream.query.join(Grade).filter(Grade.level == grade).all()
        term_obj = Term.query.filter_by(name=term).first_or_404()
        assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first_or_404()

        if not stream_objs:
            flash(f"No streams found for grade {grade}", "error")
            return redirect(url_for('classteacher.classteacher'))

        # Fetch all students across streams for the grade
        students = Student.query.filter(Student.stream_id.in_([s.id for s in stream_objs])).all()

        if not students:
            flash(f"No students found for grade {grade}", "error")
            return redirect(url_for('classteacher.classteacher'))

        subjects = Subject.query.all()
        if not subjects:
            flash("No subjects found in system", "error")
            return redirect(url_for('classteacher.classteacher'))

        # Generate marks data
        class_data = _generate_marks_data(students, subjects, term_obj, assessment_type_obj)

        if not class_data:
            flash(f"No marks found for the selected criteria", "error")
            return redirect(url_for('classteacher.classteacher'))

        # Sort by total marks and add ranks
        class_data.sort(key=lambda x: x['total_marks'], reverse=True)
        for idx, student_data in enumerate(class_data, 1):
            student_data['rank'] = idx

        # Generate performance statistics
        stats = _calculate_performance_stats(class_data)

        # Prepare template context
        context = {
            'class_data': class_data,
            'stats': stats,
            'grade': grade,
            'term': term,
            'assessment_type': assessment_type,
            'total_marks': class_data[0]['total_marks'] if class_data else 0,
            'subjects': [subject.name for subject in subjects],
            'abbreviated_subjects': [s.name[:4].upper() for s in subjects],
            'current_date': datetime.now().strftime("%Y-%m-%d"),
            'user': current_user
        }

        if action == "preview":
            return render_template("grade_marksheet.html", **context)
        elif action == "download":
            return _generate_pdf_report(context)
        else:
            flash("Invalid action specified", "error")
            return redirect(url_for('classteacher.classteacher'))

    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while generating the report: {str(e)}", "error")
        return redirect(url_for('classteacher.classteacher'))

def _generate_marks_data(students, subjects, term_obj, assessment_type_obj):
    """Helper method to generate marks data"""
    class_data = []
    total_marks = 0

    for student in students:
        student_marks = {}
        for subject in subjects:
            mark = Mark.query.filter_by(
                student_id=student.id,
                subject_id=subject.id,
                term_id=term_obj.id,
                assessment_type_id=assessment_type_obj.id
            ).first()
            student_marks[subject.name] = mark.mark if mark else 0
            if mark and total_marks == 0:  # Get total_marks from first found mark
                total_marks = mark.total_marks

        total = sum(student_marks.values())
        avg_percentage = (total / (len(subjects) * total_marks)) * 100 if total_marks > 0 else 0

        class_data.append({
            'student': student,
            'marks': student_marks,
            'total_marks': total,
            'average_percentage': avg_percentage,
            'stream': student.stream.name
        })

    return class_data

def _calculate_performance_stats(class_data):
    """Calculate performance statistics"""
    stats = {'exceeding': 0, 'meeting': 0, 'approaching': 0, 'below': 0}

    for student_data in class_data:
        avg = student_data['average_percentage']
        if avg >= 75:
            stats['exceeding'] += 1
        elif 50 <= avg < 75:
            stats['meeting'] += 1
        elif 30 <= avg < 50:
            stats['approaching'] += 1
        else:
            stats['below'] += 1

    return stats

def _generate_pdf_report(context):
    """Generate PDF report (to be implemented)"""
    flash("PDF download functionality is coming soon!", "info")
    return redirect(url_for('reports.generate_grade_marksheet',
                            grade=context['grade'],
                            term=context['term'],
                            assessment_type=context['assessment_type'],
                            action='preview'))
