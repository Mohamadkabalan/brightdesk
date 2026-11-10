def summarize(tickets: list[dict], prefix: str | None = None, seen: set[str] | None = None) -> str:

    if seen is None:  # B006 fix: create a NEW set on every call instead of sharing one default
        seen = set()

    result = ""
    for ticket in tickets:
        if ticket["id"] in seen:
            continue
        seen.add(ticket["id"])
        if "subject" in ticket:
            result += (prefix or "") + ticket["subject"] + "\n"
    return result
