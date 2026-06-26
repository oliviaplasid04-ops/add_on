def generate_response(name: str, complaint: str, category: str, sentiment: str, priority: str, model) -> str:
    prompt = f"""You are a professional customer service agent writing a reply to a complaint.

Customer name: {name}
Complaint: {complaint}
Category: {category}
Sentiment: {sentiment}
Priority: {priority}

Write a short (3-4 sentences), polite, and empathetic response to this customer.
- Address them by their first name
- Acknowledge their issue
- Tell them what action will be taken
- If priority is High, mention it will be escalated urgently
Do NOT mention internal labels like sentiment or priority in your reply.

Response:"""
    response = model.generate_content(prompt)
    return response.text.strip()
