from io import BytesIO
import os
import zipfile
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
from flask import send_file
from app.models import Stream, Grade, Subject, Student, Mark, Term, AssessmentType
from app.utils.grading import get_performance_category, get_grade_and_points, get_performance_summary
from app.utils.constants import SUBJECT_ABBREVIATIONS

def generate_subject_pdf(grade, stream, subject):
    stream_obj = Stream.query.join(Grade).filter(Grade.level == grade, Stream.name == stream[-1]).first()
    subject_obj = Subject.query.filter_by(name=subject).first()
    if not (stream_obj and subject_obj):
        return None, "Invalid grade, stream, or subject", 404

    students = Student.query.filter_by(stream_id=stream_obj.id).all()
    marks_data = []
    total_marks = 0
    for student in students:
        mark = Mark.query.filter_by(student_id=student.id, subject_id=subject_obj.id).first()
        if mark:
            percentage = (mark.mark / mark.total_marks) * 100 if mark.total_marks > 0 else 0
            performance = get_performance_category(percentage)
            marks_data.append([student.name, mark.mark, round(percentage, 1), performance])
            total_marks = mark.total_marks

    if not marks_data:
        return None, "No data available for this report.", 404

    mean_score = sum(mark[1] for mark in marks_data) / len(marks_data) if marks_data else 0
    mean_percentage = (mean_score / total_marks) * 100 if total_marks > 0 else 0
    mean_performance = get_performance_category(mean_percentage)
    performance_summary = get_performance_summary(marks_data)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    heading3_style = styles['Heading3']

    elements.append(Paragraph("Kirima Primary School", title_style))
    elements.append(Paragraph(f"Grade {grade} Stream {stream} - {subject} Report", subtitle_style))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Mean Score: {mean_score:.2f} ({mean_percentage:.1f}%) - {mean_performance}", normal_style))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Performance Summary:", heading3_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"E.E: {performance_summary.get('E.E', 0)} students", normal_style))
    elements.append(Paragraph(f"M.E: {performance_summary.get('M.E', 0)} students", normal_style))
    elements.append(Paragraph(f"A.E: {performance_summary.get('A.E', 0)} students", normal_style))
    elements.append(Paragraph(f"B.E: {performance_summary.get('B.E', 0)} students", normal_style))
    elements.append(Spacer(1, 24))

    data = [["Student Name", "Marks", "Percentage (%)", "Performance Level"]]
    for student_record in marks_data:
        data.append([
            student_record[0],
            str(student_record[1]),
            f"{student_record[2]}%",
            student_record[3]
        ])
    
    table = Table(data)
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]

    for i, row in enumerate(data[1:], start=1):
        performance = row[3]
        if performance == "E.E":
            table_style.append(('BACKGROUND', (3, i), (3, i), colors.green))
        elif performance == "M.E":
            table_style.append(('BACKGROUND', (3, i), (3, i), colors.lightblue))
        elif performance == "A.E":
            table_style.append(('BACKGROUND', (3, i), (3, i), colors.yellow))
        else:
            table_style.append(('BACKGROUND', (3, i), (3, i), colors.pink))

    table.setStyle(TableStyle(table_style))
    elements.append(table)

    elements.append(Spacer(1, 20))
    footer_style = styles['Normal']
    footer_style.alignment = 1
    elements.append(Paragraph("Kirima Primary School powered by CbcTeachkit", footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer, None, 200

def generate_class_pdf(grade, stream, term, assessment_type):
    stream_obj = Stream.query.join(Grade).filter(Grade.level == grade, Stream.name == stream[-1]).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()
    
    if not (stream_obj and term_obj and assessment_type_obj):
        return None, "Invalid grade, stream, term, or assessment type", 404

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
        return None, "No data available for this report.", 404

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

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    heading3_style = styles['Heading3']

    abbreviated_subjects = [SUBJECT_ABBREVIATIONS.get(subject.name, subject.name[:4].upper()) for subject in subjects]

    title_style.alignment = 1
    subtitle_style.alignment = 1
    elements.append(Paragraph("KIRIMA PRIMARY SCHOOL", title_style))
    elements.append(Paragraph(f"GRADE {grade} - MARKSHEET: AVERAGE SCORE", subtitle_style))
    elements.append(Paragraph(f"STREAM: {stream}  TERM: {term.replace('_', ' ').upper()}  ASSESSMENT: {assessment_type.upper()}", subtitle_style))
    elements.append(Spacer(1, 12))

    headers = ["S/N", "STUDENT NAME"] + abbreviated_subjects + ["TOTAL", "AVG %", "GRD", "RANK"]
    data = [headers]
    for idx, student_data in enumerate(class_data, 1):
        row = [str(idx), student_data['student'].upper()]
        for subject in subjects:
            mark = student_data['marks'].get(subject.name, 0)
            row.append(str(int(mark)))
        total = student_data['total_marks']
        avg_percentage = student_data['average_percentage']
        grade = get_performance_category(avg_percentage)
        row.extend([str(int(total)), f"{avg_percentage:.0f}%", grade, str(student_data['rank'])])
        data.append(row)
    
    table = Table(data)
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]

    col_widths = [30, 150] + [40] * len(abbreviated_subjects) + [50, 50, 40, 40]
    table._argW = col_widths

    table.setStyle(TableStyle(table_style))
    elements.append(table)

    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Performance Summary:", heading3_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"E.E (Exceeding Expectation, ≥75%): {stats.get('exceeding', 0)} learners", normal_style))
    elements.append(Paragraph(f"M.E (Meeting Expectation, 50-74%): {stats.get('meeting', 0)} learners", normal_style))
    elements.append(Paragraph(f"A.E (Approaching Expectation, 30-49%): {stats.get('approaching', 0)} learners", normal_style))
    elements.append(Paragraph(f"B.E (Below Expectation, <30%): {stats.get('below', 0)} learners", normal_style))

    elements.append(Spacer(1, 20))
    footer_style = styles['Normal']
    footer_style.alignment = 1
    footer_style.fontSize = 8
    current_date = datetime.now().strftime("%Y-%m-%d")
    elements.append(Paragraph(f"Generated on: {current_date}", footer_style))
    elements.append(Paragraph("Kirima Primary School powered by CbcTeachkit", footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer, None, 200

def generate_individual_report_pdf(grade, stream, term, assessment_type, student_name, class_data, education_level, total_marks, subjects):
    stream_obj = Stream.query.join(Grade).filter(Grade.level == grade, Stream.name == stream[-1]).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()
    
    if not (stream_obj and term_obj and assessment_type_obj):
        return None

    student = Student.query.filter_by(name=student_name, stream_id=stream_obj.id).first()
    if not student:
        return None

    student_data = next((data for data in class_data if data['student'] == student_name), None)
    if not student_data:
        return None

    student_marks = student_data['marks']
    total = student_data['total_marks']
    avg_percentage = student_data['average_percentage']
    mean_grade, mean_points = get_grade_and_points(avg_percentage)
    total_possible_marks = len(subjects) * total_marks
    total_points = sum(get_grade_and_points(student_marks.get(subject, 0))[1] for subject in subjects)

    # Calculate class average percentage
    class_total_avg_percentage = sum(data['average_percentage'] for data in class_data) / len(class_data) if class_data else 0

    # Calculate subject averages across all students in the class
    subject_averages = {}
    for subject in subjects:
        subject_marks = [data['marks'].get(subject, 0) for data in class_data]
        subject_avg = sum(subject_marks) / len(subject_marks) if subject_marks else 0
        subject_averages[subject] = subject_avg

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    normal_style = styles['Normal']
    heading2_style = styles['Heading2']
    heading3_style = styles['Heading3']

    title_style.alignment = 1
    heading2_style.alignment = 1
    heading3_style.alignment = 1
    normal_style.fontSize = 10

    elements.append(Paragraph("KIRIMA PRIMARY SCHOOL", title_style))
    elements.append(Paragraph(f"STUDENT REPORT: {student_name.upper()}", heading2_style))
    elements.append(Paragraph(f"Grade: {grade} | Stream: {stream} | Term: {term.replace('_', ' ').title()} | Assessment: {assessment_type.title()}", heading3_style))
    elements.append(Spacer(1, 12))

    admission_no = f"HS{grade}{stream[-1]}{str(Student.query.filter_by(stream_id=stream_obj.id).all().index(student) + 1).zfill(3)}"
    elements.append(Paragraph(f"Admission No: {admission_no}", normal_style))
    elements.append(Spacer(1, 12))

    # Modified table to include subject averages
    data = [["SUBJECT", "ENTRANCE", "MID TERM", "END TERM", "AVG", "CLASS AVG", "REMARKS"]]
    for subject in subjects:
        mark = student_marks.get(subject, 0)
        avg = mark
        percentage = (mark / total_marks) * 100 if total_marks > 0 else 0
        performance = get_performance_category(percentage)
        subject_class_avg = subject_averages.get(subject, 0)
        data.append([subject.upper(), "", "", str(int(mark)), str(int(avg)), f"{int(subject_class_avg)}", performance])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Total Marks: {total} / {total_possible_marks}", normal_style))
    elements.append(Paragraph(f"Average Percentage: {avg_percentage:.0f}%", normal_style))
    elements.append(Paragraph(f"Class Average Percentage: {class_total_avg_percentage:.0f}%", normal_style))
    elements.append(Paragraph(f"Mean Grade: {mean_grade}", normal_style))
    elements.append(Paragraph(f"Total Points: {total_points}", normal_style))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Class Teacher's Comment: _____________________________", normal_style))
    elements.append(Paragraph(f"Headteacher's Comment: _____________________________", normal_style))
    elements.append(Spacer(1, 20))

    footer_style = styles['Normal']
    footer_style.alignment = 1
    footer_style.fontSize = 8
    current_date = datetime.now().strftime("%Y-%m-%d")
    elements.append(Paragraph(f"Generated on: {current_date}", footer_style))
    elements.append(Paragraph("Kirima Primary School powered by CbcTeachkit", footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_all_individual_reports_pdf(grade, stream, term, assessment_type):
    stream_obj = Stream.query.join(Grade).filter(Grade.level == grade, Stream.name == stream[-1]).first()
    term_obj = Term.query.filter_by(name=term).first()
    assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()
    
    if not (stream_obj and term_obj and assessment_type_obj):
        return None, "Invalid grade, stream, term, or assessment type", 404

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
        return None, "No student data available for this class.", 404

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for student_data in class_data:
            student_name = student_data['student']
            pdf_buffer = generate_individual_report_pdf(
                grade, stream, term, assessment_type, student_name,
                class_data, "", total_marks, [subject.name for subject in subjects]
            )
            if pdf_buffer:
                zip_file.writestr(
                    f"report_{student_name.replace(' ', '_')}.pdf",
                    pdf_buffer.getvalue()
                )

    zip_buffer.seek(0)
    return zip_buffer, None, 200