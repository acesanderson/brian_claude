# Wellville — Health Subskill

## Project location
`~/wellville/health/`

## Structure
```
health/
├── health.yaml          ← current state: providers, conditions, baselines
├── todos.md             ← appointments to schedule, follow-ups, open items
├── log/                 ← visit notes, lab results, health events (chronological)
└── medical_history/     ← reference docs (stable facts)
    ├── diagnoses.md
    ├── medications.md
    ├── allergies.md
    ├── surgeries.md
    ├── immunizations.md
    └── family_history.md
```

## health.yaml fields
- **providers**: name, specialty, phone, portal URL, last seen
- **conditions**: name, status (active/monitoring/resolved), diagnosed date, notes
- **baselines**: personal reference values from most recent labs (BP, HR, weight, cholesterol, A1C, etc.)

## Log usage
Add dated entries to `log/` for:
- Appointment notes and outcomes
- Lab results
- Any new diagnoses, medication changes, or referrals

File naming: `YYYY-MM-DD_topic.md`

## Todos
`todos.md` tracks:
- Appointments to schedule
- Follow-ups with providers
- Prescriptions to refill
- Things to research

## Bootstrap checklist (one-time setup)
- [ ] Add known providers to health.yaml
- [ ] Add current/past conditions to health.yaml and medical_history/diagnoses.md
- [ ] Add current medications to medical_history/medications.md
- [ ] Add known allergies to medical_history/allergies.md
- [ ] Add surgeries/procedures to medical_history/surgeries.md
- [ ] Add immunization records to medical_history/immunizations.md
- [ ] Add relevant family history to medical_history/family_history.md
- [ ] Populate baselines in health.yaml from most recent labs
