from processors.knowledge_value_filter import (
    KnowledgeValueFilter,
    KEEP,
    CONSOLIDATE,
    EXCLUDE,
    REVIEW,
    TIER_A,
    TIER_B,
    TIER_C,
    TIER_D,
    TIER_REVIEW,
)

F = KnowledgeValueFilter()


def c(h, t, **kw):
    return F.classify(
        heading=h,
        text=t,
        **kw,
    )


# -----------------------------
# 15 universal families
# -----------------------------

def test_overview_a():
    assert c("Vision and Mission", "The institute provides education.")["tier"] == TIER_A


def test_admission_a():
    assert c("B.Tech Admission", "Eligibility and admission procedure.")["tier"] == TIER_A


def test_academics_a():
    assert c("CGPA Calculation", "CGPA is calculated using credits and grades.")["tier"] == TIER_A


def test_programs_a():
    assert c("B.Com Programme", "Accounting, finance and commerce courses.")["tier"] == TIER_A


def test_department_a():
    assert c("Department of Electrical Engineering", "The department offers undergraduate programmes.")["tier"] == TIER_A


def test_people_a():
    assert c("Head of Department", "Professor X is the HOD.")["tier"] == TIER_A


def test_rules_a():
    assert c("Academic Regulations", "Registration, attendance and examinations.")["tier"] == TIER_A


def test_fees_a():
    assert c("Fee Structure", "Tuition fees and refund rules.")["tier"] == TIER_A


def test_hostel_a():
    assert c("Hostel Rules and Timings", "Residence timings and visitor rules.")["tier"] == TIER_A


def test_student_services_a():
    assert c("Student Grievance Redressal", "Students can submit grievances.")["tier"] == TIER_A


def test_scholarship_a():
    assert c("Scholarships", "Financial assistance for eligible students.")["tier"] == TIER_A


def test_placement_a():
    assert c("Training and Placement Office", "Placement and career support.")["tier"] == TIER_A


def test_infrastructure_a():
    assert c("Campus Facilities", "Library, laboratories and medical centre.")["tier"] == TIER_A


def test_contacts_a():
    assert c("Important Contacts", "Security and emergency telephone numbers.")["tier"] == TIER_A


def test_research_a_or_b():
    r = c("Research Areas", "Research areas include VLSI and power systems.")
    assert r["tier"] in {TIER_A, TIER_B}
    assert r["knowledge_family"] == "Relevant Institutional Research"


# -----------------------------
# Campus map intentionally absent
# -----------------------------

def test_no_campus_map_family():
    r = c("Campus Map", "A map showing campus buildings.")
    assert r["knowledge_family"] not in {
        "Campus / Map / Directions",
    }


# -----------------------------
# UI must NEVER be rescued by source metadata
# -----------------------------

def test_rate_translation_is_d():
    r = c(
        "Rate this translation",
        "Do you like to give feedback Submit",
        source_name="admission_program_fees.json",
    )
    assert r["tier"] == TIER_D


def test_accessibility_is_d():
    r = c(
        "Accessibility Options",
        "Enable accessibility options",
        source_name="academic_regulations.json",
    )
    assert r["tier"] == TIER_D


# -----------------------------
# Hard document exclusions
# -----------------------------

def test_textbook_d():
    r = c(
        "Comparative Anatomy of Vertebrates",
        "Textbook for B.Sc. fourth semester with chapters and practicals.",
        source_name="comparative_anatomy_textbook.pdf",
    )
    assert r["tier"] == TIER_D


def test_research_paper_d():
    r = c(
        "Research Paper",
        "Abstract. Materials and Methods. Results. Discussion. References.",
        source_name="research_paper.pdf",
    )
    assert r["tier"] == TIER_D


def test_publication_d():
    r = c(
        "Publications",
        "Authors, DOI, journal, volume and issue.",
        source_name="publications.json",
    )
    assert r["tier"] == TIER_D


def test_project_report_d():
    r = c(
        "Project Report",
        "Project Title: Smart Grid. Principal Investigator: Professor X. Funding Agency: SERB.",
        source_name="project_report.pdf",
    )
    assert r["tier"] == TIER_D


def test_student_results_d():
    r = c(
        "Student Results",
        "Roll Number 22406003374 Student Name ANSHIKA TIWARI Marks 312 500 PASS.",
        source_name="result_sheet.pdf",
    )
    assert r["tier"] == TIER_D


def test_student_list_d():
    r = c(
        "Student List",
        "| Name | Roll Number | Batch | Email | | A | B24EE001 | 2024 | a@example.com |",
        source_name="students.pdf",
    )
    assert r["tier"] == TIER_D


def test_admission_name_list_d():
    r = c(
        "First Year Admission List",
        "Nilu Yadav PU21/184102 B.Sc First Semester Female OBC Botany Chemistry.",
        source_name="admission_list.pdf",
    )
    assert r["tier"] == TIER_D


def test_phd_person_record_d():
    r = c(
        "PhD Scholar",
        "Name: Rahul Kumar. Email: rahul@example.com. Supervisor: Professor X.",
        source_name="phd_student.json",
    )
    assert r["tier"] == TIER_D


def test_old_event_d():
    r = c(
        "Cleanliness Awareness 2019",
        "The college organized an awareness rally in 2019.",
        source_name="cleanliness_awareness_2019.pdf",
    )
    assert r["tier"] == TIER_D


def test_webinar_d():
    r = c(
        "Online Conference on COVID-19",
        "An international webinar with speakers and participants.",
        source_name="webinar_report.pdf",
    )
    assert r["tier"] == TIER_D


def test_news_d():
    r = c(
        "College in News",
        "College in News 02.10.2022.",
    )
    assert r["tier"] == TIER_D


def test_scanned_noise_d():
    r = c(
        "",
        "Scanned by CamScanner",
        source_name="book.pdf",
    )
    assert r["tier"] == TIER_D


def test_feedback_names_d():
    r = c(
        "",
        "Name of Student 310 responses Pragati Srivastava Manisha Yadav",
        source_name="all_feedback_forms_merged.json",
    )
    assert r["tier"] == TIER_D


# -----------------------------
# Real classification distinction
# -----------------------------

def test_research_area_survives_but_research_paper_d():
    good = c(
        "Research Areas",
        "Research areas include renewable energy, power systems and embedded systems.",
    )
    bad = c(
        "Research Paper",
        "The Department of Electrical Engineering reports experimental results. "
        "ISSN 1234. Abstract. References.",
    )

    assert good["knowledge_family"] == "Relevant Institutional Research"
    assert good["tier"] in {TIER_A, TIER_B}
    assert bad["tier"] == TIER_D


def test_department_page_survives_body_noise():
    r = c(
        "Department of Computer Science",
        "The department offers B.Tech, M.Tech and PhD programmes and has faculty members.",
        source_name="department_page.html",
    )
    assert r["tier"] == TIER_A


def test_filename_cannot_create_wrong_family():
    r = c(
        "Cyber Security Awareness",
        "Students should verify suspicious links and avoid unknown USB ports.",
        source_name="hostel_rules.json",
    )
    assert r["knowledge_family"] != "Hostel / Accommodation"
    assert r["tier"] in {TIER_C, TIER_D, TIER_REVIEW}


# -----------------------------
# C and REVIEW
# -----------------------------

def test_collaboration_c():
    r = c(
        "Collaborations",
        "The institute maintains collaborations with external organizations.",
    )
    assert r["tier"] == TIER_C
    assert r["rag_eligible"] is False


def test_tender_c():
    r = c(
        "Tender",
        "Supply and installation of equipment for campus operations.",
    )
    assert r["tier"] == TIER_C


def test_review_is_not_generic_junk():
    r = c(
        "Special Institutional Process",
        "The college maintains a documented process for students and staff "
        "with defined institutional responsibilities and procedures.",
    )
    assert r["tier"] == TIER_REVIEW
    assert r["rag_eligible"] is True


def test_random_noncollege_is_d():
    r = c(
        "Weather",
        "Today's city weather forecast and temperature.",
    )
    assert r["tier"] == TIER_D


# -----------------------------
# Cross-discipline universality
# -----------------------------

def test_law_college():
    assert c(
        "LLB Academic Regulations",
        "Attendance, examinations and academic progression rules.",
    )["tier"] == TIER_A


def test_medical_college():
    assert c(
        "Department of Pathology",
        "The department provides teaching and laboratory services.",
    )["tier"] == TIER_A


def test_commerce_college():
    assert c(
        "B.Com Programme",
        "The programme includes accounting and finance courses.",
    )["tier"] == TIER_A


def test_no_hostel_family_without_hostel_evidence():
    r = c(
        "Department of Commerce",
        "The department offers B.Com and M.Com programmes.",
    )
    assert r["knowledge_family"] != "Hostel / Accommodation"


# -----------------------------
# Old known failure: research project/event rescue
# -----------------------------

def test_research_project_is_d_even_if_department_appears():
    r = c(
        "Research Project",
        "This project is conducted by the Department of Chemistry. "
        "Project Title: Water Purification. Principal Investigator: Professor X.",
    )
    assert r["tier"] == TIER_D


def test_workshop_is_d_even_if_research_appears():
    r = c(
        "Research Methodology Workshop 2022",
        "Workshop for research scholars on methodology and data analysis.",
        source_name="research_methodology_workshop.pdf",
    )
    assert r["tier"] == TIER_D


def test_legacy_event_is_d():
    r = c(
        "Graduating Fund Raiser Campaign",
        "A campaign organized for graduating students in 2020.",
        source_name="fundraiser_event.pdf",
    )
    assert r["tier"] == TIER_D