# Profile-to-Recommendation API

Backend take-home for Potens IT Services and Consultancy (Q2). The domain is
**career-program recommendations**: a user sends a structured learner profile
and the API returns the top three eligible catalogue items with plain-language
reasoning for each match.

## What is included

- `POST /recommend` — ranks matching items for a profile with 11 attributes.
- `GET /items`, `POST /items`, `PUT /items/:id`, `DELETE /items/:id` — full CRUD,
  protected by an admin bearer token.
- `GET /explain/:item_id` — explains the eligibility rules for one catalogue
  item in plain language.
- SQLite persistence with a seed script that loads 15 real catalogue items.
- Unit tests for ranking, missing fields, boundary values, no-match behavior,
  and eligibility explanations.

## Project structure

Everything under `app/` is a Python package, so the internal imports
(`from app.database import ...`, etc.) only resolve if the files are actually
nested this way:

```
potens-intern-backend-<yourname>/
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── recommender.py
│   ├── server.py
│   └── validation.py
├── scripts/
│   └── seed.py
├── tests/
│   └── test_recommender.py
├── seed_data.py
├── data/                 (auto-created by the seed script — not committed)
└── README.md
```

## Run locally

Requires Python 3.10 or newer. No third-party packages are required.

```bash
cd potens-intern-backend-<yourname>
python scripts/seed.py
python -m app.server
```

The API runs on `http://127.0.0.1:8000`.

The default admin token is `dev-admin-token`. Override it before starting the
server if needed:

```bash
# macOS/Linux
export ADMIN_TOKEN=your-token
python -m app.server
```
```cmd
:: Windows
set ADMIN_TOKEN=your-token
python -m app.server
```

## Example requests

**Root / service info** (browser-friendly — plain `GET`, no headers needed):
```
http://127.0.0.1:8000/
http://127.0.0.1:8000/health
```

**Recommendation** (needs a POST body — use curl/Postman, not the address bar):

Windows CMD:
```cmd
curl -X POST http://127.0.0.1:8000/recommend ^
  -H "Content-Type: application/json" ^
  -d "{\"age\":21,\"education_level\":\"undergraduate\",\"city\":\"Pune\",\"skills\":[\"python\",\"javascript\",\"html\",\"css\",\"excel\",\"linux\",\"documentation\"],\"experience_months\":8,\"weekly_hours\":16,\"budget_inr\":5000,\"interests\":[\"machine learning\",\"apis\",\"data\",\"ui\"],\"has_laptop\":true,\"available_start_days\":3,\"mode_preference\":\"hybrid\"}"
```

macOS/Linux:
```bash
curl -X POST http://127.0.0.1:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"age":21,"education_level":"undergraduate","city":"Pune","skills":["python","javascript","html","css","excel","linux","documentation"],"experience_months":8,"weekly_hours":16,"budget_inr":5000,"interests":["machine learning","apis","data","ui"],"has_laptop":true,"available_start_days":3,"mode_preference":"hybrid"}'
```

**Admin catalogue (list)** — needs a header, so the browser address bar can't do this alone:
```bash
curl http://127.0.0.1:8000/items -H "Authorization: Bearer dev-admin-token"
```

**Create an item:**
```bash
curl -X POST http://127.0.0.1:8000/items \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-admin-token" \
  -d '{"id":"react-native-sprint","name":"React Native Sprint","category":"Mobile","description":"Two-week mobile app build for undergrads.","min_age":18,"max_age":28,"education_levels":["undergraduate","self-taught"],"cities":["Pune"],"remote_allowed":true,"required_skills":["javascript"],"preferred_skills":["react","mobile"],"min_experience_months":0,"fee_inr":0,"min_weekly_hours":10,"interests":["mobile","ui"],"requires_laptop":true,"starts_within_days":14,"active":true}'
```

**Update an item** — note this is a *full-replace* PUT, not a partial patch
(see "Design decisions" below). Resend every field, not just the one changing:
```bash
curl -X PUT http://127.0.0.1:8000/items/react-native-sprint \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-admin-token" \
  -d '{"name":"React Native Sprint","category":"Mobile","description":"Two-week mobile app build for undergrads.","min_age":18,"max_age":28,"education_levels":["undergraduate","self-taught"],"cities":["Pune","Mumbai"],"remote_allowed":true,"required_skills":["javascript"],"preferred_skills":["react","mobile"],"min_experience_months":0,"fee_inr":0,"min_weekly_hours":10,"interests":["mobile","ui"],"requires_laptop":true,"starts_within_days":14,"active":true}'
```

**Delete an item:**
```bash
curl -X DELETE http://127.0.0.1:8000/items/react-native-sprint -H "Authorization: Bearer dev-admin-token"
```

**Explain one item** (browser-friendly, no auth needed):
```
http://127.0.0.1:8000/explain/backend-api-lab-pune
```

## Run tests

```bash
cd potens-intern-backend-<yourname>
python -m unittest discover -s tests
```

## Design decisions

I separated hard eligibility from ranking. A profile either passes hard rules
— age, education level, location, required skills, budget, weekly time,
laptop access, and start date — or it is rejected with explicit failures.
Only eligible items are scored. This avoids the common recommender mistake
where a high soft score hides a rule violation.

The score is intentionally simple and inspectable: preferred skill overlap,
interest overlap, location fit, mode fit, extra experience, extra weekly
availability, and budget room. In a real audited product I would rather
start with readable deterministic rules than a black-box model.

SQLite is used because the assignment asks for a database and a seed script,
but the project should still run quickly in a fresh review environment. The
HTTP layer uses the Python standard library to avoid dependency setup during
a 24-hour assignment.

`PUT /items/:id` is a full-replace update (it calls the same `upsert_item`
function as create), not a partial patch — the whole object must be resent.
I chose this over building separate patch-merge logic to keep the write path
single and auditable: there's exactly one way an item's row can change,
which matters more to me here than PATCH-style convenience.

## What is broken or unfinished

- The admin token is a simple bearer token, not a full user system.
- The CRUD API validates shape and basic values, but does not yet enforce
  every business invariant a production catalogue editor would need (e.g.
  no check that `min_age <= max_age` beyond what's already in `validate_item`,
  no dedupe on skill/interest casing at write time).
- There is no pagination on `GET /items`.
- `PUT` requires the full object rather than supporting partial patches —
  documented above as a deliberate tradeoff, not an oversight.
- The optional webhook, caching layer, and generated OpenAPI spec are not
  implemented.
- `ThreadingHTTPServer` opens one shared SQLite connection per server process
  and reuses it across request threads. It works fine for this assignment's
  load, but concurrent writes under real traffic could hit SQLite's
  single-writer lock. I'd add a connection-per-request or a lock around
  writes before treating this as production-ready.

## What I would build next

I would add an OpenAPI document, request IDs, structured logs, pagination, a
stronger admin auth story, and a small webhook table for saved profiles. The
webhook would run the same eligibility engine when a new item is added and
notify only users who newly match.

##Screenshots

<img width="1366" height="768" alt="image" src="https://github.com/user-attachments/assets/facf1955-de94-40c9-97dc-6501cd4bf641" />


<img width="1366" height="768" alt="image" src="https://github.com/user-attachments/assets/b593ee32-bbf4-4414-b148-7e18590213b3" />


<img width="1366" height="768" alt="image" src="https://github.com/user-attachments/assets/5429f774-4f2c-4a95-87b0-fd9979cab077" />


## AI use log

- Google AI Studio** — approximately 12-15 messages. Used for handling errors.
  
- Claude  — approximately 15–20 messages Used for
  planning, implementation, test creation, and initial README drafting across one
  debugging session. Used to: diagnose a `ModuleNotFoundError: No module
  named 'app'` caused by the project files not being nested inside an `app/`
  package folder; verify the fix by actually running the seed script, full
  test suite, and live server and draft this updated README.
