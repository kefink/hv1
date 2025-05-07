# app/utils/constants.py
EDUCATION_LEVEL_NAMES = {
    "lower_primary": "Lower Primary",
    "upper_primary": "Upper Primary",
    "junior_secondary": "Junior Secondary"
}

SUBJECT_MAPPING = {
    "lower_primary": [
        "Mathematics", "English", "Kiswahili", "Integrated Science and Health Education",
        "Agriculture", "Pre-Technical Studies", "Visual Arts", "Religious Education",
        "Social Studies"
    ],
    "upper_primary": [
        "Mathematics", "English", "Kiswahili", "Integrated Science and Health Education",
        "Agriculture", "Pre-Technical Studies", "Visual Arts", "Religious Education",
        "Social Studies"
    ],
    "junior_secondary": [
        "Mathematics", "English", "Kiswahili", "Integrated Science and Health Education",
        "Agriculture", "Pre-Technical Studies", "Visual Arts", "Religious Education",
        "Social Studies"
    ]
}

SUBJECT_ABBREVIATIONS = {
    "Mathematics": "MATH",
    "English": "ENG",
    "Kiswahili": "KISW",
    "Integrated Science and Health Education": "ISHE",
    "Agriculture": "AGR",
    "Pre-Technical Studies": "PTS",
    "Visual Arts": "VA",
    "Religious Education": "RE",
    "Social Studies": "SS"
}

EDUCATIONAL_LEVELS = [
    "Lower Primary",
    "Upper Primary",
    "Junior School",
    "Senior School",
    "High School"
]

EDUCATIONAL_LEVEL_MAPPING = {
    "Lower Primary": ["Grade 1", "Grade 2", "Grade 3"],
    "Upper Primary": ["Grade 4", "Grade 5", "Grade 6"],
    "Junior School": ["Grade 7", "Grade 8", "Grade 9"],
    "Senior School": ["Grade 10", "Grade 11", "Grade 12"],
    "High School": ["Form 2", "Form 3", "Form 4"]
}

# Add a flat list of all subjects for easier access
ALL_SUBJECTS = [
    "Mathematics", "English", "Kiswahili", "Integrated Science and Health Education",
    "Agriculture", "Pre-Technical Studies", "Visual Arts", "Religious Education",
    "Social Studies"
]