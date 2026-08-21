from processors.knowledge_value_filter import KnowledgeValueFilter

F = KnowledgeValueFilter()


def c(h, t, **kw):
    return F.classify(heading=h, text=t, **kw)


# ------------------------------------------------------------------
# All 15 universal families
# ------------------------------------------------------------------

def test_15_families():
    cases = [
        ("Vision and Mission", "The college provides education and research.", "Institute / College Overview"),
        ("Admission Rules and Procedure", "Eligibility, documents and application steps.", "Admissions"),
        ("CGPA Calculation", "CGPA is calculated using credits and grades.", "Academics"),
        ("B.Com Programme", "Accounting and finance courses.", "Programs & Courses"),
        ("Department of Electrical Engineering", "Academic programs and faculty information.", "Departments / Schools / Branches"),
        ("Head of Department", "Professor X is the HOD.", "Faculty / HOD / Dean / Key People"),
        ("Academic Regulations", "Registration, attendance and examination rules.", "Academics"),
        ("Fee Structure", "Tuition fees and refund rules.", "Fees / Financial Information"),
        ("Hostel Rules and Timings", "Residence timings and visitor rules.", "Hostel / Accommodation"),
        ("Student Grievance Redressal", "Students can submit grievances.", "Student Services / Welfare"),
        ("Scholarships", "Eligible students can receive financial assistance.", "Scholarships / Financial Aid"),
        ("Training and Placement Office", "Placement and career support.", "Placements / Careers"),
        ("Campus Facilities", "Library, laboratories and medical facilities.", "Infrastructure / Facilities"),
        ("Important Contacts", "Security and emergency numbers.", "Important Contacts / Emergency"),
        ("Research Areas", "Research areas include VLSI and power systems.", "Relevant Institutional Research"),
    ]
    for h, t, expected in cases:
        r = c(h, t)
        assert r["tier"] in {"A", "B"}, (h, r)
        assert r["knowledge_family"] == expected, (h, r)


# ------------------------------------------------------------------
# Real failures previously observed
# ------------------------------------------------------------------

def test_student_table_hidden_in_btech_student_source_is_d():
    r = c(
        "2021",
        "| S No | Name | Roll No | | 1 | Abhilasha Bidwaiker | B21CI002 | | 2 | Akash | B21CI004 |",
        source_name="b_tech_student.json",
    )
    assert r["tier"] == "D"


def test_encoded_research_paper_filename_is_d():
    r = c(
        "",
        "Pesticide Biochemistry and Physiology 184 (2022) 105066. Abstract. References.",
        source_name="3_20ak_2021-22_20research_20paper.json",
    )
    assert r["tier"] == "D"


def test_encoded_feedback_filename_is_d():
    r = c(
        "",
        "Feedback-Stakeholders Student Peer Employer Alumni. 310 responses. Feedback Observations.",
        source_name="2017-18_20action_20taken_20report_20feedback.json",
    )
    assert r["tier"] == "D"


def test_encoded_audit_filename_is_d():
    r = c(
        "",
        "Grants received and expenditures. Principal Head of HEI Chartered Accountant.",
        source_name="audited_20statement_20of_20income_20and_20expenditure.json",
    )
    assert r["tier"] == "D"


def test_activity_programme_is_d_not_programs():
    r = c(
        "",
        "Miscellaneous Competition & Training Programme under Mission Shakti by NSS and NCC. Number of Participants: 105.",
        source_name="20_20miscellaneous_20competition_20_26_20training_20programme.json",
    )
    assert r["tier"] == "D"


def test_statue_cleaning_programme_is_d():
    r = c(
        "",
        "Statue Cleaning Programme under Swachh Bharat Abhiyan by NCC. Number of Participants: 64.",
        source_name="32_20statue_20cleaning_20programme.json",
    )
    assert r["tier"] == "D"


def test_research_methodology_event_is_d():
    r = c(
        "",
        "Researchers can develop their research problem. Technical session was handled by Dr. Vandana Kumari, Associate Professor.",
        source_name="10_20-_202020-21_20research_20methodology.json",
    )
    assert r["tier"] == "D"


def test_aqar_activity_report_is_d():
    r = c(
        "",
        "Sports and cultural activities organised during the year. Number of participants.",
        source_name="aqar_202019-20.json",
    )
    assert r["tier"] == "D"


def test_aishe_scholarship_statistics_is_d():
    r = c(
        "",
        "Survey Year 2020. Students Receiving Government Fellowship. Scholarship statistics.",
        source_name="aishe_20c-16113-dcf_202020-21.json",
    )
    assert r["tier"] == "D"


def test_research_rules_collision_is_d():
    r = c(
        "",
        "Pesticide Biochemistry and Physiology. Assessment of antioxidant activity. Rules and regulations.",
        source_name="3_20ak_2021-22_20research_20paper.json",
    )
    assert r["tier"] == "D"


# ------------------------------------------------------------------
# Research-vs-department distinction
# ------------------------------------------------------------------

def test_about_research_is_research_family():
    r = c(
        "About Research",
        "The department's research focuses on chemistry, materials and computational chemistry.",
    )
    assert r["knowledge_family"] == "Relevant Institutional Research"
    assert r["tier"] in {"A", "B"}


def test_department_profile_with_research_is_department_family():
    r = c(
        "Department of Electrical Engineering",
        "The department offers B.Tech and M.Tech. Research areas include power systems, VLSI and embedded systems.",
    )
    assert r["knowledge_family"] == "Departments / Schools / Branches"
    assert r["tier"] == "A"


def test_research_areas_is_research_family():
    r = c(
        "Current Research Areas",
        "Blended learning, flipped classroom and engineering education research.",
    )
    assert r["knowledge_family"] == "Relevant Institutional Research"


# ------------------------------------------------------------------
# Title/heading precedence
# ------------------------------------------------------------------

def test_fee_heading_not_overridden_by_admissions_title():
    r = c(
        "Fee Structure",
        "AY 2026-27 tuition and semester fees.",
        document_title="Admissions",
    )
    assert r["knowledge_family"] == "Fees / Financial Information"
    assert r["tier"] == "A"


def test_research_heading_not_overridden_by_department_title():
    r = c(
        "About Research",
        "Research areas in inorganic and organic chemistry.",
        document_title="Departments",
    )
    assert r["knowledge_family"] == "Relevant Institutional Research"


# ------------------------------------------------------------------
# Current useful vs historical junk
# ------------------------------------------------------------------

def test_current_admission_is_a():
    r = c(
        "Admission Rules and Procedure 2026-27",
        "Eligibility, application procedure, documents required and how to apply.",
    )
    assert r["tier"] == "A"


def test_old_admission_notice_is_d():
    r = c(
        "Admission Notice 2007",
        "Admission notice and application information for session 2007-08.",
    )
    assert r["tier"] == "D"


def test_current_calendar_is_a():
    r = c(
        "Academic Calendar 2026-27",
        "Semester start, registration, examinations and vacation dates.",
    )
    assert r["tier"] == "A"


def test_old_calendar_is_d():
    r = c(
        "Academic Calendar 2017-18",
        "Semester start and examination dates for 2017-18.",
    )
    assert r["tier"] == "D"


# ------------------------------------------------------------------
# Publication / record boundaries
# ------------------------------------------------------------------

def test_research_paper_d():
    r = c(
        "Research Paper",
        "Abstract. Materials and Methods. Results. Discussion. References. ISSN 1234.",
        source_name="research_paper.pdf",
    )
    assert r["tier"] == "D"


def test_journal_article_d():
    r = c(
        "",
        "International Journal of Biology. Volume 12. Issue 4. Original Article. ISSN 1234. References.",
        source_name="paper.pdf",
    )
    assert r["tier"] == "D"


def test_textbook_d_even_with_syllabus_word():
    r = c(
        "",
        "B.Sc. fourth semester syllabus, chapters, exercises and course material.",
        source_name="comparative_anatomy_textbook.pdf",
    )
    assert r["tier"] == "D"


def test_alumni_d():
    r = c(
        "Alumni",
        "| Alumni Name | Year of Graduation | Course | Current Job Role & Company | | Rahul | 2020 | B.Tech | Company X |",
    )
    assert r["tier"] == "D"


def test_student_result_d():
    r = c(
        "Results",
        "Roll Number 1001 Student Name Rahul Marks 350 PASS 2020.",
        source_name="student_results.pdf",
    )
    assert r["tier"] == "D"


# ------------------------------------------------------------------
# Legitimate structured pages
# ------------------------------------------------------------------

def test_timetable_is_academics():
    r = c(
        "First Year Section A",
        "Courses for Section A, course codes, credits and classrooms.",
        source_name="first_year_class_time_table.json",
    )
    assert r["knowledge_family"] == "Academics"
    assert r["tier"] in {"A", "B"}


def test_contact_is_contact_family():
    r = c(
        "EBSB Nodal Officer",
        "Name Dr Bhaswati Sarma, email bhaswati@college.ac.in, office contact details.",
    )
    assert r["knowledge_family"] == "Important Contacts / Emergency"
    assert r["tier"] in {"A", "B"}


def test_principal_message_is_people():
    r = c(
        "Principal's Message",
        "The principal explains the college's academic mission and student development.",
    )
    assert r["knowledge_family"] == "Faculty / HOD / Dean / Key People"
    assert r["tier"] == "A"


def test_current_research_facility_is_infrastructure():
    r = c(
        "Research Facilities",
        "Advanced instrumentation facilities include a Differential Scanning Calorimeter and other equipment.",
    )
    assert r["knowledge_family"] == "Infrastructure / Facilities"


# ------------------------------------------------------------------
# C / REVIEW / D boundaries
# ------------------------------------------------------------------

def test_collaboration_c():
    r = c("Collaborations", "The institute maintains collaborations with external organizations.")
    assert r["tier"] == "C"
    assert not r["rag_eligible"]


def test_review_is_narrow():
    r = c(
        "Special Institutional Process",
        "The institute office manages a documented process with institutional responsibilities and student support.",
    )
    assert r["tier"] == "REVIEW"


def test_review_does_not_accept_paper():
    r = c("", "Journal of Biology. ISSN 1234. Abstract. References. The college published the article.")
    assert r["tier"] == "D"


def test_random_external_is_d():
    assert c("Weather", "Today's city weather forecast.")["tier"] == "D"


# ------------------------------------------------------------------
# Cross-domain universality
# ------------------------------------------------------------------

def test_law_college():
    assert c("LLB Academic Regulations", "Attendance, examinations and academic progression rules.")["tier"] == "A"


def test_medical_college():
    assert c("Department of Pathology", "Teaching and laboratory services.")["tier"] == "A"


def test_commerce_college():
    assert c("B.Com Programme", "Accounting and finance courses.")["tier"] == "A"


def test_no_hostel_forced_without_evidence():
    r = c("Department of Commerce", "The department offers B.Com and M.Com programmes.")
    assert r["knowledge_family"] != "Hostel / Accommodation"