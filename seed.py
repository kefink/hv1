# seed.py
from app import create_app, db
from app.models import Teacher, Grade, Stream, Student, Subject, Term, AssessmentType, Mark
from werkzeug.security import generate_password_hash

app = create_app()  # Create the app instance

with app.app_context():
    # Clear existing data
    db.drop_all()
    db.create_all()

    # Add Teachers with Hashed Passwords
    teachers = [
        Teacher(username="teacher1", role="teacher"),
        Teacher(username="headteacher", role="headteacher"),
        Teacher(username="classteacher1", role="classteacher")
    ]
    for teacher in teachers:
        if teacher.username == "teacher1":
            teacher.set_password("pass123")  # Hash the password
        elif teacher.username == "headteacher":
            teacher.set_password("admin123")  # Hash the password
        elif teacher.username == "classteacher1":
            teacher.set_password("class123")  # Hash the password
    db.session.add_all(teachers)

    # Add Grades (1 to 8, with education_level)
    grades = [
        Grade(level=str(i), education_level="Primary" if i <= 6 else "Junior Secondary") for i in range(1, 9)
    ]
    db.session.add_all(grades)
    db.session.commit()

    # Add Streams
    streams_data = {}
    stream_names = ["B", "G", "Y"]
    for grade in grades:
        streams = []
        for stream_name in stream_names:
            stream = Stream(name=stream_name, grade_id=grade.id)
            streams.append(stream)
        streams_data[grade.level] = streams
        db.session.add_all(streams)
    db.session.commit()

    # Add Students (Grades 1 to 8, with admission_number and gender)
    students_data = {
        "1": {
            "B": [(f"Student {i} Grade 1B", f"A00{i:03d}", "Male" if i % 2 == 0 else "Female") for i in range(1, 16)],
            "G": [(f"Student {i} Grade 1G", f"A01{i:03d}", "Male" if i % 2 == 0 else "Female") for i in range(1, 16)],
            "Y": [(f"Student {i} Grade 1Y", f"A02{i:03d}", "Male" if i % 2 == 0 else "Female") for i in range(1, 16)]
        },
        "2": {
            "B": [(f"Student {i} Grade 2B", f"A03{i:03d}", "Male" if i % 2 == 0 else "Female") for i in range(1, 16)],
            "G": [(f"Student {i} Grade 2G", f"A04{i:03d}", "Male" if i % 2 == 0 else "Female") for i in range(1, 16)],
            "Y": [(f"Student {i} Grade 2Y", f"A05{i:03d}", "Male" if i % 2 == 0 else "Female") for i in range(1, 16)]
        },
        "3": {
            "B": [(f"Student {i} Grade 3B", f"A06{i:03d}", "Male" if i % 2 == 0 else "Female") for i in range(1, 16)],
            "G": [(f"Student {i} Grade 3G", f"A07{i:03d}", "Male" if i % 2 == 0 else "Female") for i in range(1, 16)],
            "Y": [(f"Student {i} Grade 3Y", f"A08{i:03d}", "Male" if i % 2 == 0 else "Female") for i in range(1, 16)]
        },
        "4": {
            "B": [(f"Student {i} Grade 4B", f"A09{i:03d}", "Male" if i % 2 == 0 else "Female") for i in range(1, 16)],
            "G": [(f"Student {i} Grade 4G", f"A10{i:03d}", "Male" if i % 2 == 0 else "Female") for i in range(1, 16)],
            "Y": [(f"Student {i} Grade 4Y", f"A11{i:03d}", "Male" if i % 2 == 0 else "Female") for i in range(1, 16)]
        },
        "5": {
            "B": [(f"Student {i} Grade 5B", f"A12{i:03d}", "Male" if i % 2 == 0 else "Female") for i in range(1, 16)],
            "G": [(f"Student {i} Grade 5G", f"A13{i:03d}", "Male" if i % 2 == 0 else "Female") for i in range(1, 16)],
            "Y": [(f"Student {i} Grade 5Y", f"A14{i:03d}", "Male" if i % 2 == 0 else "Female") for i in range(1, 16)]
        },
        "6": {
            "B": [(f"Student {i} Grade 6B", f"A15{i:03d}", "Male" if i % 2 == 0 else "Female") for i in range(1, 16)],
            "G": [(f"Student {i} Grade 6G", f"A16{i:03d}", "Male" if i % 2 == 0 else "Female") for i in range(1, 16)],
            "Y": [(f"Student {i} Grade 6Y", f"A17{i:03d}", "Male" if i % 2 == 0 else "Female") for i in range(1, 16)]
        },
        "7": {
            "B": [(f"Student {i} Grade 7B", f"A18{i:03d}", "Male" if i % 2 == 0 else "Female") for i in range(1, 16)],
            "G": [(f"Student {i} Grade 7G", f"A19{i:03d}", "Male" if i % 2 == 0 else "Female") for i in range(1, 16)],
            "Y": [(f"Student {i} Grade 7Y", f"A20{i:03d}", "Male" if i % 2 == 0 else "Female") for i in range(1, 16)]
        },
        "8": {
            "B": [("ALVIN BLESSED .", "A21", "Male"), ("ALVIN NGANGA WANJIKU", "A22", "Male"), ("AMARA SAU MGHANGA", "A23", "Female"),
                  ("CASEY RAPHAELA OWUOR", "A24", "Female"), ("CECILINE MBOO KANURI", "A25", "Female"),
                  ("CELLINE MUTHONI GITHIEYA", "A26", "Female"), ("CLAIRE NJERI GIKONYO", "A27", "Female"),
                  ("DIDUMO OJUAK OKELLO", "A28", "Male"), ("ETHAN MWANGI KINYUA", "A29", "Male"),
                  ("FAITH WANGECHI KAGIRI", "A30", "Female"), ("GIBSON NGARI MUNENE", "A31", "Male"),
                  ("GOY PETER MAJOK", "A32", "Male"), ("HARVEY MUGO MACHARIA", "A33", "Male"),
                  ("JAMILA KANIRI NTOITI", "A34", "Female"), ("JAYDEN NJAGI MUNGA", "A35", "Male")],
            "G": [("BRIDGETTE WAIRIMU MUTONGA", "A36", "Female"), ("BRYTON KOSGEI KISANG", "A37", "Male"),
                  ("CALEB MUTIE MUTEMI", "A38", "Male"), ("CASTROL CHERUIYOT KORIR", "A39", "Male"),
                  ("DELANE MAKORI MOREMA", "A40", "Male"), ("FAITH WANGARI WAMBUGU", "A41", "Female"),
                  ("FAITH WANJIKU KINYUA", "A42", "Female"), ("FRANKLIN MURIUKI MWANGI", "A43", "Male"),
                  ("HABIB MUMO MWENDWA", "A44", "Male"), ("IVY WAMBUI GICHOBI", "A45", "Female"),
                  ("JAMES MATHINA GITHUA", "A46", "Male"), ("JAYDEN KIMATHI KOOME", "A47", "Male"),
                  ("JOY GILGER KENDI NYAGA", "A48", "Female"), ("KRISTA KENDI MURIITHI", "A49", "Female"),
                  ("LUCY WANJIRU NDUNGU", "A50", "Female")],
            "Y": [("ABBY TATYANA MUKABI", "A51", "Female"), ("ADRIAN MBAU MWANGI", "A52", "Male"),
                  ("ALISHA WANJIKU NJUBI", "A53", "Female"), ("ALVIN NDORO WAIRAGU", "A54", "Male"),
                  ("ALVIN OWEIN MBUGUA", "A55", "Male"), ("ANGELA NYAKIO MUNENE", "A56", "Female"),
                  ("ASHLYN WAYUA JULIA", "A57", "Female"), ("BAKHITA WANGECHI GACHOKA", "A58", "Female"),
                  ("BIANCA WAMBUI NJERI", "A59", "Female"), ("BIANKA ANON MULUAL", "A60", "Female"),
                  ("CARL KINYUA IKE", "A61", "Male"), ("CHERISE NJOKI WAIRAGU", "A62", "Female"),
                  ("CHRISTINE WANGECHI MAINA", "A63", "Female"), ("CHRISTINE WANJA NJERU", "A64", "Female"),
                  ("DANIELLA NYAMBURA MWANGI", "A65", "Female")]
        }
    }

    for grade_level, streams in students_data.items():
        grade = Grade.query.filter_by(level=grade_level).first()
        if not grade:
            continue  # Skip if grade doesn't exist
        for stream_name, student_data in streams.items():
            stream = Stream.query.filter_by(name=stream_name, grade_id=grade.id).first()
            if not stream:
                continue  # Skip if stream doesn't exist
            students = [Student(name=name, admission_number=adm_no, stream_id=stream.id, gender=gender) for name, adm_no, gender in student_data]
            db.session.add_all(students)

    # Add Subjects for all education levels
    education_levels = ["Lower Primary", "Upper Primary", "Junior School", "Senior School", "High School"]
    subject_names = [
        "Mathematics", "English", "Kiswahili", "Integrated Science and Health Education",
        "Agriculture", "Pre-Technical Studies", "Visual Arts", "Religious Education",
        "Social Studies"
    ]
    subjects = []
    
    # Create a mapping between education levels and grade levels
    education_grade_mapping = {
        "Lower Primary": ["1", "2", "3"],
        "Upper Primary": ["4", "5", "6"],
        "Junior School": ["7", "8"],
        "Senior School": ["9", "10", "11"],
        "High School": ["12", "13"]
    }
    
    # Add subjects and associate them with appropriate grades
    for edu_level in education_levels:
        for subject_name in subject_names:
            abbr = subject_name[:3].upper()  # Generate abbreviation (e.g., "MAT" for "Mathematics")
            subject = Subject(name=subject_name, abbreviation=abbr, education_level=edu_level)
            subjects.append(subject)
            
            # Associate subject with appropriate grades
            grade_levels = education_grade_mapping.get(edu_level, [])
            for grade_level in grade_levels:
                grade = Grade.query.filter_by(level=grade_level).first()
                if grade:
                    subject.grade_levels.append(grade)
    
    db.session.add_all(subjects)

    # Add Terms
    terms = [
        Term(name="term_1"),
        Term(name="term_2"),
        Term(name="term_3")
    ]
    db.session.add_all(terms)

    # Add Assessment Types
    assessment_types = [
        AssessmentType(name="opener"),
        AssessmentType(name="midterm"),
        AssessmentType(name="endterm")
    ]
    db.session.add_all(assessment_types)

    # Add Sample Marks (for Grade 5B, Term 1, Endterm)
    grade_5 = Grade.query.filter_by(level="5").first()
    stream_5b = Stream.query.filter_by(name="B", grade_id=grade_5.id).first()
    term_1 = Term.query.filter_by(name="term_1").first()
    endterm = AssessmentType.query.filter_by(name="endterm").first()
    subjects_list = Subject.query.all()

    students_5b = Student.query.filter_by(stream_id=stream_5b.id).all()
    for student in students_5b[:5]:  # Add marks for first 5 students as a sample
        for subject in subjects_list[:3]:  # Add marks for first 3 subjects
            mark = Mark(
                student_id=student.id,
                subject_id=subject.id,
                term_id=term_1.id,
                assessment_type_id=endterm.id,
                mark=50 + (student.id % 40),  # Random marks between 50 and 90
                total_marks=100
            )
            db.session.add(mark)

    db.session.commit()
    print("Database seeded successfully!")