import streamlit as st

from search_engine import (
    COLLEGE_DATABASE,
    StudentProfile,
    evaluate_school_for_student,
    search_college_database,
)


PERSISTED_KEYS = (
    "gpa", "test_score", "ap_ib_count", "extracurriculars",
    "leadership_roles", "awards", "intended_major",
    "location_preference", "budget", "navigation",
    "school_query", "school_selected", "aha_school_query", "selected_school",
    "perceived_confidence",
)


def persist_widget_values():
    """Store widget values in the URL so they survive a browser refresh."""
    for key in PERSISTED_KEYS:
        if key not in st.session_state:
            continue
        value = st.session_state[key]
        if isinstance(value, float):
            st.query_params[key] = f"{value:.6g}"
        else:
            st.query_params[key] = str(value)


def initial_value(key, default):
    """Read an initial widget value from the URL, falling back to a default."""
    value = st.query_params.get(key)
    return value if value is not None else default


def initial_float(key, default, min_value, max_value):
    try:
        value = float(initial_value(key, default))
        return min(max(value, min_value), max_value)
    except (TypeError, ValueError):
        return default


def initial_int(key, default, min_value, max_value):
    try:
        value = int(float(initial_value(key, default)))
        return min(max(value, min_value), max_value)
    except (TypeError, ValueError):
        return default


def default_student() -> StudentProfile:
    return StudentProfile(
        gpa=3.8,
        test_score=1450,
        ap_ib_count=7,
        extracurriculars=6,
        leadership_roles=2,
        awards=1,
        intended_major="Computer Science",
        location_preference="West",
        budget=25000,
    )


def build_student_from_sidebar() -> StudentProfile:
    with st.sidebar:
        st.header("Student Profile")
        gpa = st.number_input("GPA", min_value=0.0, max_value=5.0,
                              value=initial_float("gpa", 3.8, 0.0, 5.0), step=0.01,
                              key="gpa", on_change=persist_widget_values)
        test_score = st.number_input("SAT/ACT equivalent", min_value=400, max_value=1600,
                                     value=initial_int("test_score", 1450, 400, 1600), step=10,
                                     key="test_score", on_change=persist_widget_values)
        ap_ib_count = st.number_input("AP/IB courses", min_value=0, max_value=30,
                                      value=initial_int("ap_ib_count", 7, 0, 30), step=1,
                                      key="ap_ib_count", on_change=persist_widget_values)
        extracurriculars = st.number_input("Extracurriculars", min_value=0, max_value=30,
                                           value=initial_int("extracurriculars", 6, 0, 30), step=1,
                                           key="extracurriculars", on_change=persist_widget_values)
        leadership_roles = st.number_input("Leadership roles", min_value=0, max_value=20,
                                           value=initial_int("leadership_roles", 2, 0, 20), step=1,
                                           key="leadership_roles", on_change=persist_widget_values)
        awards = st.number_input("Awards / honors", min_value=0, max_value=20,
                                 value=initial_int("awards", 1, 0, 20), step=1,
                                 key="awards", on_change=persist_widget_values)
        intended_major = st.text_input("Intended major",
                                       value=str(initial_value("intended_major", "Computer Science")),
                                       key="intended_major", on_change=persist_widget_values)
        location_options = ["Anywhere", "West", "Midwest", "South", "Northeast", "In-state", "Regional"]
        saved_location = str(initial_value("location_preference", "West"))
        location_index = location_options.index(saved_location) if saved_location in location_options else 1
        location_preference = st.selectbox("Location preference", location_options,
                                           index=location_index, key="location_preference",
                                           on_change=persist_widget_values)
        budget = st.number_input("Annual budget", min_value=0.0,
                                 value=initial_float("budget", 25000.0, 0.0, 1e9), step=1000.0,
                                 key="budget", on_change=persist_widget_values)

    return StudentProfile(
        gpa=float(gpa),
        test_score=int(test_score),
        ap_ib_count=int(ap_ib_count),
        extracurriculars=int(extracurriculars),
        leadership_roles=int(leadership_roles),
        awards=int(awards),
        intended_major=intended_major or "Undecided",
        location_preference=location_preference,
        budget=float(budget),
    )


def render_metric_cards(evaluation):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Academic Index", f"{evaluation['academic_index']}")
    col2.metric("Profile Strength", f"{evaluation['profile_strength']}")
    col3.metric("Fit Score", f"{evaluation['fit_score']}")
    col4.metric("Probability Index", f"{evaluation['probability_index']}%", evaluation["classification"])


def page_overview(student):
    st.title("Acceptly Admissions Planner")
    st.caption("A personalized college-fit assistant modeled on the terminal workflow.")

    query = "Stanford"
    matches, elapsed = search_college_database(COLLEGE_DATABASE, query)
    school_name = matches[0]["name"] if matches else "Stanford University"
    evaluation = evaluate_school_for_student(student, school_name, COLLEGE_DATABASE)

    render_metric_cards(evaluation)

    st.subheader(f"Recommended demo school: {evaluation['name']}")
    st.write(
        f"Search for '{query}' completed in {elapsed:.4f} seconds. "
        f"Current classification: {evaluation['classification']}"
    )

    col1, col2 = st.columns(2)
    with col1:
        st.write("### School snapshot")
        st.write(f"Location: {evaluation['location']}")
        st.write(f"Acceptance rate: {evaluation['acceptance_rate'] * 100:.1f}%")
        st.write(f"Average GPA: {evaluation['avg_gpa']:.2f}")
        st.write(f"Average SAT: {evaluation['avg_test']}")
    with col2:
        st.write("### Improvement ideas")
        for tip in evaluation["tips"]:
            st.write(f"- {tip}")


def page_demo():
    st.title("Quick Demo")
    student = default_student()
    matches, elapsed = search_college_database(COLLEGE_DATABASE, "Stanford")
    school_name = matches[0]["name"] if matches else "Stanford University"
    evaluation = evaluate_school_for_student(student, school_name, COLLEGE_DATABASE)

    render_metric_cards(evaluation)
    st.write(f"Demo student profile: GPA {student.gpa}, SAT {student.test_score}, {student.ap_ib_count} AP/IB courses.")
    st.write(f"Search query: Stanford | Completed in {elapsed:.4f} seconds")

    st.subheader("What this result means")
    st.write(
        f"For a student targeting {student.intended_major}, the current fit score is "
        f"{evaluation['fit_score']} with a probability index of {evaluation['probability_index']}% "
        f"({evaluation['classification']})."
    )

    st.write("### Tips")
    for tip in evaluation["tips"]:
        st.write(f"- {tip}")


def page_school_search(student):
    st.title("School Search")
    query = st.text_input("Search the college database",
                          value=str(initial_value("school_query", "Stanford")),
                          key="school_query", on_change=persist_widget_values)
    matches, elapsed = search_college_database(COLLEGE_DATABASE, query)

    if not matches:
        st.warning("No schools matched your search. Try a school name, state, or major keyword.")
        return

    st.write(f"Search completed in {elapsed:.4f} seconds.")
    school_names = [match["name"] for match in matches[:5]]
    saved_school = str(initial_value("school_selected", school_names[0]))
    selected_index = school_names.index(saved_school) if saved_school in school_names else 0
    selected_school = st.selectbox("Choose a school", school_names, index=selected_index,
                                   key="school_selected", on_change=persist_widget_values)
    selected_match = next((match for match in matches if match["name"] == selected_school), matches[0])
    evaluation = evaluate_school_for_student(student, selected_school, COLLEGE_DATABASE)

    render_metric_cards(evaluation)

    st.subheader(f"School review: {selected_school}")
    st.write(f"Location: {evaluation['location']}")
    st.write(f"Acceptance rate: {evaluation['acceptance_rate'] * 100:.1f}%")
    st.write(f"Academic index: {evaluation['academic_index']}")
    st.write(f"Fit score: {evaluation['fit_score']}")
    st.write(f"Major fit: {evaluation['major_fit'] * 100:.0f}%")

    st.write("### Relevant majors")
    for major in selected_match["majors"][:5]:
        st.write(f"- {major}")

    st.write("### Improvement ideas")
    for tip in evaluation["tips"]:
        st.write(f"- {tip}")


def page_aha_moment(student):
    st.title("Aha! Moment")
    st.caption("Compare the optimism of the claim against the reality the model calculates.")

    query = st.text_input("School to compare",
                          value=str(initial_value("aha_school_query", "Stanford")),
                          key="aha_school_query", on_change=persist_widget_values)
    matches, elapsed = search_college_database(COLLEGE_DATABASE, query)

    if not matches:
        st.warning("No schools matched your search. Try a school name, state, or major keyword.")
        return

    school_names = [match["name"] for match in matches[:5]]
    saved_school = str(initial_value("selected_school", school_names[0]))
    selected_index = school_names.index(saved_school) if saved_school in school_names else 0
    selected_school = st.selectbox("Choose a school", school_names, index=selected_index,
                                   key="selected_school", on_change=persist_widget_values)
    evaluation = evaluate_school_for_student(student, selected_school, COLLEGE_DATABASE)

    perceived_confidence = st.slider("Perceived confidence in this school", 0, 100,
                                     initial_int("perceived_confidence", 80, 0, 100),
                                     key="perceived_confidence", on_change=persist_widget_values)

    claim = (
        f"{student.intended_major} students with a GPA of {student.gpa:.2f} and a test score of {student.test_score} "
        f"can realistically get into {selected_school}."
    )

    left_col, right_col = st.columns(2)

    with left_col:
        st.warning("Initial perception / marketing claim")
        st.markdown(f"**Claim:** {claim}")
        st.write(f"Confidence level: {perceived_confidence}%")
        st.progress(perceived_confidence / 100)
        st.caption("This is the story someone tells themselves before the numbers are checked.")

    with right_col:
        st.success("Hidden Truth / actual consequence")
        st.metric("Probability Index", f"{evaluation['probability_index']}%", evaluation['classification'])
        st.metric("Fit Score", f"{evaluation['fit_score']}")
        st.metric("Academic Index", f"{evaluation['academic_index']}")
        st.progress(min(max(evaluation["probability_index"] / 100, 0.0), 1.0))
        st.markdown(
            f"**Reality check:** {selected_school} is currently a **{evaluation['classification']}** based on the student's profile. "
            f"The model estimates a {evaluation['probability_index']}% chance using academic fit, profile strength, and affordability."
        )

    st.markdown("---")
    st.subheader("What the gap means")
    if evaluation["probability_index"] < 30:
        insight = "This is a stretch target. The idealized story is much stronger than the actual admissions outcome suggests."
    elif evaluation["probability_index"] < 70:
        insight = "This is a realistic but not guaranteed outcome. The perception is somewhat optimistic, but the model sees a credible path."
    else:
        insight = "The story and the data are aligned. This is a strong, practical opportunity based on the current profile."

    st.info(insight)

    st.write("### Improvement ideas")
    for tip in evaluation["tips"]:
        st.write(f"- {tip}")


def main():
    st.set_page_config(page_title="Acceptly", page_icon="🎓", layout="wide")

    with st.sidebar:
        st.title("Acceptly")
        navigation_options = ["Overview", "Demo", "School Search", "Aha! Moment"]
        saved_navigation = str(initial_value("navigation", "Overview"))
        navigation_index = navigation_options.index(saved_navigation) if saved_navigation in navigation_options else 0
        navigation = st.radio("Navigation", navigation_options, index=navigation_index,
                              key="navigation", on_change=persist_widget_values)

    student = build_student_from_sidebar()

    if navigation == "Overview":
        page_overview(student)
    elif navigation == "Demo":
        page_demo()
    elif navigation == "School Search":
        page_school_search(student)
    else:
        page_aha_moment(student)

    persist_widget_values()


if __name__ == "__main__":
    main()
