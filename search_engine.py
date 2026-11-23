import math
import time
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from models import StudentProfile


def load_college_database(file_path: str) -> Dict[str, Dict[str, Any]]:
    with open(file_path, "r") as file:
        return json.load(file)


COLLEGE_DATABASE = load_college_database(Path(__file__).parent / "college_database.json")


def compute_academic_index(gpa, max_gpa, test_score, test_max, ap_count, ap_max=10, weights=(0.5, 0.4, 0.1)):
    """Return an academic score from 0 to 100 based on GPA, test performance, and AP/IB rigor."""
    if max_gpa <= 0 or test_max <= 0:
        raise ValueError("max_gpa and test_max must be positive")
    gpa_norm = max(0.0, min(1.0, gpa / max_gpa))
    test_norm = max(0.0, min(1.0, test_score / test_max))
    ap_norm = max(0.0, min(1.0, ap_count / ap_max))
    score = (weights[0] * gpa_norm + weights[1] * test_norm + weights[2] * ap_norm) * 100
    return round(score, 2)


def compute_profile_strength(extracurriculars, leadership_roles=0, awards=0):
    """Translate extracurricular activity, leadership, and accolades into a 0-100 profile score."""
    score = (extracurriculars * 5) + (leadership_roles * 12) + (awards * 15)
    return round(min(100.0, score), 2)


def compute_fit_score(academic_index, location_advantage, budget_score, weights=(0.6, 0.2, 0.2)):
    """Blend academic strength, location fit, and affordability into a single fit score."""
    if not (0 <= location_advantage <= 1 and 0 <= budget_score <= 1):
        raise ValueError("location_advantage and budget_score must be between 0 and 1")
    fit = weights[0] * (academic_index / 100.0) + weights[1] * location_advantage + weights[2] * budget_score
    return round(fit * 100, 2)


def probability_from_z(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def compute_probability_index(student_score, school_avg, school_std):
    """Calculate an admissions probability percentile and classify as Reach/Match/Safety."""
    if school_std <= 0:
        raise ValueError("school_std must be positive")
    z = (student_score - school_avg) / school_std
    p = probability_from_z(z)
    pct = round(p * 100, 2)
    if p < 0.2:
        bucket = "Reach"
    elif p < 0.7:
        bucket = "Match"
    else:
        bucket = "Safety"
    return pct, bucket, round(z, 2)


def _location_match_score(student_location_preference, school_location):
    location = school_location.get("region", "").lower()
    preferred = str(student_location_preference).lower().strip()
    if preferred in {"anywhere", "national", "all"}:
        return 0.7
    if preferred in {"in-state", "state", "regional"}:
        return 0.8 if preferred in {"state", "regional"} else 0.85
    if preferred in {"west", "midwest", "south", "northeast", "east"}:
        return 0.9 if preferred == location else 0.6
    if preferred in {"urban", "rural", "suburban"}:
        return 0.8
    return 0.7


def _budget_score(student_budget, school_cost):
    total_cost = float(school_cost.get("estimated_total", 0) or 0)
    if total_cost <= 0:
        return 1.0
    if student_budget <= 0:
        return 0.1
    gap = total_cost - student_budget
    return round(max(0.0, min(1.0, 1.0 - (gap / max(total_cost, 1))),), 2)


def _major_fit(student_major, school_majors):
    if not student_major:
        return 1.0
    major = str(student_major).lower().strip()
    for school_major in school_majors:
        if major in school_major.lower() or school_major.lower() in major:
            return 1.0
    return 0.7


def _improvement_tips(student, school, academic_index, profile_strength, fit_score, probability_index, bucket):
    tips = []
    college_stats = school["admissions"]
    if student.gpa < college_stats["avg_gpa"]:
        needed = max(student.gpa, 0) + 0.1
        tips.append(f"Raise your GPA from {student.gpa:.2f} to about {college_stats['avg_gpa']:.2f} to compete more comfortably.")
    if student.test_score < college_stats["avg_test"]:
        needed = college_stats["avg_test"]
        tips.append(f"Target a test score around {needed} to better align with the school’s admitted profile.")
    if student.ap_ib_count < college_stats["avg_ap_ib"]:
        tips.append(f"Add a few more AP/IB courses so your rigor reaches around {college_stats['avg_ap_ib']} total classes.")
    if student.extracurriculars < school["profile"]["extracurricular_expectation"]:
        tips.append(f"Build a more standout extracurricular profile; this school typically expects at least {school['profile']['extracurricular_expectation']} strong activities.")
    if student.leadership_roles < school["profile"]["leadership_expectation"]:
        tips.append(f"Increase leadership breadth by taking on roles in clubs, projects, or team leadership.")
    if bucket == "Reach":
        tips.append("Keep applying to ambitious schools, but pair them with a stronger set of Match and Safety options.")
    elif bucket == "Match":
        tips.append("Your profile is competitive; a small boost in rigor or leadership could strengthen your odds.")
    else:
        tips.append("You are in a strong position for this school—keep your current trajectory and continue building depth in your profile.")
    return tips[:4]


def evaluate_school_for_student(student: StudentProfile, school_name: str, data: Dict[str, Dict[str, Any]]):
    if school_name not in data:
        raise KeyError(f"School '{school_name}' was not found in the database.")
    school = data[school_name]
    major_fit = _major_fit(student.intended_major, list(school["majors"].keys()))
    academic_index = compute_academic_index(
        student.gpa,
        4.0,
        student.test_score,
        1600,
        student.ap_ib_count,
    )
    profile_strength = compute_profile_strength(
        student.extracurriculars,
        student.leadership_roles,
        student.awards,
    )
    location_score = _location_match_score(student.location_preference, school["location"])
    budget_score = _budget_score(student.budget, school["cost"])
    fit_score = compute_fit_score(academic_index, location_score, budget_score)
    fit_score = round(fit_score * major_fit, 2)
    school_avg = school["admissions"]["avg_academic_index"]
    school_std = school["admissions"]["std_academic_index"]
    probability, bucket, z_score = compute_probability_index(academic_index, school_avg, school_std)
    tips = _improvement_tips(student, school, academic_index, profile_strength, fit_score, probability, bucket)
    return {
        "name": school_name,
        "location": f"{school['location']['city']}, {school['location']['state']}",
        "acceptance_rate": school["admissions"]["acceptance_rate"],
        "avg_gpa": school["admissions"]["avg_gpa"],
        "avg_test": school["admissions"]["avg_test"],
        "major_fit": major_fit,
        "academic_index": academic_index,
        "profile_strength": profile_strength,
        "fit_score": fit_score,
        "probability_index": probability,
        "classification": bucket,
        "z_score": z_score,
        "budget_score": budget_score,
        "location_score": location_score,
        "tips": tips,
        "school_data": school,
    }


def search_college_database(data: Dict[str, Dict[str, Any]], query: str) -> Tuple[List[Dict[str, Any]], float]:
    """Search the nested college database by name or major and return matches with timing."""
    query_lower = str(query).strip().lower()
    matches: List[Dict[str, Any]] = []
    start = time.perf_counter()

    for school_name, school in data.items():
        school_lower = school_name.lower()
        major_names = list(school.get("majors", {}).keys())
        searchable = [school_lower, school.get("location", {}).get("city", "").lower(), school.get("location", {}).get("state", "").lower()]
        searchable.extend(major.lower() for major in major_names)
        if query_lower and any(query_lower in item for item in searchable):
            matches.append({
                "name": school_name,
                "location": f"{school['location']['city']}, {school['location']['state']}",
                "acceptance_rate": school["admissions"]["acceptance_rate"],
                "avg_gpa": school["admissions"]["avg_gpa"],
                "avg_test": school["admissions"]["avg_test"],
                "majors": major_names,
            })

    elapsed = time.perf_counter() - start
    matches.sort(key=lambda entry: entry["acceptance_rate"])
    return matches, elapsed


def print_school_result(student: StudentProfile, school_name: str, evaluation: Dict[str, Any]) -> None:
    print("\n=== Acceptly school review ===")
    print(f"College: {evaluation['name']}")
    print(f"Location: {evaluation['location']}")
    print(f"Acceptance rate: {evaluation['acceptance_rate'] * 100:.1f}%")
    print(f"Average admitted GPA: {evaluation['avg_gpa']:.2f}")
    print(f"Average admitted test score: {evaluation['avg_test']}")
    print(f"Academic Index: {evaluation['academic_index']}")
    print(f"Profile Strength: {evaluation['profile_strength']}")
    print(f"Fit Score: {evaluation['fit_score']}")
    print(f"Probability Index: {evaluation['probability_index']}% ({evaluation['classification']})")
    print(f"Major fit for {student.intended_major}: {evaluation['major_fit'] * 100:.0f}%")
    print("What you could improve:")
    for tip in evaluation["tips"]:
        print(f"- {tip}")


def prompt_numeric(label, default, cast, *, min_value=None, max_value=None):
    """Prompt for a numeric value and keep asking until the input is valid."""
    while True:
        try:
            raw = input(f"{label} [{default}]: ").strip()
        except EOFError:
            print("Invalid input. Please enter a valid number.")
            return default
        except KeyboardInterrupt:
            print("\nInput cancelled. Using the default value.")
            return default

        if raw == "":
            print("Blank input. Using the default value.")
            return default

        try:
            value = cast(raw)
        except (TypeError, ValueError):
            print("Invalid input. Please enter a valid number.")
            continue

        if min_value is not None and value < min_value:
            print(f"Invalid input. Please enter a number greater than or equal to {min_value}.")
            continue
        if max_value is not None and value > max_value:
            print(f"Invalid input. Please enter a number less than or equal to {max_value}.")
            continue
        return value


def build_student_profile_from_prompt():
    print("\nWelcome to Acceptly — your personalized admissions guide")
    print("Enter your profile information below. Press Enter to use the suggested defaults.\n")

    prompt_values = {
        "gpa": 3.8,
        "test_score": 1450,
        "ap_ib_count": 7,
        "extracurriculars": 6,
        "leadership_roles": 2,
        "awards": 1,
        "intended_major": "Computer Science",
        "location_preference": "West",
        "budget": 25000,
    }

    while True:
        intended_major = input(f"Intended major [{prompt_values['intended_major']}]: ").strip()
        if intended_major:
            break
        print("Blank input. Please enter a major or press Enter to use the default.")

    while True:
        location_preference = input(f"Location preference [{prompt_values['location_preference']}]: ").strip()
        if location_preference:
            break
        print("Blank input. Please enter a location preference or press Enter to use the default.")

    return StudentProfile(
        gpa=float(prompt_numeric("GPA", prompt_values["gpa"], float, min_value=0.0, max_value=5.0)),
        test_score=int(prompt_numeric("SAT score", prompt_values["test_score"], int, min_value=400, max_value=1600)),
        ap_ib_count=int(prompt_numeric("AP/IB courses", prompt_values["ap_ib_count"], int, min_value=0, max_value=30)),
        extracurriculars=int(prompt_numeric("Extracurriculars", prompt_values["extracurriculars"], int, min_value=0, max_value=30)),
        leadership_roles=int(prompt_numeric("Leadership roles", prompt_values["leadership_roles"], int, min_value=0, max_value=20)),
        awards=int(prompt_numeric("Awards or honors", prompt_values["awards"], int, min_value=0, max_value=20)),
        intended_major=intended_major or prompt_values["intended_major"],
        location_preference=location_preference or prompt_values["location_preference"],
        budget=float(prompt_numeric("Annual budget", prompt_values["budget"], float, min_value=0.0)),
    )


def run_acceptly_app():
    student = build_student_profile_from_prompt()

    while True:
        try:
            query = input("\nSearch for a college to evaluate (for example: Stanford, Michigan, Florida): ").strip()
        except EOFError:
            print("Invalid input. Please enter a valid search term.")
            return
        except KeyboardInterrupt:
            print("\nInput cancelled. Exiting Acceptly.")
            return

        if query == "":
            print("Blank input. Please enter a college name or keyword.")
            continue
        break

    print(f"\nSearching the nested college database for '{query}'...")
    matches, elapsed = search_college_database(COLLEGE_DATABASE, query)
    print(f"Search completed in {elapsed:.6f} seconds.")

    if not matches:
        print("No exact school matches were found in the nested database. Try a school name or state/region keyword.")
        return

    school_name = matches[0]["name"]
    evaluation = evaluate_school_for_student(student, school_name, COLLEGE_DATABASE)
    print_school_result(student, school_name, evaluation)

    print("\nRelevant majors at this school:")
    for major in matches[0]["majors"][:5]:
        print(f"- {major}")

    print("\nThis result came from the live nested college data, not a hardcoded lookup.")


def main():
    run_acceptly_app()


if __name__ == "__main__":
    main()
