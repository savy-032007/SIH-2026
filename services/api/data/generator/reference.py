"""Real-world reference data for the synthetic generator (SPEC 9.1, 9.2).

Place names, boards and course titles are real; every institution, student and
APAAR ID built from them is invented. SPEC 9.1 prefers a genuine AICTE
approved-institutions list, but the consolidated list is published behind
institution logins and SPEC section 0 forbids scraping those, so institutions are
generated instead. Drop a real CSV into `/data/reference/institutions.csv` and the
seeder will use it (see that directory's README).

States were chosen to span four AICTE regions with Maharashtra included, as the
demo script needs it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StateRef:
    name: str
    #: AICTE regional office covering this state.
    region: str
    districts: tuple[str, ...]
    #: Dominant school board, used for realistic qualifying_board values.
    state_board: str
    #: Rough centroid, for the national choropleth in Phase 3.
    lat: float
    lng: float


STATES: tuple[StateRef, ...] = (
    StateRef(
        name="Maharashtra",
        region="WESTERN",
        districts=(
            "Pune",
            "Mumbai Suburban",
            "Nagpur",
            "Nashik",
            "Thane",
            "Chhatrapati Sambhajinagar",
            "Solapur",
            "Kolhapur",
            "Amravati",
            "Satara",
        ),
        state_board="MSBSHSE",
        lat=19.7515,
        lng=75.7139,
    ),
    StateRef(
        name="Karnataka",
        region="SOUTH_WESTERN",
        districts=(
            "Bengaluru Urban",
            "Mysuru",
            "Belagavi",
            "Dharwad",
            "Dakshina Kannada",
            "Tumakuru",
            "Kalaburagi",
            "Shivamogga",
        ),
        state_board="KSEEB",
        lat=15.3173,
        lng=75.7139,
    ),
    StateRef(
        name="Tamil Nadu",
        region="SOUTHERN",
        districts=(
            "Chennai",
            "Coimbatore",
            "Madurai",
            "Tiruchirappalli",
            "Salem",
            "Erode",
            "Vellore",
            "Thanjavur",
        ),
        state_board="TNBSE",
        lat=11.1271,
        lng=78.6569,
    ),
    StateRef(
        name="Uttar Pradesh",
        region="NORTHERN",
        districts=(
            "Lucknow",
            "Kanpur Nagar",
            "Varanasi",
            "Prayagraj",
            "Ghaziabad",
            "Gautam Buddha Nagar",
            "Meerut",
            "Agra",
        ),
        state_board="UPMSP",
        lat=26.8467,
        lng=80.9462,
    ),
)

STATES_BY_NAME: dict[str, StateRef] = {state.name: state for state in STATES}


#: Course titles by (level, program). Real AICTE-approved programme names.
COURSE_CATALOGUE: dict[tuple[str, str], tuple[str, ...]] = {
    ("UG", "ENGINEERING"): (
        "Computer Science and Engineering",
        "Information Technology",
        "Electronics and Communication Engineering",
        "Mechanical Engineering",
        "Civil Engineering",
        "Electrical Engineering",
        "Artificial Intelligence and Data Science",
        "Chemical Engineering",
        "Robotics and Automation",
    ),
    ("UG", "MANAGEMENT"): (
        "Bachelor of Business Administration",
        "Bachelor of Management Studies",
    ),
    ("UG", "DESIGN"): (
        "Bachelor of Design",
        "Industrial Design",
    ),
    ("UG", "OTHER_TECH"): (
        "Bachelor of Computer Applications",
        "Bachelor of Pharmacy",
        "Bachelor of Hotel Management and Catering Technology",
    ),
    ("PG", "ENGINEERING"): (
        "Computer Science and Engineering",
        "Structural Engineering",
        "VLSI Design and Embedded Systems",
        "Thermal Engineering",
        "Power Systems",
    ),
    ("PG", "MANAGEMENT"): (
        "Master of Business Administration",
        "Post Graduate Diploma in Management",
    ),
    ("PG", "DESIGN"): ("Master of Design",),
    ("PG", "OTHER_TECH"): (
        "Master of Computer Applications",
        "Master of Pharmacy",
    ),
    ("DIPLOMA", "ENGINEERING"): (
        "Diploma in Computer Engineering",
        "Diploma in Mechanical Engineering",
        "Diploma in Civil Engineering",
        "Diploma in Electrical Engineering",
        "Diploma in Electronics and Telecommunication Engineering",
    ),
    ("DIPLOMA", "MANAGEMENT"): ("Diploma in Business Management",),
    ("DIPLOMA", "DESIGN"): ("Diploma in Interior Design",),
    ("DIPLOMA", "OTHER_TECH"): (
        "Diploma in Pharmacy",
        "Diploma in Hotel Management",
    ),
}

#: Approved intakes AICTE actually grants (SPEC 9.2).
INTAKE_OPTIONS: tuple[int, ...] = (30, 60, 120, 180)

INSTITUTION_NAME_PREFIXES: tuple[str, ...] = (
    "Shri",
    "Shree",
    "Sant",
    "Rajarshi",
    "Maharaja",
    "Vidya",
    "Gyan",
    "Pragati",
    "Sahyadri",
    "Anand",
    "Bharati",
    "Jagruti",
    "Navjeevan",
    "Siddhartha",
    "Vivekanand",
    "Lokmanya",
    "Yashwant",
    "Narayan",
    "Shivaji",
    "Kaveri",
)

INSTITUTION_NAME_CORES: tuple[str, ...] = (
    "Institute of Technology",
    "College of Engineering",
    "Institute of Engineering and Technology",
    "School of Management",
    "Institute of Management Studies",
    "Polytechnic",
    "Institute of Design",
    "College of Technology",
    "Academy of Technology",
    "Institute of Science and Technology",
)

#: Deliberately regional, because Faker('en_IN') alone skews towards one register
#: and the ghost-cluster and name-match plants need variety to be convincing.
FIRST_NAMES_MALE: tuple[str, ...] = (
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Krishna",
    "Ishaan", "Rohan", "Siddharth", "Karthik", "Pranav", "Rahul", "Nikhil",
    "Omkar", "Tanmay", "Harsh", "Yash", "Atharva", "Soham", "Shreyas", "Kunal",
    "Mahesh", "Ganesh", "Sandeep", "Prathamesh", "Rudra", "Advait", "Darshan",
    "Mohammed", "Imran", "Faizan", "Zaid", "Arnav", "Devansh", "Lakshya",
    "Murugan", "Senthil", "Dinesh", "Bharath", "Ashwin", "Naveen", "Gokul",
)

FIRST_NAMES_FEMALE: tuple[str, ...] = (
    "Aadhya", "Ananya", "Diya", "Saanvi", "Aarohi", "Anika", "Navya", "Kiara",
    "Myra", "Sara", "Ishita", "Riya", "Shreya", "Pooja", "Sneha", "Aditi",
    "Meera", "Nandini", "Tanvi", "Gauri", "Rutuja", "Shruti", "Sakshi",
    "Prachi", "Vaishnavi", "Harini", "Kavya", "Deepika", "Lakshmi", "Divya",
    "Fatima", "Ayesha", "Zoya", "Nikita", "Apurva", "Mrunal", "Janhvi",
    "Keerthana", "Swathi", "Nithya", "Revathi", "Bhavana", "Charulata",
)

SURNAMES: tuple[str, ...] = (
    "Sharma", "Verma", "Patel", "Shah", "Deshmukh", "Patil", "Kulkarni",
    "Joshi", "Gokhale", "Chavan", "Jadhav", "More", "Shinde", "Pawar",
    "Bhosale", "Kadam", "Gaikwad", "Sawant", "Naik", "Hegde", "Shetty",
    "Rao", "Reddy", "Nair", "Menon", "Pillai", "Iyer", "Iyengar",
    "Krishnan", "Subramanian", "Balakrishnan", "Murugan", "Venkatesh",
    "Singh", "Yadav", "Mishra", "Tiwari", "Dubey", "Pandey", "Srivastava",
    "Agarwal", "Gupta", "Khan", "Siddiqui", "Ansari", "Qureshi", "Sheikh",
)

GUARDIAN_SUFFIXES: tuple[str, ...] = ("Sharma", "Patil", "Reddy", "Singh", "Nair")

#: Street-name fragments for synthetic addresses.
STREET_NAMES: tuple[str, ...] = (
    "MG Road", "Station Road", "FC Road", "Nehru Nagar", "Gandhi Chowk",
    "Shivaji Nagar", "Model Colony", "Civil Lines", "Ring Road",
    "Industrial Estate Road", "Tilak Road", "Kothrud Lane", "Anna Salai",
    "Brigade Road", "Hazratganj", "Sadar Bazaar",
)

#: Overseas countries for FN, NRI and OCI students.
FOREIGN_COUNTRIES: tuple[tuple[str, str], ...] = (
    ("Nepalese", "Nepal"),
    ("Bhutanese", "Bhutan"),
    ("Sri Lankan", "Sri Lanka"),
    ("Bangladeshi", "Bangladesh"),
    ("Afghan", "Afghanistan"),
    ("Nigerian", "Nigeria"),
    ("Kenyan", "Kenya"),
    ("Emirati", "United Arab Emirates"),
    ("Omani", "Oman"),
    ("Malaysian", "Malaysia"),
)

#: Boards a genuinely foreign-qualified student would present.
FOREIGN_BOARDS: tuple[str, ...] = ("FOREIGN", "IB", "CAIE")


def email_domains() -> tuple[str, ...]:
    return ("gmail.com", "yahoo.co.in", "outlook.com", "rediffmail.com", "hotmail.com")
