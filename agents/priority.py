def assess_priority(complaint: str, sentiment: str, model) -> str:
    prompt = f"""You are a priority assessment agent for customer complaints.
Based on the complaint and its sentiment, reply with ONLY one word: High, Medium, or Low.

Rules:
- High: threats, legal mentions, safety issues, extreme anger, urgent unresolved issues
- Medium: moderate frustration, pending issues needing follow-up
- Low: general feedback, minor inconveniences, neutral tone

Complaint: {complaint}
Sentiment: {sentiment}
Priority:"""
    response = model.generate_content(prompt)
    priority = response.text.strip()
    for level in ["High", "Medium", "Low"]:
        if level.lower() in priority.lower():
            return level
    return "Medium"
