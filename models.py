"""Data models used by the Acceptly admissions application."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StudentProfile:
    """Academic and personal preferences for a college applicant."""

    gpa: float
    test_score: int
    ap_ib_count: int
    extracurriculars: int
    leadership_roles: int = 0
    awards: int = 0
    intended_major: str = "Undecided"
    location_preference: str = "Anywhere"
    budget: float = 0.0

    def __post_init__(self) -> None:
        self.gpa = float(self.gpa)
        self.test_score = int(self.test_score)
        self.ap_ib_count = int(self.ap_ib_count)
        self.extracurriculars = int(self.extracurriculars)
        self.leadership_roles = int(self.leadership_roles)
        self.awards = int(self.awards)
        self.intended_major = str(self.intended_major).strip() or "Undecided"
        self.location_preference = str(self.location_preference).strip() or "Anywhere"
        self.budget = float(self.budget)

        if not 0.0 <= self.gpa <= 5.0:
            raise ValueError("gpa must be between 0.0 and 5.0")
        if not 400 <= self.test_score <= 1600:
            raise ValueError("test_score must be between 400 and 1600")
        if self.ap_ib_count < 0:
            raise ValueError("ap_ib_count cannot be negative")
        if self.extracurriculars < 0:
            raise ValueError("extracurriculars cannot be negative")
        if self.leadership_roles < 0:
            raise ValueError("leadership_roles cannot be negative")
        if self.awards < 0:
            raise ValueError("awards cannot be negative")
        if self.budget < 0:
            raise ValueError("budget cannot be negative")


@dataclass
class Location:
    city: str
    state: str
    region: str


@dataclass
class Cost:
    tuition: float
    room_board: float
    estimated_total: float


@dataclass
class Admissions:
    acceptance_rate: float
    avg_gpa: float
    avg_test: int
    avg_ap_ib: int
    avg_academic_index: float
    std_academic_index: float
    profile_expectation: str = ""


@dataclass
class ProfileExpectation:
    extracurricular_expectation: int
    leadership_expectation: int


@dataclass
class Major:
    name: str
    avg_gpa: float
    avg_test: int
    selectivity: float


@dataclass
class College:
    name: str
    location: Location
    cost: Cost
    admissions: Admissions
    profile: ProfileExpectation
    majors: Dict[str, Major] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "College":
        location = data["location"]
        cost = data["cost"]
        admissions = data["admissions"]
        profile = data["profile"]
        majors = {
            major_name: Major(name=major_name, **major_data)
            for major_name, major_data in data.get("majors", {}).items()
        }
        return cls(
            name=name,
            location=Location(**location),
            cost=Cost(**cost),
            admissions=Admissions(**admissions),
            profile=ProfileExpectation(**profile),
            majors=majors,
        )


@dataclass
class SchoolSearchResult:
    name: str
    location: str
    acceptance_rate: float
    avg_gpa: float
    avg_test: int
    majors: List[str] = field(default_factory=list)


@dataclass
class SchoolEvaluation:
    name: str
    location: str
    acceptance_rate: float
    avg_gpa: float
    avg_test: int
    major_fit: float
    academic_index: float
    profile_strength: float
    fit_score: float
    probability_index: float
    classification: str
    z_score: float
    budget_score: float
    location_score: float
    tips: List[str] = field(default_factory=list)
    school_data: Optional[Dict[str, Any]] = None


# Backward-compatible name used by earlier versions of the project.
Applicant = StudentProfile
