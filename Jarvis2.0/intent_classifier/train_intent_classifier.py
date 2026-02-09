import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import pickle

def train():
    # Load dataset
    df = pd.read_csv("intent_classifier/intent_data.csv")

    X = df["text"]
    y = df["intent"]

    # Vectorizer
    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1
    )

    X_vec = vectorizer.fit_transform(X)

    # Model
    model = LogisticRegression(max_iter=200)
    model.fit(X_vec, y)

    # Save both
    with open("intent_classifier/intent_model.pkl", "wb") as f:
        pickle.dump(model, f)

    with open("intent_classifier/intent_vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)

    print("Training complete.")

train()
