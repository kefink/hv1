from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from flask_login import login_required, current_user
from app.models import Grade, Stream, Subject, Mark, Student, Term, AssessmentType
from app import db
from flask_paginate import Pagination, get_page_args
from datetime import datetime

bp = Blueprint('teacher', __name__)

@bp.route("/teacher", methods=["GET", "POST"])
@login_required
def teacher():
    if current_user.role != 'teacher':
        return redirect(url_for('auth.teacher_login'))

    grades = [grade.level for grade in Grade.query.all()]
    streams = Stream.query.all()
    subjects = [subject.name for subject in Subject.query.all()]
    terms = [term.name for term in Term.query.all()]
    assessment_types = [assessment_type.name for assessment_type in AssessmentType.query.all()]
    show_students = False
    students = []
    subject = ""
    grade = ""
    stream = ""
    term = ""
    assessment_type = ""
    total_marks = 0
    show_download_button = False

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
        subject = request.form.get("subject", "")
        grade = request.form.get("grade", "")
        stream = request.form.get("stream", "")
        term = request.form.get("term", "")
        assessment_type = request.form.get("assessment_type", "")
        try:
            total_marks = int(request.form.get("total_marks", 0))
        except ValueError:
            total_marks = 0

        if "upload_marks" in request.form:
            if not all([subject, grade, stream, term, assessment_type, total_marks > 0]):
                flash("Please fill in all fields before uploading marks", "error")
            else:
                stream_obj = Stream.query.join(Grade).filter(Grade.level == grade, Stream.name == stream).first()
                if stream_obj:
                    students = [student.name for student in Student.query.filter_by(stream_id=stream_obj.id).all()]
                    show_students = True
                    if not students:
                        flash(f"No students found for Grade {grade} Stream {stream}", "error")
                        show_students = False
                else:
                    flash(f"Invalid Grade {grade} or Stream {stream}", "error")

        elif "submit_marks" in request.form:
            if not all([subject, grade, stream, term, assessment_type, total_marks > 0]):
                flash("Please fill in all fields before submitting marks", "error")
            else:
                stream_obj = Stream.query.join(Grade).filter(Grade.level == grade, Stream.name == stream).first()
                subject_obj = Subject.query.filter_by(name=subject).first()
                term_obj = Term.query.filter_by(name=term).first()
                assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

                if not (stream_obj and subject_obj and term_obj and assessment_type_obj):
                    flash("Invalid selection for grade, stream, subject, term, or assessment type", "error")
                else:
                    students = Student.query.filter_by(stream_id=stream_obj.id).all()
                    any_marks_submitted = False

                    for student in students:
                        mark_key = f"mark_{student.name.replace(' ', '_')}"
                        mark_value = request.form.get(mark_key, '')
                        if mark_value and mark_value.replace('.', '').isdigit():
                            mark = float(mark_value)
                            if 0 <= mark <= total_marks:
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
                                flash(f"Invalid mark for {student.name}. Must be between 0 and {total_marks}.", "error")
                                break
                        else:
                            flash(f"Missing or invalid mark for {student.name}", "error")
                            break

                    if any_marks_submitted and not get_flashed_messages(with_categories=True):
                        db.session.commit()
                        flash("Marks submitted successfully!", "success")
                        show_download_button = True

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

    return render_template(
        "teacher.html",
        grades=grades,
        streams=streams,
        subjects=subjects,
        terms=terms,
        assessment_types=assessment_types,
        students=students,
        subject=subject,
        grade=grade,
        stream=stream,
        term=term,
        assessment_type=assessment_type,
        total_marks=total_marks,
        show_students=show_students,
        show_download_button=show_download_button,
        recent_reports=recent_reports_paginated,
        pagination=pagination
    )

@bp.route('/get_streams/<grade_id>')
@login_required
def get_streams(grade_id):
    if current_user.role != 'teacher':
        return jsonify({"error": "Unauthorized access"}), 401

    try:
        streams = Stream.query.filter_by(grade_id=grade_id).all()
        return jsonify({"streams": [{"name": stream.name} for stream in streams]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/edit_subject_report/<grade>/<stream>/<term>/<assessment_type>/<subject>", methods=["GET", "POST"])
@login_required
def edit_subject_report(grade, stream, term, assessment_type, subject):
    if current_user.role != 'teacher':
        return redirect(url_for('auth.teacher_login'))

    stream_obj = Stream.query.join(Grade).filter(Grade.level == grade, Stream.name == stream).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()
    subject_obj = Subject.query.filter_by(name=subject).first()

    if not (stream_obj and term_obj and assessment_type_obj and subject_obj):
        flash("Invalid grade, stream, term, assessment type, or subject", "error")
        return redirect(url_for('teacher'))

    students = Student.query.filter_by(stream_id=stream_obj.id).all()

    if request.method == "POST":
        try:
            for student in students:
                mark_key = f"mark_{student.id}_{subject_obj.id}"
                mark_value = request.form.get(mark_key)
                if mark_value and mark_value.replace('.', '').isdigit():
                    mark_value = float(mark_value)
                    mark = Mark.query.filter_by(
                        student_id=student.id,
                        subject_id=subject_obj.id,
                        term_id=term_obj.id,
                        assessment_type_id=assessment_type_obj.id
                    ).first()
                    if mark:
                        mark.mark = mark_value
                    else:
                        new_mark = Mark(
                            student_id=student.id,
                            subject_id=subject_obj.id,
                            term_id=term_obj.id,
                            assessment_type_id=assessment_type_obj.id,
                            mark=mark_value,
                            total_marks=mark.total_marks if mark else 100  # Use existing total_marks if available
                        )
                        db.session.add(new_mark)
            db.session.commit()
            flash("Marks updated successfully", "success")
            return redirect(url_for('teacher.edit_subject_report', grade=grade, stream=stream, term=term, assessment_type=assessment_type, subject=subject))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating marks: {str(e)}", "error")

    class_data = []
    for student in students:
        mark = Mark.query.filter_by(
            student_id=student.id,
            subject_id=subject_obj.id,
            term_id=term_obj.id,
            assessment_type_id=assessment_type_obj.id
        ).first()
        class_data.append({
            'student_id': student.id,
            'student_name': student.name,
            'mark': mark.mark if mark else "",
            'total_marks': mark.total_marks if mark else 100
        })

    return render_template(
        "edit_subject_report.html",
        class_data=class_data,
        grade=grade,
        stream=stream,
        term=term,
        assessment_type=assessment_type,
        subject=subject
    )

@bp.route("/preview_subject_report/<grade>/<stream>/<term>/<assessment_type>/<subject>")
@login_required
def preview_subject_report(grade, stream, term, assessment_type, subject):
    if current_user.role != 'teacher':
        return redirect(url_for('auth.teacher_login'))

    stream_obj = Stream.query.join(Grade).filter(Grade.level == grade, Stream.name == stream).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()
    subject_obj = Subject.query.filter_by(name=subject).first()

    if not (stream_obj and term_obj and assessment_type_obj and subject_obj):
        flash("Invalid grade, stream, term, assessment type, or subject", "error")
        return redirect(url_for('teacher'))

    students = Student.query.filter_by(stream_id=stream_obj.id).all()
    class_data = []
    total_marks = 0

    for student in students:
        mark = Mark.query.filter_by(
            student_id=student.id,
            subject_id=subject_obj.id,
            term_id=term_obj.id,
            assessment_type_id=assessment_type_obj.id
        ).first()
        if mark:
            total_marks = mark.total_marks
            percentage = (mark.mark / total_marks) * 100 if total_marks > 0 else 0
            class_data.append({
                'student_name': student.name,
                'mark': mark.mark,
                'percentage': round(percentage, 1)
            })

    if not class_data:
        flash("No marks found for the selected criteria", "error")
        return redirect(url_for('teacher'))

    class_data.sort(key=lambda x: x['mark'], reverse=True)
    for idx, student_data in enumerate(class_data, 1):
        student_data['rank'] = idx

    current_date = datetime.now().strftime('%Y-%m-%d')

    # Compute performance stats
    stats = {'exceeding': 0, 'meeting': 0, 'approaching': 0, 'below': 0}
    for data in class_data:
        if data['percentage'] >= 75:
            stats['exceeding'] += 1
        elif data['percentage'] >= 50:
            stats['meeting'] += 1
        elif data['percentage'] >= 30:
            stats['approaching'] += 1
        else:
            stats['below'] += 1

    return render_template(
        "preview_subject_report.html",
        class_data=class_data,
        grade=grade,
        stream=stream,
        term=term,
        assessment_type=assessment_type,
        subject=subject,
        total_marks=total_marks,
        current_date=current_date,
        stats=stats
    )

@bp.route("/preview_class_report/<grade>/<stream>/<term>/<assessment_type>")
@login_required
def preview_class_report(grade, stream, term, assessment_type):
    if current_user.role != 'teacher':
        return redirect(url_for('auth.teacher_login'))

    stream_obj = Stream.query.join(Grade).filter(Grade.level == grade, Stream.name == stream).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

    if not (stream_obj and term_obj and assessment_type_obj):
        flash("Invalid grade, stream, term, or assessment type", "error")
        return redirect(url_for('teacher'))

    students = Student.query.filter_by(stream_id=stream_obj.id).all()
    subjects = [subject.name for subject in Subject.query.all()]
    abbreviated_subjects = [subject.name[:3].upper() for subject in Subject.query.all()]  # Fallback abbreviation
    education_level = Grade.query.filter_by(level=grade).first().education_level  # Assuming Grade has an education_level field

    class_data = []
    for idx, student in enumerate(students, 1):
        marks = {}
        total_marks = 0
        mark_count = 0

        for subject in subjects:
            subject_obj = Subject.query.filter_by(name=subject).first()
            mark = Mark.query.filter_by(
                student_id=student.id,
                subject_id=subject_obj.id,
                term_id=term_obj.id,
                assessment_type_id=assessment_type_obj.id
            ).first()
            marks[subject] = mark.mark if mark else 0
            if mark:
                total_marks += mark.mark
                mark_count += 1

        average_percentage = (total_marks / (mark_count * 100) * 100) if mark_count > 0 else 0
        performance_category = "E.E" if average_percentage >= 75 else "M.E" if average_percentage >= 50 else "A.E" if average_percentage >= 30 else "B.E"

        class_data.append({
            'index': idx,
            'student': student.name,
            'marks': marks,
            'total_marks': total_marks,
            'average_percentage': average_percentage,
            'performance_category': performance_category,
            'rank': idx  # Placeholder; sort by average_percentage later
        })

    # Sort by average_percentage and reassign ranks
    class_data.sort(key=lambda x: x['average_percentage'], reverse=True)
    for idx, data in enumerate(class_data, 1):
        data['rank'] = idx

    # Compute performance stats
    stats = {'exceeding': 0, 'meeting': 0, 'approaching': 0, 'below': 0}
    for data in class_data:
        if data['average_percentage'] >= 75:
            stats['exceeding'] += 1
        elif data['average_percentage'] >= 50:
            stats['meeting'] += 1
        elif data['average_percentage'] >= 30:
            stats['approaching'] += 1
        else:
            stats['below'] += 1

    current_date = datetime.now().strftime('%Y-%m-%d')

    return render_template(
        "preview_class_report.html",
        class_data=class_data,
        subjects=subjects,
        abbreviated_subjects=abbreviated_subjects,
        grade=grade,
        stream=stream,
        term=term,
        assessment_type=assessment_type,
        education_level=education_level,
        stats=stats,
        current_date=current_date
    )

@bp.route("/preview_grade_marksheet/<grade>/<term>/<assessment_type>")
@login_required
def preview_grade_marksheet(grade, term, assessment_type):
    if current_user.role != 'teacher':
        return redirect(url_for('auth.teacher_login'))

    grade_obj = Grade.query.filter_by(level=grade).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

    if not (grade_obj and term_obj and assessment_type_obj):
        flash("Invalid grade, term, or assessment type", "error")
        return redirect(url_for('teacher'))

    streams = Stream.query.filter_by(grade_id=grade_obj.id).all()
    subjects = [subject.name for subject in Subject.query.all()]
    total_marks = {}

    # Collect total marks per subject (assuming it may vary per subject)
    for subject in subjects:
        subject_obj = Subject.query.filter_by(name=subject).first()
        mark = Mark.query.filter_by(
            subject_id=subject_obj.id,
            term_id=term_obj.id,
            assessment_type_id=assessment_type_obj.id
        ).first()
        total_marks[subject] = mark.total_marks if mark else 100  # Default to 100 if not found

    students_data = []
    all_students = []
    for stream in streams:
        students = Student.query.filter_by(stream_id=stream.id).all()
        for student in students:
            marks = {}
            student_total_marks = 0
            mark_count = 0

            for subject in subjects:
                subject_obj = Subject.query.filter_by(name=subject).first()
                mark = Mark.query.filter_by(
                    student_id=student.id,
                    subject_id=subject_obj.id,
                    term_id=term_obj.id,
                    assessment_type_id=assessment_type_obj.id
                ).first()
                marks[subject] = mark.mark if mark else 0
                if mark:
                    student_total_marks += mark.mark
                    mark_count += 1

            average_percentage = (student_total_marks / (mark_count * 100) * 100) if mark_count > 0 else 0
            all_students.append({
                'stream': stream.name,
                'student': student.name,
                'marks': marks,
                'total_marks': student_total_marks,
                'average_percentage': average_percentage
            })

    # Sort by average_percentage and assign ranks
    all_students.sort(key=lambda x: x['average_percentage'], reverse=True)
    for idx, student_data in enumerate(all_students, 1):
        student_data['rank'] = idx
        students_data.append(student_data)

    # Compute performance stats
    stats = {'exceeding': 0, 'meeting': 0, 'approaching': 0, 'below': 0}
    for data in students_data:
        if data['average_percentage'] >= 75:
            stats['exceeding'] += 1
        elif data['average_percentage'] >= 50:
            stats['meeting'] += 1
        elif data['average_percentage'] >= 30:
            stats['approaching'] += 1
        else:
            stats['below'] += 1

    return render_template(
        "preview_grade_marksheet.html",
        grade=grade,
        term=term,
        assessment_type=assessment_type,
        stats=stats,
        subjects=subjects,
        total_marks=total_marks,
        students_data=students_data
    )

@bp.route("/download_grade_marksheet/<grade>/<term>/<assessment_type>")
@login_required
def download_grade_marksheet(grade, term, assessment_type):
    if current_user.role != 'teacher':
        return redirect(url_for('auth.teacher_login'))

    # Placeholder for PDF generation logic
    flash("PDF download functionality is not yet implemented", "error")
    return redirect(url_for('teacher.preview_grade_marksheet', grade=grade, term=term, assessment_type=assessment_type))