def summarize(tickets: list[dict], prefix: str | None = None, seen=[]) -> str:
    result = ""
    for t in tickets:
        if t["id"] in seen:
            continue
        seen.append(t["id"])
        if "subject" in t.keys():
            result = result + (prefix or "") + t["subject"] + "\n"
    return result
