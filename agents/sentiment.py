def analyze_sentiment(complaint: str, model) -> str:
    prompt = f"""You are a sentiment analysis agent.
Read the complaint below and reply with ONLY one word from this list:
Angry, Frustrated, Disappointed, Neutral, Concerned

Complaint: {complaint}
Sentiment:"""
    response = model.generate_content(prompt)
    sentiment = response.text.strip()
    valid = ["Angry", "Frustrated", "Disappointed", "Neutral", "Concerned"]
    for v in valid:
        if v.lower() in sentiment.lower():
            return v
    return "Neutral"
