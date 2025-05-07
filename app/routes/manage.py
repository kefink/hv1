from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify, flash
from app.models import Grade, Stream, Subject, Student, Teacher, Term, AssessmentType, Mark
from app import db, cache  # Import cache from app package instead of flask_caching
from app.utils.constants import EDUCATIONAL_LEVELS, EDUCATIONAL_LEVEL_MAPPING
import pandas as pd
from io import StringIO

bp = Blueprint('manage', __name__)

@bp.route("/get_streams/<grade_id>", methods=["GET"])
@cache.cached(timeout=300)  # Cache the response for 5 minutes
def get_streams(grade_id):
    try:
        grade_id = int(grade_id)
        streams = Stream.query.filter_by(grade_id=grade_id).all()
        return jsonify({"streams": [{"id": stream.id, "name": stream.name} for stream in streams]})
    except ValueError:
        return jsonify({"streams": [], "error": "Invalid grade ID"}), 400

@bp.route("/manage_students", methods=["GET", "POST"])
def manage_students():
    if 'teacher_id' not in session or session['role'] != 'classteacher':
        return redirect(url_for('auth.classteacher_login'))

    error_message = None
    success_message = None
    selected_level = None

    selected_level = request.args.get('level') or request.form.get('educational_level') or request.form.get('redirect_level')

    if request.method == "POST":
        action = request.form.get('action')
        redirect_level = request.form.get('redirect_level') or selected_level

        if action == 'add_grade':
            grade_name = request.form.get('grade_name')
            educational_level = request.form.get('educational_level')
            if not educational_level:
                error_message = "Please select an educational level before adding a grade."
            elif grade_name:
                allowed_grades = EDUCATIONAL_LEVEL_MAPPING.get(educational_level, [])
                if grade_name not in allowed_grades:
                    error_message = f"Grade '{grade_name}' is not valid for {educational_level}. Valid grades are: {', '.join(allowed_grades)}."
                else:
                    existing_grade = Grade.query.filter_by(level=grade_name).first()
                    if existing_grade:
                        error_message = f"Grade '{grade_name}' already exists."
                    else:
                        new_grade = Grade(level=grade_name, education_level=educational_level)
                        db.session.add(new_grade)
                        db.session.commit()
                        success_message = f"Grade '{grade_name}' added successfully."
            else:
                error_message = "Grade name is required."

        elif action == 'add_stream':
            stream_name = request.form.get('stream_name')
            grade_id = request.form.get('grade_id')
            
            if stream_name and grade_id:
                # Check if the grade exists
                grade = Grade.query.get(grade_id)
                if not grade:
                    error_message = "Selected grade does not exist."
                else:
                    existing_stream = Stream.query.filter_by(name=stream_name, grade_id=grade_id).first()
                    if existing_stream:
                        error_message = f"Stream '{stream_name}' already exists for grade '{grade.level}'."
                    else:
                        new_stream = Stream(name=stream_name, grade_id=grade_id)
                        db.session.add(new_stream)
                        db.session.commit()
                        success_message = f"Stream '{stream_name}' added successfully to grade '{grade.level}'."
            else:
                error_message = "Stream name and grade are required."

        elif action == 'add_student':
            name = request.form.get('name')
            admission_number = request.form.get('admission_number')
            stream_id = request.form.get('stream') or None
            gender = request.form.get('gender')
            educational_level = request.form.get('educational_level')
            if not educational_level:
                error_message = "Please select an educational level before adding a student."
            elif not name:
                error_message = "Student name is required."
            elif not admission_number:
                error_message = "Admission number is required."
            elif not gender:
                error_message = "Gender is required."
            else:
                existing_student = Student.query.filter_by(admission_number=admission_number).first()
                if existing_student:
                    error_message = f"Admission number '{admission_number}' is already in use."
                else:
                    if stream_id:
                        existing_student = Student.query.filter_by(name=name, stream_id=stream_id).first()
                        if existing_student:
                            error_message = f"Student '{name}' already exists in this stream."
                        else:
                            new_student = Student(
                                name=name,
                                admission_number=admission_number,
                                stream_id=stream_id,
                                gender=gender.lower()
                            )
                            db.session.add(new_student)
                            db.session.commit()
                            success_message = f"Student '{name}' added successfully."
                    else:
                        existing_student = Student.query.filter_by(name=name, stream_id=None).first()
                        if existing_student:
                            error_message = f"Student '{name}' already exists with no stream."
                        else:
                            new_student = Student(
                                name=name,
                                admission_number=admission_number,
                                stream_id=None,
                                gender=gender.lower()
                            )
                            db.session.add(new_student)
                            db.session.commit()
                            success_message = f"Student '{name}' added successfully."

        elif action == 'bulk_upload_students':
            if 'student_file' not in request.files:
                error_message = "No file uploaded."
            else:
                file = request.files['student_file']
                if not (file.filename.endswith('.csv') or file.filename.endswith('.xlsx')):
                    error_message = "Only CSV and Excel (.xlsx) files are supported."
                else:
                    try:
                        if file.filename.endswith('.csv'):
                            stream = StringIO(file.stream.read().decode("utf-8"))
                            df = pd.read_csv(stream)
                        else:
                            df = pd.read_excel(file, engine='openpyxl')

                        required_columns = ['name', 'grade', 'admission_number', 'stream']
                        if not all(col in df.columns for col in required_columns):
                            error_message = "File must contain 'name', 'grade', 'admission_number', and 'stream' columns."
                        else:
                            educational_level = request.form.get('educational_level')
                            if not educational_level:
                                error_message = "Please select an educational level before uploading students."
                            else:
                                for index, row in df.iterrows():
                                    name = str(row['name']).strip()
                                    grade_name = str(row['grade']).strip()
                                    admission_number = str(row['admission_number']).strip()
                                    stream_name = str(row['stream']).strip()
                                    gender = str(row.get('gender', 'male')).strip().lower()

                                    if not all([name, grade_name, admission_number, stream_name]):
                                        error_message = f"Missing data in row {index + 2}."
                                        break

                                    allowed_grades = EDUCATIONAL_LEVEL_MAPPING.get(educational_level, [])
                                    if grade_name not in allowed_grades:
                                        error_message = f"Grade '{grade_name}' in row {index + 2} is not valid for {educational_level}."
                                        break

                                    grade = Grade.query.filter_by(level=grade_name, education_level=educational_level).first()
                                    if not grade:
                                        grade = Grade(level=grade_name, education_level=educational_level)
                                        db.session.add(grade)
                                        db.session.flush()  # Flush to get the grade ID

                                    stream = Stream.query.filter_by(name=stream_name, grade_id=grade.id).first()
                                    if not stream:
                                        stream = Stream(name=stream_name, grade_id=grade.id)
                                        db.session.add(stream)
                                        db.session.flush()  # Flush to get the stream ID

                                    existing_student = Student.query.filter_by(admission_number=admission_number).first()
                                    if existing_student:
                                        error_message = f"Admission number '{admission_number}' in row {index + 2} is already in use."
                                        break

                                    existing_student = Student.query.filter_by(name=name, stream_id=stream.id).first()
                                    if existing_student:
                                        error_message = f"Student '{name}' in row {index + 2} already exists in stream {stream_name}."
                                        break

                                    if gender not in ['male', 'female', 'm', 'f', 'boy', 'girl']:
                                        error_message = f"Invalid gender '{gender}' in row {index + 2}. Must be 'male', 'female', 'm', 'f', 'boy', or 'girl'."
                                        break

                                    new_student = Student(
                                        name=name,
                                        admission_number=admission_number,
                                        stream_id=stream.id,
                                        gender=gender
                                    )
                                    db.session.add(new_student)

                                if not error_message:
                                    db.session.commit()
                                    success_message = f"Successfully uploaded {len(df)} students."

                    except Exception as e:
                        db.session.rollback()
                        error_message = f"Error processing file: {str(e)}"

        elif action == 'delete_all':
            try:
                # First delete all marks to avoid foreign key constraint
                Mark.query.delete()
                # Then delete all students
                num_deleted = Student.query.delete()
                db.session.commit()
                success_message = f"Successfully deleted all {num_deleted} students."
            except Exception as e:
                db.session.rollback()
                error_message = f"Error deleting all students: {str(e)}"

        elif action == 'delete_selected':
            student_ids = request.form.getlist('student_ids')
            if not student_ids:
                error_message = "No students selected for deletion."
            else:
                try:
                    for student_id in student_ids:
                        student = Student.query.get(student_id)
                        if student:
                            Mark.query.filter_by(student_id=student.id).delete()
                            db.session.delete(student)
                    db.session.commit()
                    success_message = f"Successfully deleted {len(student_ids)} students."
                except Exception as e:
                    db.session.rollback()
                    error_message = f"Error deleting students: {str(e)}"

        if redirect_level and not error_message and not success_message:
            return redirect(url_for('manage.manage_students', level=redirect_level))

    grades = Grade.query.all()
    streams = Stream.query.all()
    # Use join to get student data with stream and grade information
    students = db.session.query(
        Student,
        Stream,
        Grade
    ).outerjoin(
        Stream, Student.stream_id == Stream.id
    ).outerjoin(
        Grade, Stream.grade_id == Grade.id
    ).all()

    # Serialize the data
    serialized_grades = [{
        'id': grade.id,
        'level': grade.level,
        'education_level': grade.education_level
    } for grade in grades]
    
    serialized_streams = [{
        'id': stream.id,
        'name': stream.name,
        'grade_id': stream.grade_id
    } for stream in streams]
    
    # Update the student serialization to include stream and grade info
    serialized_students = [{
        'id': student.id,
        'name': student.name,
        'admission_number': student.admission_number,
        'gender': student.gender,
        'stream_id': student.stream_id,
        'stream': {
            'id': stream.id if stream else None,
            'name': stream.name if stream else None,
            'grade': {
                'id': grade.id if grade else None,
                'level': grade.level if grade else None,
                'education_level': grade.education_level if grade else None
            } if grade else None
        } if stream else None
    } for student, stream, grade in students]

    return render_template(
        "manage_students.html",
        grades=serialized_grades,
        streams=serialized_streams,
        students=serialized_students,
        educational_levels=EDUCATIONAL_LEVELS,
        educational_level_mapping=EDUCATIONAL_LEVEL_MAPPING,
        error_message=error_message,
        success_message=success_message,
        selected_level=selected_level
    )

@bp.route("/manage_subjects", methods=["GET", "POST"])
def manage_subjects():
    if 'teacher_id' not in session or session['role'] != 'classteacher':
        return redirect(url_for('auth.classteacher_login'))

    print("\n=== DEBUG: Entering manage_subjects route ===")  # Debug
    print(f"Request method: {request.method}")  # Debug

    if request.method == "POST":
        action = request.form.get('action')
        print(f"Action: {action}")  # Debug
        print(f"Form data: {request.form}")  # Debug

        if action == 'add_subject':
            name = request.form.get('name')
            education_level = request.form.get('education_level')
            grade_level = request.form.get('grade_id')
            
            print(f"Adding subject - Name: {name}, Level: {education_level}, Grade: {grade_level}")  # Debug
            
            if not all([name, education_level, grade_level]):
                flash("All fields are required.", 'error')
                print("Validation failed: Missing required fields")  # Debug
            else:
                try:
                    # Check if the grade exists, if not create it
                    grade = Grade.query.filter_by(level=grade_level, education_level=education_level).first()
                    if not grade:
                        print("Creating new grade")  # Debug
                        try:
                            grade = Grade(level=grade_level, education_level=education_level)
                            db.session.add(grade)
                            db.session.flush()
                        except Exception as e:
                            db.session.rollback()
                            # Grade might have been created by another request, try to fetch it again
                            grade = Grade.query.filter_by(level=grade_level, education_level=education_level).first()
                            if not grade:
                                raise e
                    
                    # Check if subject already exists for this education level and grade
                    existing_subject = Subject.query.join(Subject.grade_levels).filter(
                        Subject.name == name,
                        Subject.education_level == education_level,
                        Grade.id == grade.id
                    ).first()
                    
                    if existing_subject:
                        msg = f"Subject '{name}' already exists for Grade {grade_level} in {education_level}."
                        print(f"Subject exists: {msg}")  # Debug
                        flash(msg, 'error')
                    else:
                        print("Creating new subject")  # Debug
                        new_subject = Subject(
                            name=name,
                            education_level=education_level,
                            abbreviation=name[:3].upper()
                        )
                        new_subject.grade_levels.append(grade)
                        db.session.add(new_subject)
                        db.session.commit()
                        msg = f"✅ Subject '{name}' has been successfully added for Grade {grade_level}."
                        print(msg)  # Debug
                        flash(msg, 'success')
                        return redirect(url_for('manage.manage_subjects'))
                except Exception as e:
                    db.session.rollback()
                    error_msg = f"❌ Error adding subject: {str(e)}"
                    print(error_msg)  # Debug
                    flash(error_msg, 'error')
                    import traceback
                    traceback.print_exc()  # Print full traceback
        elif action == 'delete_subject':
            subject_id = request.form.get('subject_id')
            if not subject_id:
                flash("❌ No subject selected for deletion.", 'error')
            else:
                try:
                    subject = Subject.query.get(subject_id)
                    if subject:
                        subject_name = subject.name
                        
                        # Delete any marks associated with this subject
                        from app.models import Mark
                        marks_deleted = Mark.query.filter_by(subject_id=subject_id).delete()
                        
                        # Now delete the subject
                        db.session.delete(subject)
                        db.session.commit()
                        
                        if marks_deleted > 0:
                            flash(
                                f"✅ Subject '{subject_name}' and its {marks_deleted} associated mark(s) have been successfully deleted.", 
                                'success'
                            )
                        else:
                            flash(f"✅ Subject '{subject_name}' has been successfully deleted.", 'success')
                            
                        return redirect(url_for('manage.manage_subjects'))
                    else:
                        flash("❌ Subject not found.", 'error')
                except Exception as e:
                    db.session.rollback()
                    flash(f"❌ Error deleting subject: {str(e)}", 'error')
                    
        elif action == 'bulk_delete':
            subject_ids = request.form.getlist('subject_ids')
            if not subject_ids:
                flash("❌ No subjects selected for deletion.", 'error')
            else:
                try:
                    from app.models import Mark
                    deleted_count = 0
                    marks_deleted = 0
                    
                    for subject_id in subject_ids:
                        subject = Subject.query.get(subject_id)
                        if subject:
                            # Delete associated marks
                            marks_count = Mark.query.filter_by(subject_id=subject_id).delete()
                            marks_deleted += marks_count
                            
                            # Delete the subject
                            db.session.delete(subject)
                            deleted_count += 1
                    
                    db.session.commit()
                    
                    if deleted_count > 0:
                        msg = f"✅ Successfully deleted {deleted_count} subject(s)"
                        if marks_deleted > 0:
                            msg += f" and {marks_deleted} associated mark(s)"
                        msg += "."
                        flash(msg, 'success')
                    else:
                        flash("❌ No subjects were deleted.", 'error')
                        
                except Exception as e:
                    db.session.rollback()
                    flash(f"❌ Error during bulk deletion: {str(e)}", 'error')
                
                return redirect(url_for('manage.manage_subjects'))

    # Get all subjects with their grades for display
    subjects = Subject.query.all()
    
    return render_template(
        "manage_subjects.html", 
        subjects=subjects,
        educational_levels=EDUCATIONAL_LEVELS,
        educational_level_mapping=EDUCATIONAL_LEVEL_MAPPING
    )

@bp.route("/manage_teachers", methods=["GET", "POST"])
def manage_teachers():
    if 'teacher_id' not in session or session['role'] != 'classteacher':
        return redirect(url_for('auth.classteacher_login'))

    error_message = None
    success_message = None

    if request.method == "POST":
        action = request.form.get('action')

        if action == 'add_teacher':
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')
            subject_ids = request.form.getlist('subjects')
            grade_id = request.form.get('grade')
            stream_id = request.form.get('stream')
            
            if not all([username, password, role]):
                error_message = "All fields are required."
            elif role not in ['headteacher', 'teacher', 'classteacher']:
                error_message = "Invalid role selected."
            else:
                existing_teacher = Teacher.query.filter_by(username=username).first()
                if existing_teacher:
                    error_message = f"Username '{username}' already exists."
                else:
                    try:
                        new_teacher = Teacher(username=username, role=role)
                        new_teacher.set_password(password)  # Hash the password
                        
                        # Assign stream if provided
                        if stream_id:
                            stream = Stream.query.get(stream_id)
                            if stream:
                                new_teacher.stream_id = stream.id
                        
                        # Add the teacher first to get an ID
                        db.session.add(new_teacher)
                        db.session.flush()
                        
                        # Associate selected subjects with the teacher
                        if subject_ids:
                            for subject_id in subject_ids:
                                subject = Subject.query.get(subject_id)
                                if subject:
                                    new_teacher.subjects.append(subject)
                        
                        db.session.commit()
                        success_message = f"Teacher '{username}' added successfully with {len(subject_ids)} subjects."
                    except Exception as e:
                        db.session.rollback()
                        error_message = f"Error adding teacher: {str(e)}"
        elif action == 'delete_selected':
            teacher_ids = request.form.getlist('teacher_ids')
            if not teacher_ids:
                error_message = "No teachers selected for deletion."
            else:
                try:
                    for teacher_id in teacher_ids:
                        teacher = Teacher.query.get(teacher_id)
                        if teacher:
                            db.session.delete(teacher)
                    db.session.commit()
                    success_message = f"Successfully deleted {len(teacher_ids)} teachers."
                except Exception as e:
                    db.session.rollback()
                    error_message = f"Error deleting teachers: {str(e)}"

    teachers = Teacher.query.all()
    return render_template(
        "manage_teachers.html",
        teachers=teachers,
        error_message=error_message,
        success_message=success_message
    )

@bp.route("/manage_grades_streams", methods=["GET", "POST"])
def manage_grades_streams():
    if 'teacher_id' not in session or session['role'] != 'classteacher':
        return redirect(url_for('auth.classteacher_login'))

    error_message = None
    success_message = None
    selected_level = request.args.get('level') or request.form.get('educational_level')

    if request.method == "POST":
        action = request.form.get('action')

        if action == 'add_grade':
            grade_name = request.form.get('grade_name')
            educational_level = request.form.get('educational_level')
            if not educational_level:
                error_message = "Please select an educational level before adding a grade."
            elif grade_name:
                allowed_grades = EDUCATIONAL_LEVEL_MAPPING.get(educational_level, [])
                if grade_name not in allowed_grades:
                    error_message = f"Grade '{grade_name}' is not valid for {educational_level}."
                else:
                    existing_grade = Grade.query.filter_by(level=grade_name).first()
                    if existing_grade:
                        error_message = f"Grade '{grade_name}' already exists."
                    else:
                        new_grade = Grade(level=grade_name, education_level=educational_level)
                        db.session.add(new_grade)
                        db.session.commit()
                        success_message = f"Grade '{grade_name}' added successfully."
            else:
                error_message = "Grade name is required."

        elif action == 'add_stream':
            stream_name = request.form.get('stream_name')
            grade_id = request.form.get('grade_id')
            
            if stream_name and grade_id:
                # Check if the grade exists
                grade = Grade.query.get(grade_id)
                if not grade:
                    error_message = "Selected grade does not exist."
                else:
                    existing_stream = Stream.query.filter_by(name=stream_name, grade_id=grade_id).first()
                    if existing_stream:
                        error_message = f"Stream '{stream_name}' already exists for grade '{grade.level}'."
                    else:
                        new_stream = Stream(name=stream_name, grade_id=grade_id)
                        db.session.add(new_stream)
                        db.session.commit()
                        success_message = f"Stream '{stream_name}' added successfully to grade '{grade.level}'."
            else:
                error_message = "Stream name and grade are required."

        elif action == 'delete_grade':
            grade_id = request.form.get('grade_id')
            grade = Grade.query.get(grade_id)
            if grade:
                streams = Stream.query.filter_by(grade_id=grade.id).all()
                for stream in streams:
                    students = Student.query.filter_by(stream_id=stream.id).all()
                    for student in students:
                        Mark.query.filter_by(student_id=student.id).delete()
                        db.session.delete(student)
                    db.session.delete(stream)
                db.session.delete(grade)
                db.session.commit()
                success_message = f"Grade '{grade.level}' and associated streams/students deleted successfully."
            else:
                error_message = "Grade not found."

        elif action == 'delete_stream':
            stream_id = request.form.get('stream_id')
            stream = Stream.query.get(stream_id)
            if stream:
                students = Student.query.filter_by(stream_id=stream.id).all()
                for student in students:
                    Mark.query.filter_by(student_id=student.id).delete()
                    db.session.delete(student)
                db.session.delete(stream)
                db.session.commit()
                success_message = f"Stream '{stream.name}' and associated students deleted successfully."
            else:
                error_message = "Stream not found."

    grades = Grade.query.all()
    streams = Stream.query.all()
    return render_template(
        "manage_grades_streams.html",
        grades=grades,
        streams=streams,
        educational_levels=EDUCATIONAL_LEVELS,
        educational_level_mapping=EDUCATIONAL_LEVEL_MAPPING,
        error_message=error_message,
        success_message=success_message,
        selected_level=selected_level
    )

@bp.route("/manage_terms_assessments", methods=["GET", "POST"])
def manage_terms_assessments():
    if 'teacher_id' not in session or session['role'] != 'classteacher':
        return redirect(url_for('auth.classteacher_login'))

    error_message = None
    success_message = None

    if request.method == "POST":
        action = request.form.get('action')

        if action == 'add_term':
            name = request.form.get('term_name')
            if not name:
                error_message = "Term name is required."
            else:
                existing_term = Term.query.filter_by(name=name).first()
                if existing_term:
                    error_message = f"Term '{name}' already exists."
                else:
                    new_term = Term(name=name)
                    db.session.add(new_term)
                    db.session.commit()
                    success_message = f"Term '{name}' added successfully."

        elif action == 'add_assessment':
            name = request.form.get('assessment_name')
            if not name:
                error_message = "Assessment type name is required."
            else:
                existing_assessment = AssessmentType.query.filter_by(name=name).first()
                if existing_assessment:
                    error_message = f"Assessment type '{name}' already exists."
                else:
                    new_assessment = AssessmentType(name=name)
                    db.session.add(new_assessment)
                    db.session.commit()
                    success_message = f"Assessment type '{name}' added successfully."

        elif action == 'delete_term':
            term_id = request.form.get('term_id')
            term = Term.query.get(term_id)
            if term:
                Mark.query.filter_by(term_id=term.id).delete()
                db.session.delete(term)
                db.session.commit()
                success_message = f"Term '{term.name}' deleted successfully."
            else:
                error_message = "Term not found."

        elif action == 'delete_assessment':
            assessment_id = request.form.get('assessment_id')
            assessment = AssessmentType.query.get(assessment_id)
            if assessment:
                Mark.query.filter_by(assessment_type_id=assessment.id).delete()
                db.session.delete(assessment)
                db.session.commit()
                success_message = f"Assessment type '{assessment.name}' deleted successfully."
            else:
                error_message = "Assessment type not found."

    terms = Term.query.all()
    assessments = AssessmentType.query.all()
    return render_template(
        "manage_terms_assessments.html",
        terms=terms,
        assessments=assessments,
        error_message=error_message,
        success_message=success_message
    )