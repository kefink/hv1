from app.models import Student, Teacher, Stream, Mark, Grade
from app.utils.grading import get_performance_category, get_grade_and_points

def calculate_school_stats():
    total_students = Student.query.count()
    total_teachers = Teacher.query.count()
    total_classes = Stream.query.count()

    marks = Mark.query.all()
    if marks:
        total_marks = sum(mark.mark for mark in marks if mark.mark is not None)
        count_marks = len([mark for mark in marks if mark.mark is not None])
        avg_performance = round(total_marks / count_marks, 2) if count_marks > 0 else 0
    else:
        avg_performance = 0

    top_class = "N/A"
    top_class_score = 0
    stream_performances = {}
    for stream in Stream.query.all():
        stream_marks = Mark.query.join(Student, Mark.student_id == Student.id).filter(Student.stream_id == stream.id).all()
        if stream_marks:
            stream_avg = round(sum(mark.mark for mark in stream_marks) / len(stream_marks), 2)
            stream_name = f"{stream.grade.level} {stream.name}" if stream.grade else stream.name
            stream_performances[stream_name] = stream_avg
    if stream_performances:
        top_class = max(stream_performances, key=stream_performances.get)
        top_class_score = stream_performances[top_class]

    least_performing_grade = "N/A"
    least_grade_score = 0
    grade_performances = {}
    for grade in Grade.query.all():
        grade_marks = Mark.query.join(Student, Mark.student_id == Student.id).join(Stream, Student.stream_id == Stream.id).filter(Stream.grade_id == grade.id).all()
        if grade_marks:
            grade_avg = round(sum(mark.mark for mark in grade_marks) / len(grade_marks), 2)
            grade_performances[grade.level] = grade_avg
    if grade_performances:
        least_performing_grade = min(grade_performances, key=grade_performances.get)
        least_grade_score = grade_performances[least_performing_grade]  # Corrected here

    learners_per_grade = {}
    gender_per_grade = {}
    streams_per_grade = {}

    students = Student.query.all()
    for student in students:
        grade = student.stream.grade.level if student.stream and student.stream.grade else "No Grade"
        stream_name = student.stream.name if student.stream else "No Stream"

        if grade not in learners_per_grade:
            learners_per_grade[grade] = 0
            gender_per_grade[grade] = {'Male': 0, 'Female': 0}
            streams_per_grade[grade] = {}

        if stream_name not in streams_per_grade[grade]:
            streams_per_grade[grade][stream_name] = {'total': 0, 'Male': 0, 'Female': 0}

        learners_per_grade[grade] += 1
        streams_per_grade[grade][stream_name]['total'] += 1

        gender = student.gender.strip() if student.gender else None
        if gender:
            gender_lower = gender.lower()
            if gender_lower in ['male', 'm', 'boy']:
                gender_per_grade[grade]['Male'] += 1
                streams_per_grade[grade][stream_name]['Male'] += 1
            elif gender_lower in ['female', 'f', 'girl']:
                gender_per_grade[grade]['Female'] += 1
                streams_per_grade[grade][stream_name]['Female'] += 1

    learners_per_grade = dict(sorted(learners_per_grade.items()))
    gender_per_grade = dict(sorted(gender_per_grade.items()))
    streams_per_grade = {grade: dict(sorted(streams.items())) for grade, streams in sorted(streams_per_grade.items())}

    return {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'avg_performance': avg_performance,
        'top_class': top_class,
        'top_class_score': top_class_score,
        'least_performing_grade': least_performing_grade,
        'least_grade_score': least_grade_score,
        'learners_per_grade': learners_per_grade,
        'gender_per_grade': gender_per_grade,
        'streams_per_grade': streams_per_grade
    }

def get_performance_data():
    performance_data = []
    for grade in Grade.query.all():
        for stream in Stream.query.filter_by(grade_id=grade.id).all():
            stream_marks = Mark.query.join(Student, Mark.student_id == Student.id).filter(Student.stream_id == stream.id).all()
            if not stream_marks:
                continue

            marks_by_term_assessment = {}
            for mark in stream_marks:
                term_name = mark.term.name if mark.term else "Unknown Term"
                assessment_type_name = mark.assessment_type.name if mark.assessment_type else "Unknown Assessment"
                key = (term_name, assessment_type_name)
                if key not in marks_by_term_assessment:
                    marks_by_term_assessment[key] = []
                marks_by_term_assessment[key].append(mark)

            for (term_name, assessment_type_name), marks in marks_by_term_assessment.items():
                marks_by_student = {}
                for mark in marks:
                    student_id = mark.student_id
                    if student_id not in marks_by_student:
                        marks_by_student[student_id] = []
                    marks_by_student[student_id].append(mark)

                performance_counts = {'E.E': 0, 'M.E': 0, 'A.E': 0, 'B.E': 0}
                total_percentage = 0
                student_count = 0

                for student_id, student_marks in marks_by_student.items():
                    student_total_percentage = 0
                    mark_count = 0
                    for mark in student_marks:
                        if mark.mark is not None and mark.total_marks > 0:
                            percentage = (mark.mark / mark.total_marks) * 100
                            student_total_percentage += percentage
                            mark_count += 1
                    if mark_count > 0:
                        student_avg_percentage = student_total_percentage / mark_count
                        category = get_performance_category(student_avg_percentage)
                        performance_counts[category] += 1
                        total_percentage += student_avg_percentage
                        student_count += 1

                mean_percentage = round(total_percentage / student_count, 2) if student_count > 0 else 0
                performance_category = get_performance_category(mean_percentage)

                performance_data.append({
                    'grade': grade.level,
                    'stream': stream.name,
                    'term': term_name,
                    'assessment_type': assessment_type_name,
                    'mean_percentage': mean_percentage,
                    'performance_category': performance_category,
                    'performance_counts': performance_counts
                })
    
    return performance_data
