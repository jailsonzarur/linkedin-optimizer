# LinkedIn Optimizer

An open-source platform to analyze and optimize a LinkedIn profile,
helping tech professionals get found by more recruiters.

The platform is built around three pieces of context, combined at
analysis time:

1. **A knowledge base per user** — experiences, skills, and achievements
   captured from audio, pasted text, or an uploaded résumé, indexed for
   semantic retrieval rather than forced into a rigid résumé schema.
2. **A corpus of real job postings** for common tech roles, kept fresh on
   a recurring schedule so gap analysis has current market signal to
   compare against.
3. **The user's actual LinkedIn profile**, pulled in at analysis time and
   scored section by section.

Combining the three, the platform generates a rewritten headline, About
section, and experience bullets — grounded strictly in what the user's
own knowledge base supports, never inventing skills or experience, just
restructuring for how recruiters actually search.

## Status

Data model in place across all four apps (`accounts`, `knowledge`,
`jobs`, `analysis`) and migrated end to end, including `pgvector`
embedding columns. No ingestion pipeline, parsing logic, job-scraping
task, or LLM analysis pipeline exist yet — those are next.

## Stack

- **Django 6**, server-rendered templates + [HTMX](https://htmx.org/) +
  [Alpine.js](https://alpinejs.dev/) — no separate frontend build
- **PostgreSQL 16** with [`pgvector`](https://github.com/pgvector/pgvector)
  — relational data alongside embedding columns for semantic retrieval
  over the user's knowledge base and the job-postings corpus
- **Celery + Redis** — the analysis pipeline runs as a background job,
  not inline in the request/response cycle
- **[OpenAI API](https://platform.openai.com/docs/)** — an LLM for
  analysis and rewrite generation, `text-embedding-3-small` (1536
  dimensions) for embeddings
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

Each Django app is one feature domain. Inside an app, code is layered — the
layer a file lives in tells you what it is allowed to do:

```
analysis/                      # one feature domain
  models.py                    # fields, Meta, __str__, validation — nothing heavy
  urls.py
  admin.py

  selectors/                   # READS: queries that build what a view renders
    result.py                  #   get_result_context(pk)

  services/                    # WRITES + business rules
    diffing.py                 #   inline_diff()
    scoring.py                 #   score_tone()

  views/                       # thin: call a selector/service, return a response
    result.py

  templates/analysis/          # templates belong to the app that renders them
  management/commands/
  tests/
```

Project-level directories hold only what is genuinely shared:

```
config/
  settings/
    base.py   # shared settings, loads .env via django-environ
    dev.py    # DEBUG=True, local-only additions
    prod.py   # security hardening (HSTS, secure cookies, SSL redirect)
  celery.py
  urls.py
templates/
  base.html
  components/   # reusable UI partials (_btn, _icon, _meter, _pill, _topbar)
static/css/     # design system: tokens.css, base.css, components.css
```

### The rules

1. **Selectors read, services write.** Every query a view needs is a selector;
   every operation that changes state or applies a domain rule is a service.
   "Where does this function go?" always has one of those two answers.
2. **Views stay thin.** Receive the request, call a selector or service, render.
   A business-rule `if` inside a view belongs in a service.
3. **Models stay thin.** Fields, `Meta`, `__str__`, `clean()`. No fat query
   methods — those are selectors.
4. **Flat until it hurts.** `models.py` stays a single module while it is small;
   it becomes a `models/` package when it passes roughly 200 lines. Do not
   create a package for one file.

Settings are split by environment (`dev.py` / `prod.py`) instead of branching on
`DEBUG` inside a single file, so environment differences are explicit at the
file level.

## Tests

```bash
uv run python manage.py test
```

## Development data

The ingestion pipeline does not exist yet, so a management command seeds one
fully-populated analysis to develop the result screen against:

```bash
uv run python manage.py seed_demo
```

It prints the URL of the analysis it created.

## Roadmap

- [x] Data model across all four apps, migrated with `pgvector` support
- [ ] Knowledge base ingestion: audio transcription, résumé parsing,
      pasted text → `KnowledgeChunk` extraction
- [ ] `IdentityVariation` generation from headline + knowledge base
- [ ] Job-postings scraper + recurring Celery Beat schedule
- [ ] Semantic retrieval of relevant job postings per user (gap analysis)
- [ ] LLM-based profile analysis pipeline (completeness, headline, About,
      experience bullets) running via Celery
- [ ] Rewrite suggestions with before/after diff
- [ ] Web UI (Django templates + HTMX)

## License

[MIT](LICENSE)
