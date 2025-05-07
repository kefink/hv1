from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(10), unique=True, nullable=False)  # e.g., "5"
    education_level = db.Column(db.String(50), nullable=False)  # e.g., "Primary" (added for consistency with templates)
    streams = db.relationship('Stream', backref='grade', lazy=True)
    
    # Relationship with Subject
    subject_list = db.relationship('Subject', 
                                 secondary='subject_grade', 
                                 back_populates='grade_levels',
                                 lazy=True)

class Stream(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False)  # e.g., "A"
    grade_id = db.Column(db.Integer, db.ForeignKey('grade.id'), nullable=False)
    students = db.relationship('Student', backref='stream', lazy=True)

class Subject(db.Model):
    __tablename__ = 'subject'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Mathematics"
    abbreviation = db.Column(db.String(10))  # e.g., "MTH"
    education_level = db.Column(db.String(50), nullable=False)  # e.g., "lower_primary"
    marks = db.relationship('Mark', backref='subject', lazy=True)
    
    # Relationship with Grade
    grade_levels = db.relationship('Grade', 
                                 secondary='subject_grade', 
                                 back_populates='subject_list',
                                 lazy=True)

    __table_args__ = (
        db.UniqueConstraint('name', 'education_level', name='uix_subject_name_edu_level'),
    )

# Association table for many-to-many relationship between Subject and Grade
subject_grade = db.Table('subject_grade',
    db.Column('subject_id', db.Integer, db.ForeignKey('subject.id'), primary_key=True),
    db.Column('grade_id', db.Integer, db.ForeignKey('grade.id'), primary_key=True)
)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # e.g., "John Doe"
    admission_number = db.Column(db.String(50), unique=True, nullable=False)  # Added from your model
    stream_id = db.Column(db.Integer, db.ForeignKey('stream.id'), nullable=True)
    gender = db.Column(db.String(20), nullable=True)  # Added from your model
    marks = db.relationship('Mark', backref='student', lazy=True)

# Updated Teacher model to work with Flask-Login
class Teacher(db.Model, UserMixin):  # Add UserMixin inheritance
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)  # Store hashed password
    role = db.Column(db.String(20), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # The UserMixin provides default implementations for:
    # is_authenticated, is_active, is_anonymous, and get_id()

class Term(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # e.g., "term_1"
    marks = db.relationship('Mark', backref='term', lazy=True)

class AssessmentType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # e.g., "opener"
    marks = db.relationship('Mark', backref='assessment_type', lazy=True)

class Mark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    term_id = db.Column(db.Integer, db.ForeignKey('term.id'), nullable=False)
    assessment_type_id = db.Column(db.Integer, db.ForeignKey('assessment_type.id'), nullable=False)
    mark = db.Column(db.Float, nullable=False)
    total_marks = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Association table for many-to-many relationship between Subject and Teacher
teacher_subject = db.Table('teacher_subject',
    db.Column('subject_id', db.Integer, db.ForeignKey('subject.id'), primary_key=True),
    db.Column('teacher_id', db.Integer, db.ForeignKey('teacher.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)