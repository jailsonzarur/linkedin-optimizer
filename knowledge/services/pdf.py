from pypdf import PdfReader


class ExtractionError(RuntimeError):
    pass


def extract_text(django_file):
    try:
        django_file.open("rb")
        reader = PdfReader(django_file)
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise ExtractionError(f"Could not read that PDF: {exc}") from exc
    finally:
        django_file.close()

    text = "\n".join(pages).strip()
    if not text:
        raise ExtractionError("That PDF has no readable text — it may be a scan.")
    return "\n".join(line.rstrip() for line in text.splitlines() if line.strip())
