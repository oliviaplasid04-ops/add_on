def intake(name: str, complaint: str) -> dict:
    if not name.strip() or not complaint.strip():
        raise ValueError("Name and complaint cannot be empty.")
    return {"name": name.strip(), "complaint": complaint.strip()}
