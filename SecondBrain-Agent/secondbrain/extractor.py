def extract_tasks(text: str) -> list[str]:
    tasks = []
    for line in text.splitlines():
        l = line.strip()
        if not l:
            continue
        low = l.lower()

        if low.startswith("- [ ]"):
            tasks.append(l[5:].strip())
        elif "aufgabe:" in low:
            tasks.append(l.split(":", 1)[-1].strip())
        elif low.startswith("todo:"):
            tasks.append(l.split(":", 1)[-1].strip())
        elif low.startswith("nächster schritt:"):
            tasks.append(l.split(":", 1)[-1].strip())

    cleaned = []
    for task in tasks:
        task = task.strip("- ").strip()
        if task and task not in cleaned:
            cleaned.append(task)
    return cleaned

def extract_decisions(text: str) -> list[str]:
    decisions = []
    markers = ["entscheidung:", "beschluss:", "festlegung:"]
    for line in text.splitlines():
        l = line.strip()
        low = l.lower()
        for marker in markers:
            if marker in low:
                value = l.split(":", 1)[-1].strip()
                if value and value not in decisions:
                    decisions.append(value)
    return decisions
