def classify(complaint: str, model) -> str:
    prompt = f"""You are a complaint classification agent.
Read the complaint below and reply with ONLY one word from this list:
Billing, Delivery, Product Quality, Customer Service, Technical, Other

Complaint: {complaint}
Category:"""
    response = model.generate_content(prompt)
    category = response.text.strip()
    valid = ["Billing", "Delivery", "Product Quality", "Customer Service", "Technical", "Other"]
    for v in valid:
        if v.lower() in category.lower():
            return v
    return "Other"
