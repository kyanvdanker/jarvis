def detect_emotion(text):
    text_lower = text.lower()

    # Strong positive cues
    if any(w in text_lower for w in ["happy", "glad", "excited", "joy", "great", "amazing"]):
        return "joy"

    # Strong negative cues
    if any(w in text_lower for w in ["sad", "upset", "depressed", "unhappy"]):
        return "sadness"

    if any(w in text_lower for w in ["angry", "mad", "furious"]):
        return "anger"

    if any(w in text_lower for w in ["scared", "afraid", "terrified"]):
        return "fear"

    return None
