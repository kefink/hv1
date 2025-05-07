from collections import defaultdict

def get_performance_category(percentage):
    if percentage >= 75:
        return "E.E"
    elif percentage >= 50:
        return "M.E"
    elif percentage >= 30:
        return "A.E"
    else:
        return "B.E"

def get_grade_and_points(average):
    if average >= 80:
        return "A", 12
    elif average >= 75:
        return "A-", 11
    elif average >= 70:
        return "B+", 10
    elif average >= 65:
        return "B", 9
    elif average >= 60:
        return "B-", 8
    elif average >= 55:
        return "C+", 7
    elif average >= 50:
        return "C", 6
    elif average >= 45:
        return "C-", 5
    elif average >= 40:
        return "D+", 4
    elif average >= 35:
        return "D", 3
    elif average >= 30:
        return "D-", 2
    else:
        return "E", 1

def get_performance_summary(marks_data):
    summary = defaultdict(int)
    for student in marks_data:
        summary[student[3]] += 1
    return dict(summary)

def get_subject_performance_category(percentage):
    if percentage >= 75:
        return "Exceeding Expectation"
    elif percentage >= 50:
        return "Meeting Expectation"
    elif percentage >= 30:
        return "Approaching Expectation"
    else:
        return "Below Expectation"