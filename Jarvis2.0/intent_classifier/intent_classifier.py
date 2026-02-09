import pickle
import numpy as np

with open("intent_classifier/intent_model.pkl", "rb") as f:
    model = pickle.load(f)

with open("intent_classifier/intent_vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

def classify_intent_ml(text):
    X = vectorizer.transform([text])
    probs = model.predict_proba(X)[0]
    intents = model.classes_

    # Best intent
    idx = np.argmax(probs)
    return intents[idx], probs[idx], sorted(
        zip(intents, probs),
        key=lambda x: x[1],
        reverse=True
    )
