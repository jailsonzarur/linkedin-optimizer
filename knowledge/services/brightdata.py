import time

import httpx
from django.conf import settings

TRIGGER_URL = "https://api.brightdata.com/datasets/v3/trigger"
SNAPSHOT_URL = "https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}"


class ScrapeError(RuntimeError):
    pass


class LinkedInScraper:
    def __init__(self, token=None, dataset_id=None, on_event=None):
        self.token = token or settings.BRIGHTDATA_API_TOKEN
        self.dataset_id = dataset_id or settings.BRIGHTDATA_DATASET_ID
        self.on_event = on_event or (lambda name, detail: None)

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def fetch(self, profile_url):
        if not self.token or not self.dataset_id:
            raise ScrapeError("Bright Data credentials are not configured.")

        snapshot_id = self._trigger(profile_url)
        return self._await_snapshot(snapshot_id)

    def _trigger(self, profile_url):
        response = httpx.post(
            TRIGGER_URL,
            headers=self._headers(),
            params={"dataset_id": self.dataset_id, "include_errors": "true"},
            json=[{"url": profile_url}],
            timeout=30,
        )
        if response.status_code >= 400:
            raise ScrapeError(f"Bright Data refused the request ({response.status_code}).")

        snapshot_id = response.json().get("snapshot_id")
        if not snapshot_id:
            raise ScrapeError("Bright Data accepted the request but returned no snapshot.")

        self.on_event("fetch.requested", snapshot_id)
        return snapshot_id

    def _await_snapshot(self, snapshot_id):
        deadline = time.monotonic() + settings.BRIGHTDATA_TIMEOUT_SECONDS
        attempt = 0

        while time.monotonic() < deadline:
            attempt += 1
            response = httpx.get(
                SNAPSHOT_URL.format(snapshot_id=snapshot_id),
                headers=self._headers(),
                params={"format": "json"},
                timeout=60,
            )

            if response.status_code == 200:
                return self._first_profile(response.json())

            if response.status_code == 202:
                self.on_event("fetch.waiting", attempt)
                time.sleep(settings.BRIGHTDATA_POLL_SECONDS)
                continue

            raise ScrapeError(f"Bright Data returned {response.status_code} while collecting.")

        raise ScrapeError("Bright Data took too long. Try again in a few minutes.")

    def _first_profile(self, payload):
        rows = payload if isinstance(payload, list) else [payload]
        rows = [row for row in rows if isinstance(row, dict)]
        if not rows:
            raise ScrapeError("Nothing came back for that URL.")

        row = rows[0]
        if row.get("error") or row.get("warning"):
            raise ScrapeError(str(row.get("error") or row.get("warning")))
        if not row.get("name") and not row.get("experience"):
            raise ScrapeError("That profile came back empty. It may be private.")
        return row


def _company_name(profile):
    company = profile.get("current_company")
    if isinstance(company, dict):
        return company.get("name") or ""
    return profile.get("current_company_name") or ""


def _lines(items, render):
    out = []
    for item in items or []:
        if isinstance(item, dict):
            text = render(item)
            if text and text.strip(" —-"):
                out.append(text)
    return out


def profile_to_text(profile):
    parts = []

    def add(label, value):
        if value:
            parts.append(f"{label}: {value}")

    add("NAME", profile.get("name"))
    add("HEADLINE", profile.get("position") or profile.get("headline"))
    add("LOCATION", profile.get("city") or profile.get("location"))
    add("CURRENT COMPANY", _company_name(profile))
    add("ABOUT", profile.get("about") or profile.get("summary"))

    experiences = _lines(
        profile.get("experience"),
        lambda job: f"\n{job.get('title','')} — {job.get('company') or job.get('company_name','')} — "
                    f"{job.get('duration') or job.get('start_date','')}\n"
                    f"{job.get('description') or job.get('summary') or ''}",
    )
    if experiences:
        parts.append("\nEXPERIENCE")
        parts.extend(experiences)

    for label, key, render in (
        ("EDUCATION", "education",
         lambda e: f"{e.get('degree','')} {e.get('field','')} — {e.get('title') or e.get('institute','')} — "
                   f"{e.get('start_year','')}-{e.get('end_year','')}"),
        ("PROJECTS", "projects",
         lambda e: f"{e.get('title','')} — {e.get('start_date','')} — {e.get('description','')}"),
        ("VOLUNTEERING", "volunteer_experience",
         lambda e: f"{e.get('title','')} — {e.get('subtitle') or e.get('organization','')} — "
                   f"{e.get('duration','')} — {e.get('info') or e.get('description','')}"),
        ("CERTIFICATIONS", "certifications",
         lambda e: f"{e.get('title','')} — {e.get('subtitle','')} — {e.get('meta','')}"),
        ("HONOURS", "honors_and_awards",
         lambda e: f"{e.get('title','')} — {e.get('publication','')} — {e.get('date','')}"),
        ("LANGUAGES", "languages",
         lambda e: f"{e.get('title','')} — {e.get('subtitle','')}"),
    ):
        rendered = _lines(profile.get(key), render)
        if rendered:
            parts.append(f"\n{label}")
            parts.extend(rendered)

    return "\n".join(" ".join(part.split()) if part.strip() else part for part in parts).strip()
