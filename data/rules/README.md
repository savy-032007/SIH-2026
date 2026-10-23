# Validation rule sets

One JSON file per academic year, validated by `app.rules.schema.RuleSetConfig` and
loaded into the `rule_set` table by `make seed`. The AICTE Rules Manager (Phase 4)
edits them in the database; these files are the committed starting point.

| File | Supernumerary slab | Why it exists |
|---|---|---|
| `rules_2025_26.json` | single 15 % across all levels and programs | the pre-2026-27 regime, so the year switch is demonstrable |
| `rules_2026_27.json` | 15 % UG/diploma engineering, 25 % PG engineering and all management/design/other-technical | current, and the active set after seeding |

## Unverified facts — do not harden these without a source

SPEC section 7 marks these ⚠. They are configuration, never constants in code,
and each carries a `TODO(verify)` at its definition in `app/rules/schema.py`:

- **`ciwgc_fraction_of_supernumerary`** (0.3333) — whether the one-third CIWGC
  sub-pool split survived the 2026-27 Approval Process Handbook rewrite is not
  confirmed.
- **`ciwgc_vacancy_transfer`** (true) — whether unfilled CIWGC seats transfer to
  the wider supernumerary pool.
- **`oci_foreign_cutoff_date`** (2021-03-04) — the OCI card issue date on or after
  which a student counts as foreign for seat classification.
- **`supernumerary_pct`** — the 2026-27 slabs above, and the handbook's statement
  that supernumerary seats are exclusively for international students.
- **APAAR ID checksum** — no official spec is known, so `V2.FORMAT` checks length
  and digits only. Inventing a checksum would reject valid real IDs.

When any of these is confirmed against the Approval Process Handbook, update the
JSON (and the `TODO(verify)` comment), not the rule code.
