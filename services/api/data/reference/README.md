# Real reference data (optional drop-in)

SPEC 9.1 prefers a real AICTE approved-institutions subset over generated ones.
The consolidated approved-institutions list is published behind institution
logins, and SPEC section 0 forbids scraping anything behind a login, so the
generator invents institutions by default.

If you obtain a list legitimately — an export from an AICTE login, or an open-data
release — save it here as `institutions.csv` and `make seed` will use it instead
of the generated institutions. Nothing else needs changing.

## Expected columns

| Column | Required | Notes |
|---|---|---|
| `aicte_id` | yes | permanent id, e.g. `1-3482910756` |
| `name` | yes | |
| `state` | yes | must match a state the generator knows, or add it to `data/generator/reference.py` |
| `district` | yes | |
| `region` | yes | one of `NORTHERN`, `SOUTHERN`, `EASTERN`, `WESTERN`, `CENTRAL`, `NORTH_EASTERN`, `SOUTH_WESTERN` |
| `type` | yes | `GOVT`, `PRIVATE` or `DEEMED` |
| `lat` | no | decimal degrees; blank is fine, the map just won't pin it |
| `lng` | no | |

Courses and approved intake stay generated unless you also supply `courses.csv`
with `aicte_id`, `level`, `program`, `name`, `approved_intake`, `academic_year`.

## What must never go in this directory

Real **student** data. Not a sample, not an anonymised extract. The platform is
built and demonstrated on synthetic students only (SPEC section 0), and this
directory is committed to git.
