def classify_text(text: str, provider: str = "") -> str:
    t = text.lower()

    if any(x in t for x in ["aufgabe:", "- [ ]", "todo", "erledigen", "nächster schritt"]):
        return "task"
    if any(x in t for x in ["projekt", "masterplan", "roadmap", "sprint", "backlog", "release", "mvp"]):
        return "project"
    if any(x in t for x in ["kontakt", "person:", "ansprechpartner", "stakeholder"]):
        return "person"
    if any(x in t for x in ["http://", "https://", "quelle", "artikel", "recherche", "youtube", "perplexity"]):
        return "source"
    if any(x in t for x in ["definition", "konzept", "architektur", "erklärung", "entscheidung", "wissen"]):
        return "knowledge"

    if provider in ["Perplexity", "Webseiten", "YouTube", "PDFs", "Emails"]:
        return "source"

    return "inbox"
