from processors_v2.knowledge_organization_iitj_final import IITJKnowledgeOrganizerV2

def unit(unit_id, heading, text, source_file="iitj.json"):
    return {
        "unit_id": unit_id,
        "heading": heading,
        "text": text,
        "tier": "A",
        "source_file": source_file,
        "source_url": "https://www.iitj.ac.in/test",
    }

def paths(plan):
    return {d["path"] for d in plan["documents"]}

def test_new_department_entities_are_supported():
    plan = IITJKnowledgeOrganizerV2().build_plan([
        unit("e1", "Welcome to the Department of Electronics Engineering",
             "Department overview.", "electronics_engineering.json"),
        unit("e2", "Faculty", "Electronics faculty.", "electronics_engineering.json"),
        unit("e3", "Research Areas", "Electronics research.", "electronics_engineering.json"),
    ])
    result = paths(plan)
    assert "departments/electronics_engineering/overview.md" in result
    assert "departments/electronics_engineering/faculty.md" in result
    assert "departments/electronics_engineering/research.md" in result

def test_school_is_not_treated_as_department():
    plan = IITJKnowledgeOrganizerV2().build_plan([
        unit("s1", "Welcome to School of Design",
             "Design school overview.", "school_of_design.json"),
        unit("s2", "M.Des Program",
             "M.Des in Smart Product Design.", "school_of_design.json"),
    ])
    result = paths(plan)
    assert "schools/design/overview.md" in result
    assert "schools/design/programs.md" in result
    assert not any(p.startswith("departments/design/") for p in result)

def test_research_platform_has_own_entity_family():
    plan = IITJKnowledgeOrganizerV2().build_plan([
        unit("q1", "Quantum Information and Computation",
             "Research platform information.",
             "quantum_information_and_computation.json"),
    ])
    assert "research_platforms/quantum_information_and_computation/research.md" in paths(plan)

def test_offices_have_own_entity_family():
    plan = IITJKnowledgeOrganizerV2().build_plan([
        unit("o1", "Welcome to Office of Accounts",
             "Accounts and financial management services.",
             "office_of_accounts.json"),
    ])
    assert "offices_and_administration/office_of_accounts/overview.md" in paths(plan)

def test_admission_beats_program():
    plan = IITJKnowledgeOrganizerV2().build_plan([
        unit("a1", "Admission to M.Tech Program",
             "M.Tech admission eligibility.",
             "mtech_admissions.json"),
    ])
    assert "admissions/mtech_admissions.md" in paths(plan)

def test_btech_program_entity():
    plan = IITJKnowledgeOrganizerV2().build_plan([
        unit("b1", "B.Tech Curriculum",
             "B.Tech curriculum details.",
             "btech_programs.json"),
    ])
    assert "programs/btech/curriculum.md" in paths(plan)

def test_hostel_small_topic_stays_together():
    plan = IITJKnowledgeOrganizerV2().build_plan([
        unit("h1", "Accommodation", "Hostel accommodation.", "hostel.json"),
        unit("h2", "Hostel Rules", "Hostel rules.", "hostel.json"),
        unit("h3", "Dining", "Dining facilities.", "hostel.json"),
    ])
    assert paths(plan) == {"hostel_accommodation/general_information.md"}

def test_training_is_separate_from_degree_programs():
    plan = IITJKnowledgeOrganizerV2().build_plan([
        unit("t1", "Specialized Training in Government e-Marketplace",
             "Two-day professional training program.", "training.json"),
    ])
    assert "training_and_upskilling/training.md" in paths(plan)

def test_health_facility_is_not_generic_infrastructure_only():
    plan = IITJKnowledgeOrganizerV2().build_plan([
        unit("h1", "Welcome To The Health Center, IIT Jodhpur",
             "Round-the-clock health care facilities.", "health_center.json"),
    ])
    assert "research_and_technology_facilities/facilities.md" in paths(plan)

def test_unknown_content_goes_to_named_buffer():
    plan = IITJKnowledgeOrganizerV2().build_plan([
        unit("x1", "Rare IITJ Topic",
             "Legitimate institutional content not covered by a known family.",
             "rare_topic.json"),
    ])
    assert "fallback/knowledge_buffer_general.md" in paths(plan)

def test_lossless_assignment():
    units = [
        unit("a1", "B.Tech Curriculum", "Curriculum", "btech.json"),
        unit("a2", "Office of Accounts", "Finance office", "office_of_accounts.json"),
        unit("a3", "Department of Economics", "Economics department", "economics.json"),
        unit("a4", "Unknown Topic", "Valid content", "unknown.json"),
    ]
    plan = IITJKnowledgeOrganizerV2().build_plan(units)
    assigned = [uid for d in plan["documents"] for uid in d["unit_ids"]]
    assert sorted(assigned) == sorted(u["unit_id"] for u in units)
    assert len(assigned) == len(set(assigned))

def test_deterministic():
    units = [
        unit("d1", "Office of Registrar", "Registrar information", "office_of_registrar.json"),
        unit("d2", "M.Tech Curriculum", "M.Tech curriculum", "mtech.json"),
        unit("d3", "Electrical Engineering Faculty", "EE faculty", "electrical_engineering.json"),
    ]
    organizer = IITJKnowledgeOrganizerV2()
    assert organizer.build_plan(units) == organizer.build_plan(list(reversed(units)))