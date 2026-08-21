
from processors.knowledge_value_filter import (
    KEEP,
    CONSOLIDATE,
    EXCLUDE,
    REVIEW,
    TIER_A,
    TIER_B,
    TIER_C,
    TIER_D,
    TIER_REVIEW,
    KnowledgeValueFilter,
)

F = KnowledgeValueFilter()


def c(h, t, **kw):
    return F.classify(
        heading=h,
        text=t,
        **kw,
    )


# Core assistant questions
def test_overview_a():
    r = c("Vision and Mission", "The college provides education and research.")
    assert r["tier"] == TIER_A


def test_admission_a():
    r = c("MBBS Admission", "Eligibility, counselling, seat intake and documents required.")
    assert r["tier"] == TIER_A


def test_academics_a():
    r = c("CGPA Calculation", "CGPA is calculated using the prescribed credit weighted grading system.")
    assert r["tier"] == TIER_A


def test_program_a():
    r = c("B.Com Programme", "The programme includes accounting, finance and commerce courses.")
    assert r["tier"] == TIER_A


def test_department_a():
    r = c("Department of Electrical Engineering", "The department offers undergraduate programmes.")
    assert r["tier"] == TIER_A


def test_hod_a():
    r = c("Head of Department", "Professor X is HOD of Mechanical Engineering.")
    assert r["tier"] == TIER_A


def test_faculty_a():
    r = c("Faculty Members", "The department has professors and assistant professors.")
    assert r["tier"] == TIER_A


def test_rules_a():
    r = c("Academic Regulations", "Registration, attendance, grading and examination regulations.")
    assert r["tier"] == TIER_A


def test_hostel_a():
    r = c("Hostel Rules and Timings", "Residence timings and visitor rules.")
    assert r["tier"] == TIER_A


def test_fees_a():
    r = c("Fee Structure", "Tuition fee and refund rules.")
    assert r["tier"] == TIER_A


def test_student_services_a():
    r = c("Student Grievance Redressal", "Students can submit grievances through the college mechanism.")
    assert r["tier"] == TIER_A


def test_scholarship_a():
    r = c("Scholarships", "Government scholarships and financial assistance are available.")
    assert r["tier"] == TIER_A


def test_placement_a():
    r = c("Training and Placement Office", "The office coordinates placements and career support.")
    assert r["tier"] == TIER_A


def test_infrastructure_a():
    r = c("Campus Facilities", "Laboratories, library, sports facilities and medical centre.")
    assert r["tier"] == TIER_A


def test_contacts_a():
    r = c("Important Contacts", "Security 1000, medical centre 1001, admissions office 1002.")
    assert r["tier"] == TIER_A


def test_research_b():
    r = c("Research Areas", "Research areas include renewable energy and VLSI.")
    assert r["tier"] == TIER_A or r["tier"] == TIER_B
    assert r["knowledge_family"] == "Relevant Institutional Research"


# No campus map/directions family
def test_map_is_not_a_family():
    r = c("Campus Map", "The map shows campus buildings and roads.")
    assert r["knowledge_family"] != "Campus / Map / Directions"


# Useful PDFs remain
def test_rules_pdf_a():
    r = c("Academic Regulations", "Rules for registration, attendance and examinations.",
          source_name="academic_regulations.pdf")
    assert r["tier"] == TIER_A


def test_hostel_pdf_a():
    r = c("Hostel Handbook", "Hostel timings and accommodation regulations.",
          source_name="hostel_handbook.pdf")
    assert r["tier"] == TIER_A


# Hard exclusions
def test_textbook_d():
    r = c("Comparative Anatomy of Vertebrates",
          "Textbook for B.Sc. fourth semester with chapters and practicals.",
          source_name="comparative_anatomy_textbook.pdf")
    assert r["tier"] == TIER_D


def test_research_paper_d():
    r = c("Research Paper",
          "Abstract. Materials and Methods. Results. Discussion. References.",
          source_name="research_paper.pdf")
    assert r["tier"] == TIER_D


def test_publication_d():
    r = c("Publications",
          "Authors, DOI, journal title, volume and issue.",
          source_name="publications.json")
    assert r["tier"] == TIER_D


def test_student_result_d():
    r = c("Student Results",
          "Roll Number 22406003374 Student Name ANSHIKA TIWARI Marks 312 500 PASS.",
          source_name="result_sheet.pdf")
    assert r["tier"] == TIER_D


def test_student_list_d():
    r = c("Student List",
          "| Name | Roll Number | Batch | Email | | A | B24EE001 | 2024 | a@example.com |",
          source_name="student_list.pdf")
    assert r["tier"] == TIER_D


def test_admission_name_list_d():
    r = c("First Year Admission List",
          "Nilu Yadav PU21/184102 B.Sc First Semester Female OBC Botany Chemistry.",
          source_name="admission_list.pdf")
    assert r["tier"] == TIER_D


def test_individual_phd_d():
    r = c("PhD Scholar",
          "Name: Rahul Kumar. Email: rahul@example.com. Supervisor: Professor X.",
          source_name="phd_student.json")
    assert r["tier"] == TIER_D


def test_project_record_d():
    r = c("Research Project",
          "Project Title: Smart Grid. Principal Investigator: Professor X. Funding Agency: SERB.")
    assert r["tier"] == TIER_D


def test_event_report_d():
    r = c("Cleanliness Awareness 2019",
          "The college organized an awareness rally in 2019.",
          source_name="cleanliness_awareness_2019.pdf")
    assert r["tier"] == TIER_D


def test_news_d():
    r = c("College in News",
          "College in News 02.10.2022.")
    assert r["tier"] == TIER_D


def test_scanned_noise_d():
    r = c("", "Scanned by CamScanner", source_name="book.pdf")
    assert r["tier"] == TIER_D


# C: legitimate extra institutional content, not RAG
def test_collaboration_c():
    r = c("Collaborations",
          "The institute maintains collaborations with national organizations.")
    assert r["tier"] == TIER_C
    assert r["decision"] == CONSOLIDATE
    assert r["rag_eligible"] is False


def test_accreditation_c():
    r = c("Accreditation Report",
          "The institution maintains accreditation and quality records.")
    assert r["tier"] == TIER_C


# REVIEW: potentially useful institutional information only
def test_review_plausible_unknown():
    r = c("Special Institutional Process",
          "The college maintains a documented process for students and staff "
          "with defined institutional procedures and responsibilities.")
    assert r["tier"] in {
        TIER_REVIEW,
        TIER_A,
        TIER_B,
    }
    assert r["rag_eligible"] is True


def test_random_noncollege_is_d():
    r = c("Weather",
          "Today's weather conditions and forecast for the city.")
    assert r["tier"] == TIER_D


# University / discipline agnostic
def test_law_college():
    r = c("LLB Academic Regulations",
          "Attendance, examinations and academic progression rules.")
    assert r["tier"] == TIER_A


def test_medical_college():
    r = c("Department of Pathology",
          "The department provides teaching and laboratory services.")
    assert r["tier"] == TIER_A


def test_small_college_without_hostel():
    r = c("Department of Commerce",
          "The department offers B.Com and M.Com programmes.")
    assert r["knowledge_family"] != "Hostel / Accommodation"


# Edge cases from real GWPGC audit
def test_research_paper_with_department_word_still_d():
    r = c("",
          "This study was conducted in the Department of Botany. "
          "Abstract. Materials and Methods. Results. References.",
          source_name="13_research_paper.json")
    assert r["tier"] == TIER_D


def test_book_with_bsc_words_d():
    r = c("",
          "As per CBCS syllabus for B.Sc. 4th Semester. Textbook with chapters.",
          source_name="comparative_anatomy_textbook.json")
    assert r["tier"] == TIER_D

def test_feedback_names_d():
    r = c("",
          "Name of Student 310 responses Pragati Srivastava Manisha Yadav Nikita Vikram",
          source_name="all_feedback_forms_merged.json")
    assert r["tier"] == TIER_D