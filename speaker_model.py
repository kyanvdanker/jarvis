import librosa
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def embed(path):
    y, sr = librosa.load(path, sr=16000)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
    return np.mean(mfcc, axis=1)

REFERENCE_FILE = "kyan_reference.wav"
reference_emb = embed(REFERENCE_FILE)

def is_kyan(path):
    test_emb = embed(path)
    sim = cosine_similarity([reference_emb], [test_emb])[0][0]
    return sim > 0.85
