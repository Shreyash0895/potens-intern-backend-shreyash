# Profile-to-Recommendation API

Backend take-home for Potens IT Services and Consultancy. The domain is career-program recommendations: a user sends a structured learner profile and the API returns the top three eligible catalogue items with short reasoning.

## What is included

- `POST /recommend` ranks matching items for a profile with 11 attributes.
- `GET /items`, `POST /items`, `PUT /items/:id`, and `DELETE /items/:id` are protected with an admin bearer token.
- `GET /explain/:item_id` explains the eligibility rules for one catalogue item in plain language.
- SQLite persistence with a seed script that loads 15 real catalogue items.
- Unit tests for ranking, missing fields, boundary values, no-match behavior, and eligibility explanations.

## Run locally

Requires Python 3.10 or newer. No third-party packages are required.

```bash
cd potens-intern-backend-shreyash
python scripts/seed.py
python -m app.server
```

The API runs on `http://127.0.0.1:8000`.

The default admin token is `dev-admin-token`. Override it before starting the server if needed:

```bash
set ADMIN_TOKEN=your-token
python -m app.server
```

## Example requests

Recommendation:

```bash
curl -X POST http://127.0.0.1:8000/recommend ^
  -H "Content-Type: application/json" ^
  -d "{\"age\":21,\"education_level\":\"undergraduate\",\"city\":\"Pune\",\"skills\":[\"python\",\"javascript\",\"html\",\"css\",\"excel\",\"linux\",\"documentation\"],\"experience_months\":8,\"weekly_hours\":16,\"budget_inr\":5000,\"interests\":[\"machine learning\",\"apis\",\"data\",\"ui\"],\"has_laptop\":true,\"available_start_days\":3,\"mode_preference\":\"hybrid\"}"
```

Admin catalogue:

```bash
curl http://127.0.0.1:8000/items -H "Authorization: Bearer dev-admin-token"
```

Explain one item:

```bash
curl http://127.0.0.1:8000/explain/backend-api-lab-pune
```

## Run tests

```bash
cd potens-intern-backend-shreyash
python -m unittest discover -s tests
```

## Design decisions

I separated hard eligibility from ranking. A profile either passes hard rules such as age, education level, location, required skills, budget, weekly time, laptop access, and start date, or it is rejected with explicit failures. Only eligible items are scored. This avoids the common recommender mistake where a high soft score hides a rule violation.

The score is intentionally simple and inspectable: preferred skill overlap, interest overlap, location fit, mode fit, extra experience, extra weekly availability, and budget room. In a real audited product I would rather start with readable deterministic rules than a black-box model.

SQLite is used because the assignment asks for a database and a seed script, but the project should still run quickly in a fresh review environment. The HTTP layer uses the Python standard library to avoid dependency setup during a 24-hour assignment.

## What is broken or unfinished

- The admin token is a simple bearer token, not a full user system.
- The CRUD API validates shape and basic values, but does not yet enforce every business invariant that a production catalogue editor would need.
- There is no pagination on `GET /items`.
- The optional webhook, cache, and generated OpenAPI spec are not implemented.

## What I would build next

I would add an OpenAPI document, request IDs, structured logs, pagination, a stronger admin auth story, and a small webhook table for saved profiles. The webhook would run the same eligibility engine when a new item is added and notify only users who newly match.

## 150-word approach summary

I modelled the assignment as a deterministic eligibility engine plus a transparent ranking layer. The API accepts a learner profile with age, education, city, skills, experience, weekly availability, budget, interests, laptop access, start availability, and mode preference. Catalogue items store hard requirements and softer preference signals. The recommender first rejects anything that violates a hard rule, then scores only eligible items using skill overlap, interest overlap, location fit, mode fit, experience margin, weekly availability, and budget room. Each returned item includes a paragraph explaining why it matched instead of only exposing a number. I chose SQLite and a seed script so reviewers can run the project quickly while still seeing real persistence. I used standard-library Python to avoid dependency friction in a short take-home. The tests focus on the cases most likely to reveal bad modelling: missing fields, boundary eligibility, no-match profiles, required-skill failures, and ranked top-three output.

## AI use log

- Codex in ChatGPT/Codex desktop: approximately 10 messages, used for planning, implementation, test creation, and README drafting.

-Google Studio AI : approzimately 7 messages,used for handling errors
