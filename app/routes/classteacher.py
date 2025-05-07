from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify, flash, get_flashed_messages
from flask_login import login_required, current_user
from app.models import Grade, Stream, Term, AssessmentType, Student, Mark, Subject, Teacher
from app.utils.constants import SUBJECT_MAPPING, ALL_SUBJECTS
from app import db, cache
from flask_paginate import Pagination, get_page_args
from datetime import datetime
from app.routes.reports import generate_class_report_data  # Import shared function

bp = Blueprint('classteacher', __name__)

# Check function to verify if the user has the correct role
def check_classteacher():
    if not current_user.is_authenticated:
        flash('You must be logged in to access this page')
        return False
    if 'role' not in session or session['role'] != 'classteacher':
        flash('You must be a class teacher to access this page')
        return False
    return True

@bp.route("/all_class_reports", methods=['GET'])
@login_required
def all_class_reports():
    if not check_classteacher():
        return redirect(url_for('auth.classteacher_login'))

    all_reports = []
    marks = Mark.query.join(Student).join(Stream).join(Grade).join(Term).join(AssessmentType).all()
    seen_combinations = set()
    for mark in marks:
        combination = (mark.student.stream.grade.level, mark.student.stream.name, mark.term.name, mark.assessment_type.name)
        if combination not in seen_combinations:
            seen_combinations.add(combination)
            all_reports.append({
                'grade': mark.student.stream.grade.level,
                'stream': f"Stream {mark.student.stream.name}",
                'term': mark.term.name,
                'assessment_type': mark.assessment_type.name,
                'date': mark.created_at.strftime('%Y-%m-%d') if mark.created_at else 'N/A'
            })

    return render_template('all_class_reports.html', all_reports=all_reports)

@bp.route("/classteacher", methods=["GET", "POST"])
@login_required
def classteacher():
    if not check_classteacher():
        return redirect(url_for('auth.classteacher_login'))

    # Use current_user instead of querying the database again
    teacher = current_user

    grades = [grade.level for grade in Grade.query.all()]
    grades_dict = {grade.level: grade.id for grade in Grade.query.all()}
    terms = [term.name for term in Term.query.all()]
    assessment_types = [assessment_type.name for assessment_type in AssessmentType.query.all()]
    streams = Stream.query.all()
    show_students = False
    students = []
    education_level = ""
    grade = ""
    stream = ""
    term = ""
    assessment_type = ""
    total_marks = 0
    show_download_button = False
    show_individual_report_button = False
    subjects = []
    stats = None
    class_data = None

    # Fetch recent reports with pagination
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    per_page = 5  # Show 5 reports per page
    recent_reports = []
    marks = Mark.query.join(Student).join(Stream).join(Grade).join(Term).join(AssessmentType).all()
    seen_combinations = set()
    for mark in marks:
        combination = (mark.student.stream.grade.level, mark.student.stream.name, mark.term.name, mark.assessment_type.name)
        if combination not in seen_combinations:
            seen_combinations.add(combination)
            recent_reports.append({
                'grade': mark.student.stream.grade.level,
                'stream': f"Stream {mark.student.stream.name}",
                'term': mark.term.name,
                'assessment_type': mark.assessment_type.name,
                'date': mark.created_at.strftime('%Y-%m-%d') if mark.created_at else 'N/A'
            })
    total = len(recent_reports)
    recent_reports_paginated = recent_reports[offset: offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    if request.method == "POST":
        education_level = request.form.get("education_level", "")
        grade = request.form.get("grade", "")
        stream = request.form.get("stream", "")
        term = request.form.get("term", "")
        assessment_type = request.form.get("assessment_type", "")
        try:
            total_marks = int(request.form.get("total_marks", 0))
        except ValueError:
            total_marks = 0

        # Use Subject_MAPPING if education_level matches, otherwise fall back to all subjects from DB
        subjects = SUBJECT_MAPPING.get(education_level, ALL_SUBJECTS) if education_level in SUBJECT_MAPPING else [s.name for s in Subject.query.all()]

        if "upload_marks" in request.form:
            if not all([education_level, grade, stream, term, assessment_type, total_marks > 0]):
                flash("Please fill in all fields before uploading marks", "error")
            else:
                stream_letter = stream.replace("Stream ", "") if stream.startswith("Stream ") else stream[-1]
                stream_obj = Stream.query.join(Grade).filter(Grade.level == grade, Stream.name == stream_letter).first()
                if stream_obj:
                    students = [student for student in Student.query.filter_by(stream_id=stream_obj.id).all()]
                    show_students = True
                else:
                    flash(f"No students found for grade {grade} stream {stream_letter}", "error")

        elif "submit_marks" in request.form:
            if not all([education_level, grade, stream, term, assessment_type, total_marks > 0]):
                flash("Please fill in all fields before submitting marks", "error")
            else:
                stream_letter = stream.replace("Stream ", "") if stream.startswith("Stream ") else stream[-1]
                stream_obj = Stream.query.join(Grade).filter(Grade.level == grade, Stream.name == stream_letter).first()
                term_obj = Term.query.filter_by(name=term).first()
                assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

                if not (stream_obj and term_obj and assessment_type_obj):
                    flash("Invalid selection for grade, stream, term, or assessment type", "error")
                else:
                    students = Student.query.filter_by(stream_id=stream_obj.id).all()
                    marks_data = []
                    any_marks_submitted = False
                    subject_marks = {subject: {} for subject in subjects}
                    subject_objs = {subject: Subject.query.filter_by(name=subject).first() for subject in subjects}

                    for student in students:
                        student_marks = {}
                        valid_student = True
                        for subject in subjects:
                            mark_key = f"mark_{student.name.replace(' ', '_')}_{subject.replace(' ', '_')}"
                            mark_value = request.form.get(mark_key, '')
                            if mark_value and mark_value.replace('.', '').isdigit():
                                mark = float(mark_value)
                                if 0 <= mark <= total_marks:
                                    subject_marks[subject][student.name] = mark
                                    student_marks[subject] = mark
                                    subject_obj = subject_objs[subject]
                                    if subject_obj:
                                        new_mark = Mark(
                                            student_id=student.id,
                                            subject_id=subject_obj.id,
                                            term_id=term_obj.id,
                                            assessment_type_id=assessment_type_obj.id,
                                            mark=mark,
                                            total_marks=total_marks
                                        )
                                        db.session.add(new_mark)
                                    any_marks_submitted = True
                                else:
                                    flash(f"Invalid mark for {student.name} in {subject}. Must be between 0 and {total_marks}.", "error")
                                    valid_student = False
                                    break
                            else:
                                flash(f"Missing or invalid mark for {student.name} in {subject}", "error")
                                valid_student = False
                                break
                        if valid_student:
                            marks_data.append([student, student_marks])

                    if any_marks_submitted and not get_flashed_messages(with_categories=True):
                        db.session.commit()
                        flash("Marks submitted successfully!", "success")
                        class_data = []
                        for student, student_marks in marks_data:
                            total = sum(student_marks.values())
                            avg_percentage = (total / (len(subjects) * total_marks)) * 100
                            class_data.append({
                                'student': student,
                                'marks': student_marks,
                                'total_marks': total,
                                'average_percentage': avg_percentage
                            })

                        class_data.sort(key=lambda x: x['total_marks'], reverse=True)
                        for i, student_data in enumerate(class_data, 1):
                            student_data['rank'] = i

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

                        show_download_button = True
                        show_individual_report_button = True

                        # Refresh recent reports after submission
                        recent_reports = []
                        marks = Mark.query.join(Student).join(Stream).join(Grade).join(Term).join(AssessmentType).all()
                        seen_combinations = set()
                        for mark in marks:
                            combination = (mark.student.stream.grade.level, mark.student.stream.name, mark.term.name, mark.assessment_type.name)
                            if combination not in seen_combinations:
                                seen_combinations.add(combination)
                                recent_reports.append({
                                    'grade': mark.student.stream.grade.level,
                                    'stream': f"Stream {mark.student.stream.name}",
                                    'term': mark.term.name,
                                    'assessment_type': mark.assessment_type.name,
                                    'date': mark.created_at.strftime('%Y-%m-%d') if mark.created_at else 'N/A'
                                })
                        total = len(recent_reports)
                        recent_reports_paginated = recent_reports[offset: offset + per_page]
                        pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

        elif "generate_stream_marksheet" in request.form or "download_stream_marksheet" in request.form:
            stream_grade = request.form.get("stream_grade", "")
            stream_term = request.form.get("stream_term", "")
            stream_assessment_type = request.form.get("stream_assessment_type", "")
            action = "preview" if "generate_stream_marksheet" in request.form else "download"

            if not all([stream_grade, stream_term, stream_assessment_type]):
                flash("Please fill in all fields to generate the grade marksheet", "error")
            else:
                return redirect(url_for('reports.generate_grade_marksheet',
                                        grade=stream_grade,
                                        term=stream_term,
                                        assessment_type=stream_assessment_type,
                                        action=action))

    return render_template(
        "classteacher.html",
        teacher=teacher,
        grades=grades,
        grades_dict=grades_dict,
        terms=terms,
        assessment_types=assessment_types,
        streams=streams,
        students=students,
        education_level=education_level,
        grade=grade,
        stream=stream,
        term=term,
        assessment_type=assessment_type,
        total_marks=total_marks,
        show_students=show_students,
        show_download_button=show_download_button,
        show_individual_report_button=show_individual_report_button,
        subjects=subjects,
        stats=stats,
        class_data=class_data,
        recent_reports=recent_reports_paginated,
        pagination=pagination
    )

@bp.route("/api/check_stream_status/<grade>/<term>/<assessment_type>")
@login_required
def check_stream_status(grade, term, assessment_type):
    if not check_classteacher():
        return jsonify({"error": "Unauthorized access"}), 401

    grade_obj = Grade.query.filter_by(level=grade).first()
    if not grade_obj:
        return jsonify({"error": f"Grade {grade} not found"}), 404

    streams = Stream.query.filter_by(grade_id=grade_obj.id).all()
    if not streams:
        return jsonify({"error": f"No streams found for grade {grade}"}), 404

    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

    if not (term_obj and assessment_type_obj):
        return jsonify({"error": "Invalid term or assessment type"}), 404

    stream_status = []
    for stream in streams:
        marks_exist = Mark.query.join(Student).filter(
            Student.stream_id == stream.id,
            Mark.term_id == term_obj.id,
            Mark.assessment_type_id == assessment_type_obj.id
        ).first() is not None

        stream_status.append({
            "name": f"Stream {stream.name}",
            "has_report": marks_exist
        })

    return jsonify({"streams": stream_status})

@bp.route("/preview_class_report/<grade>/<stream>/<term>/<assessment_type>")
@login_required
def preview_class_report(grade, stream, term, assessment_type):
    """Now just redirects to the reports blueprint version"""
    if not check_classteacher():
        return redirect(url_for('auth.classteacher_login'))

    return redirect(url_for('reports.preview_class_report',
                            grade=grade,
                            stream=stream,
                            term=term,
                            assessment_type=assessment_type))

@bp.route("/edit_class_report/<grade>/<stream>/<term>/<assessment_type>", methods=["GET", "POST"])
@login_required
def edit_class_report(grade, stream, term, assessment_type):
    if not check_classteacher():
        return redirect(url_for('auth.classteacher_login'))

    stream_obj = Stream.query.join(Grade).filter(Grade.level == grade, Stream.name == stream[-1]).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

    if not (stream_obj and term_obj and assessment_type_obj):
        flash("Invalid grade, stream, term, or assessment type", "error")
        return redirect(url_for('classteacher.classteacher'))

    students = Student.query.filter_by(stream_id=stream_obj.id).all()
    subjects = Subject.query.all()

    if not students or not subjects:
        flash("No students or subjects found for this class", "error")
        return redirect(url_for('classteacher.classteacher'))

    if request.method == 'POST':
        try:
            for student in students:
                for subject in subjects:
                    mark_key = f"mark_{student.id}_{subject.id}"
                    mark_value = request.form.get(mark_key)

                    if mark_value is not None and mark_value.strip():
                        mark_value = float(mark_value)
                        mark = Mark.query.filter_by(
                            student_id=student.id,
                            subject_id=subject.id,
                            term_id=term_obj.id,
                            assessment_type_id=assessment_type_obj.id
                        ).first()

                        if mark:
                            mark.mark = mark_value
                        else:
                            new_mark = Mark(
                                student_id=student.id,
                                subject_id=subject.id,
                                term_id=term_obj.id,
                                assessment_type_id=assessment_type_obj.id,
                                mark=mark_value,
                                total_marks=100  # Should this be dynamic?
                            )
                            db.session.add(new_mark)
            db.session.commit()
            flash("Marks updated successfully", "success")
            return redirect(url_for('classteacher.edit_class_report', grade=grade, stream=stream, term=term, assessment_type=assessment_type))
        except ValueError:
            db.session.rollback()
            flash("Invalid mark value provided", "error")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating marks: {str(e)}", "error")

    class_data = []
    for student in students:
        student_marks = {}
        for subject in subjects:
            mark = Mark.query.filter_by(
                student_id=student.id,
                subject_id=subject.id,
                term_id=term_obj.id,
                assessment_type_id=assessment_type_obj.id
            ).first()
            student_marks[subject.id] = mark.mark if mark else ""
        class_data.append({
            'student_id': student.id,
            'student_name': student.name,
            'marks': student_marks
        })

    return render_template(
        "edit-class-report.html",
        class_data=class_data,
        grade=grade,
        stream=stream,
        term=term,
        assessment_type=assessment_type,
        subjects=subjects,
        current_date=datetime.now().strftime("%Y-%m-%d")
    )
