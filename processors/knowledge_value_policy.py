"""
Final universal policy for the college-assistant demo RAG value filter.

The crawler may collect everything. Command 3 decides what belongs in the
student/faculty/staff-facing demo knowledge base.

15 universal semantic families:
1. Institute / College Overview
2. Admissions
3. Academics
4. Programs & Courses
5. Departments / Schools / Branches
6. Faculty / HOD / Dean / Key People
7. Rules & Regulations / Policies
8. Fees / Financial Information
9. Hostel / Accommodation
10. Student Services / Welfare
11. Scholarships / Financial Aid
12. Placements / Careers
13. Infrastructure / Facilities
14. Important Contacts / Emergency
15. Relevant Institutional Research

Tiers:
A       Core, high-value institutional knowledge
B       Important institutional knowledge
REVIEW  Plausibly useful but uncertain institutional knowledge
C       Legitimate low-priority institutional extra; not in demo RAG
D       Excluded from demo RAG

The policy is college-agnostic. It does not hardcode IITJ/GWPGC departments,
programs, faculty names, or hostel assumptions.
"""

CORE_FAMILIES = (
    "Institute / College Overview",
    "Admissions",
    "Academics",
    "Programs & Courses",
    "Departments / Schools / Branches",
    "Faculty / HOD / Dean / Key People",
    "Rules & Regulations / Policies",
    "Fees / Financial Information",
    "Hostel / Accommodation",
    "Student Services / Welfare",
    "Scholarships / Financial Aid",
    "Placements / Careers",
    "Infrastructure / Facilities",
    "Important Contacts / Emergency",
    "Relevant Institutional Research",
)

FAMILY_SIGNALS = {
    "Institute / College Overview": (
        "vision and mission", "vision", "mission", "about the institute",
        "about the college", "institute overview", "college overview",
        "institution overview", "history of the college",
        "history of the institute", "established in", "about us",
        "who we are",
    ),
    "Admissions": (
        "admission rules", "admission process", "admission procedure",
        "admission eligibility", "admission", "admissions", "eligibility",
        "application process", "application procedure", "counselling",
        "counseling", "seat intake", "intake capacity", "documents required",
        "admission brochure", "admission prospectus", "reservation rules",
        "reservation policy", "seat matrix", "how to apply",
        "registration for admission",
    ),
    "Academics": (
        "academic calendar", "academic regulations", "academic rules",
        "grading system", "grading", "cgpa", "cg calculation",
        "credit structure", "credits", "semester", "examination rules",
        "exam rules", "course registration", "registration",
        "attendance policy", "attendance", "academic progression",
        "academic session", "timetable", "time table", "class schedule",
        "course schedule", "section and group allocation",
        "instructors and classrooms", "evaluation system", "assessment rules",
    ),
    "Programs & Courses": (
        "programmes offered", "programs offered", "course catalog",
        "course catalogue", "courses offered", "programmes", "programs",
        "programme", "program", "course", "courses", "curriculum",
        "syllabus", "degree programme", "degree program", "b.tech", "b tech",
        "m.tech", "m tech", "b.sc", "b sc", "m.sc", "m sc", "b.com", "b com",
        "bba", "mba", "b.a.", "b a", "llb", "mbbs", "phd", "p.hd",
    ),
    "Departments / Schools / Branches": (
        "department of", "departments", "department", "school of", "schools",
        "faculty of", "branch of", "branches",
    ),
    "Faculty / HOD / Dean / Key People": (
        "faculty members", "faculty directory", "faculty profile", "faculty profiles",
        "faculty", "professor", "associate professor", "assistant professor",
        "dean", "director", "principal", "registrar", "vice chancellor",
        "chancellor", "head of department", "head of the department", "hod",
        "key functionaries", "position holders", "leadership", "office head",
        "faculty contact", "principal's message", "principal message",
    ),
    "Rules & Regulations / Policies": (
        "rules and regulations", "rules", "regulations", "regulation", "policy",
        "policies", "guidelines", "code of conduct", "conduct rules",
        "disciplinary rules", "anti ragging", "anti-ragging", "grievance policy",
        "leave rules", "academic regulations", "examination rules", "hostel rules",
        "student rules",
    ),
    "Fees / Financial Information": (
        "fee structure", "fees", "fee", "tuition fee", "tuition fees",
        "admission fee", "semester fee", "hostel fee", "hostel fees", "charges",
        "refund policy", "fee refund", "dues", "payment of fees",
    ),
    "Hostel / Accommodation": (
        "hostel rules", "hostel timing", "hostel timings", "hostel booking",
        "hostel accommodation", "hostel fee", "hostel fees", "hostel",
        "hostels", "accommodation", "residential facilities", "residence rules",
        "visitor rules", "mess", "warden", "wardens",
    ),
    "Student Services / Welfare": (
        "student services", "student affairs", "student welfare", "student support",
        "student wellbeing", "student well-being", "grievance redressal",
        "grievance", "counselling service", "counseling service", "student help",
        "student support office", "student senate", "student development",
    ),
    "Scholarships / Financial Aid": (
        "scholarship", "scholarships", "fellowship", "fellowships", "financial aid",
        "financial assistance", "assistantship", "student financial support",
    ),
    "Placements / Careers": (
        "training and placement", "training & placement", "placement office",
        "placements", "placement", "career services", "career office", "careers",
        "recruitment process", "internship policy", "internships",
    ),
    "Infrastructure / Facilities": (
        "infrastructure", "facilities", "facility", "laboratory", "laboratories",
        "labs", "lab facilities", "library", "gymnasium", "auditorium",
        "sports facilities", "computer center", "computer centre", "medical centre",
        "medical center", "health centre", "health center", "campus facilities",
        "estate office", "physical infrastructure", "hostel infrastructure",
    ),
    "Important Contacts / Emergency": (
        "important contacts", "contact us", "emergency contacts", "emergency contact",
        "emergency helpline", "helpline", "office contact", "department contact",
        "security contact", "medical emergency", "nodal officer", "contact details",
        "communication details", "phone number", "telephone number", "email address",
    ),
    "Relevant Institutional Research": (
        "research areas", "research area", "research centre", "research center",
        "research centres", "research centers", "research group", "research groups",
        "research theme", "research themes", "research focus", "research interests",
        "research capability", "research infrastructure", "research overview",
        "major research areas", "current research areas",
    ),
}

# Hard document identities. These run BEFORE family classification.
HARD_EXCLUDE_GENRES = (
    # books/publications
    "textbook", "text book", "book chapter", "chapter in", "journal article",
    "journal paper", "research paper", "research papers", "conference paper",
    "conference papers", "proceedings", "publication", "publications", "thesis",
    "dissertation", "research article", "original article", "international journal",
    # projects/personal records
    "project report", "individual project", "project record", "research project record",
    "website research project", "website-research-project", "student result",
    "student results", "result list", "result sheet", "marksheet", "mark sheet",
    "tabulation chart", "student list", "student roster", "student directory",
    "student names", "students list", "current students", "graduated students",
    "phd scholars", "phd students", "alumni directory", "alumni list",
    "alumni global presence", "admission list", "candidate list", "merit list",
    "selected candidates", "shortlisted candidates", "speaker list", "participant list",
    # events/news/activities
    "event report", "seminar report", "workshop report", "activity report",
    "annual activity", "annual event report", "college in news", "news archive",
    "newsletter archive", "newsletter", "latest news", "news & events", "news and events",
    "current activities", "upcoming events", "upcoming programmes", "past events",
    "online conference", "webinar report", "webinar", "research methodology workshop",
    "awareness programme", "awareness program", "awareness rally", "medical check-up camp",
    "mask distribution", "plantation and distribution", "voter awareness", "yoga practice camp",
    "nss activity", "ncc activity", "plogging", "fund raiser campaign", "fundraiser campaign",
    "award announcement", "award ceremony", "award 2024", "award 2025", "award 2026",
    "competition & training programme", "competition and training programme",
    "statue cleaning programme", "swachh bharat", "mission shakti", "number of participants",
    "competition programme", "training programme under", "cultural programme", "ncc cadets", "nss",
    # feedback/reporting/statistics
    "feedback form", "feedback forms", "feedback report", "stakeholder feedback",
    "survey response", "survey responses", "response analytics", "google forms",
    "action taken report", "action taken report on feedback", "feedback and action taken",
    "aishe", "all india survey on higher education", "data capture format", "aqar",
    "self study report", "ssr", "naac ssr", "accreditation report", "audit statement",
    "audited statement of income", "audited statement of income and expenditure",
    "audit report", "financial year report", "pass percentage", "final year examination details",
)

PUBLICATION_BODY_SIGNALS = (
    "issn", "isbn", "doi", "doi.org", "impact factor", "ugc care", "materials and methods",
    "materials & methods", "published by", "copyright", "volume", "issue", "original article",
    "research article", "references", "works cited", "elsevier", "springer", "wiley",
    "taylor & francis",
)

RECORD_SIGNALS = (
    "roll number", "roll no", "registration number", "enrollment number", "student name",
    "name of student", "father's name", "mother's name", "date of birth", "alumni name",
    "year of graduation", "current job role", "current job role & company", "principal investigator",
    "funding agency", "project title", "project name", "co-pi",
)

LOW_PRIORITY_EXTRA = (
    "collaborations", "collaboration", "industry collaboration", "strategic partnership",
    "tender", "tenders", "procurement",
)

UI_SIGNALS = (
    "rate this translation", "do you like to give feedback", "submit feedback",
    "enable accessibility options", "accessibility options", "skip to main content",
    "cookie settings",
)

VOLATILE_PRIMARY_GENRES = (
    "news", "newsletter", "latest", "highlights", "event", "events", "seminar", "seminars",
    "workshop", "workshops", "conference", "conferences", "webinar", "webinars", "campaign",
    "rally", "celebration", "celebrations", "commemoration", "award", "awards", "achievement",
    "achievements",
)

CURRENT_YEAR_WORDS = (
    "2026", "2025-26", "2026-27", "2025–26", "2026–27", "current", "latest session", "current session",
)

HISTORICAL_WORDS = (
    "2014-15", "2015-16", "2016-17", "2017-18", "2018-19", "2019-20", "2020-21",
    "2021-22", "2022-23", "2023-24", "2024-25", "old", "archive", "archived", "historical", "past",
)

INSTITUTIONAL_INTENT = (
    "rules", "regulations", "policy", "procedure", "eligibility", "admission", "academic calendar",
    "course", "programme", "department", "faculty", "hod", "dean", "principal", "registrar", "hostel",
    "fee", "scholarship", "placement", "infrastructure", "facility", "contact", "emergency",
    "research areas", "research centre", "research group", "student services", "grievance",
    "curriculum", "syllabus", "timetable", "class schedule",
)