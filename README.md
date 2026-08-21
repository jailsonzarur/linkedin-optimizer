# LinkedIn Optimizer

An open-source platform to analyze and optimize a LinkedIn profile,
helping tech professionals get found by more recruiters.

A user submits their profile (PDF export or pasted text). The platform
parses it, runs it through an LLM-based analysis pipeline, and returns a
structured breakdown — completeness, headline strength, About section
quality, experience bullets — plus a rewritten version of the weak spots.
A planned gap-analysis stage compares the profile's vocabulary against a
corpus of real job postings for the user's target role, to surface
missing keywords a recruiter's search would otherwise filter out on.

## Status

Early scaffold stage. The Django project, async task infrastructure, and
local dev environment are wired up and working end to end. No domain
models, parsing logic, or analysis pipeline exist yet — those come after
the feature set is fully scoped, so the data model is designed once
instead of migrated repeatedly.

## Stack

- **Django 6**, server-rendered templates + [HTMX](https://htmx.org/) +
  [Alpine.js](https://alpinejs.dev/) — no separate frontend build
- **PostgreSQL 16** with [`pgvector`](https://github.com/pgvector/pgvector)
  — relational data now, embeddings for the job-postings RAG corpus later
- **Celery + Redis** — the analysis pipeline runs as a background job,
  not inline in the request/response cycle
- **[Anthropic API](https://docs.anthropic.com/)** for the analysis and
  rewrite generation
- **[`uv`](https://docs.astral.sh/uv/)** for dependency management

## Local setup

Requirements: Python 3.13+, Docker, [`uv`](https://docs.astral.sh/uv/).

```bash
cp .env.example .env
# generate your own value for DJANGO_SECRET_KEY, e.g.:
uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

docker compose up -d      # starts Postgres and Redis
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

The app runs at `http://127.0.0.1:8000`, admin at `/admin/`.

If ports 5432 or 6379 are already taken on your machine, set
`POSTGRES_PORT` / `REDIS_PORT` in `.env` before running `docker compose up`
— `docker-compose.yml` reads them with 5432/6379 as defaults.

Celery worker (once the project has tasks):

```bash
uv run celery -A config worker -l info
```

## Project structure

```
config/
  settings/
    base.py   # shared settings, loads .env via django-environ
    dev.py    # DEBUG=True, local-only additions
    prod.py   # security hardening (HSTS, secure cookies, SSL redirect)
  celery.py   # Celery app definition
  urls.py
templates/    # project-wide Django templates
static/       # project-wide static assets
```

Settings are split by environment (`dev.py` / `prod.py`) instead of
branching on `DEBUG` inside a single file, so environment differences are
explicit at the file level.

## Roadmap

- [ ] Domain models: profile, experience, education, skills
- [ ] PDF / pasted-text parser into the normalized profile schema
- [ ] LLM-based analysis pipeline (completeness, headline, About,
      experience bullets) running via Celery
- [ ] Job-postings corpus + keyword gap analysis (RAG over `pgvector`)
- [ ] Rewrite suggestions with before/after diff
- [ ] Web UI (Django templates + HTMX)

## License

[MIT](LICENSE)
