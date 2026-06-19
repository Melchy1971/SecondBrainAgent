KEYWORD_TAGS = {
    "obsidian": "obsidian",
    "claude": "claude",
    "chatgpt": "chatgpt",
    "gemini": "gemini",
    "perplexity": "perplexity",
    "python": "python",
    "mcp": "mcp",
    "docker": "docker",
    "postgres": "postgresql",
    "jarvis": "jarvis",
    "wissensdatenbank": "wissensdatenbank",
    "secondbrain": "secondbrain",
    "pdf": "pdf",
    "youtube": "youtube",
    "email": "email",
    "automation": "automation",
}

def generate_tags(text: str, limit: int = 5) -> list[str]:
    t = text.lower()
    out = []
    for k, v in KEYWORD_TAGS.items():
        if k in t and v not in out:
            out.append(v)
        if len(out) >= limit:
            break
    return out
