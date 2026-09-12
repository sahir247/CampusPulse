"""
CampusPulse AI Training & Threshold Calibration Pipeline - Multilingual Edition
Architecture:
1. MPNet Dense Embeddings: sentence-transformers/paraphrase-multilingual-mpnet-base-v2 (768-d)
2. Languages: English, Hindi (Devanagari & Hinglish), Bengali (Bengali script & Benglish)
3. Branch A: LogisticRegression classifier on 768-d embeddings for 7-class campus category prediction.
4. Branch B: Cosine similarity calibration over paired multilingual validation set across thresholds [0.65 - 0.95].
"""

import os
import sys
import json
import torch
import numpy as np
import joblib
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import precision_recall_fscore_support

# Reconfigure stdout for utf-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend.ai.dataset import CAMPUS_TRAINING_DATA, PAIRED_EVALUATION_DATA

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

def run_training_pipeline():
    print("=" * 70)
    print("[PIPELINE] CampusPulse Trilingual MPNet Training & Threshold Calibration")
    print("=" * 70)

    # 1. Device check
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        gpu_name = torch.cuda.get_device_name(0)
        print(f"[OK] Hardware Acceleration: CUDA ENABLED ({gpu_name})")
    else:
        print("[INFO] Hardware: CPU execution")

    # 2. Load Sentence Transformer
    print(f"\n[INFO] Loading multilingual embedding model: {MODEL_NAME} on {device}...")
    embedder = SentenceTransformer(MODEL_NAME, device=device)
    print("[OK] Embedding model ready (768-d dense multilingual representation).")

    # 3. Prepare Dataset
    texts = [item["text"] for item in CAMPUS_TRAINING_DATA]
    labels = [item["category"] for item in CAMPUS_TRAINING_DATA]
    unique_labels = sorted(list(set(labels)))
    print(f"\n[INFO] Multilingual Dataset loaded: {len(texts)} complaints across {len(unique_labels)} categories:")
    for lbl in unique_labels:
        count = sum(1 for l in labels if l == lbl)
        print(f"   * {lbl}: {count} examples (English, Hindi, Bengali)")

    # 4. Extract 768-d MPNet Embeddings
    print("\n[INFO] Generating 768-d dense embeddings for training samples...")
    embeddings = embedder.encode(texts, convert_to_numpy=True, show_progress_bar=False, normalize_embeddings=True)
    print(f"[OK] Extracted embedding matrix shape: {embeddings.shape}")

    # 5. Train Supervised Category Classifier
    print("\n[INFO] Training Multi-Class Logistic Regression on MPNet Embeddings...")
    classifier = LogisticRegression(C=2.0, max_iter=1000, random_state=42)
    
    # 5-fold Stratified Cross Validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(classifier, embeddings, labels, cv=cv)
    print(f"[RESULT] 5-Fold Cross-Validation Accuracy: {cv_scores.mean() * 100:.2f}% (+/- {cv_scores.std() * 100:.2f}%)")

    # Fit final model on all data
    classifier.fit(embeddings, labels)
    print("[OK] Supervised category classifier fitted successfully.")

    # Save classifier bundle
    classifier_artifact = {
        "model_name": MODEL_NAME,
        "classes": list(classifier.classes_),
        "classifier": classifier,
        "embedding_dim": 768,
        "languages": ["English", "Hindi (Devanagari & Hinglish)", "Bengali (Bangla & Benglish)"]
    }
    classifier_path = os.path.join(MODELS_DIR, "category_classifier.joblib")
    joblib.dump(classifier_artifact, classifier_path)
    print(f"[SAVED] Category classifier artifact: {classifier_path}")

    # 6. Empirically Calibrate Duplicate Similarity Threshold
    print("\n[INFO] Calibrating Duplicate Match Threshold on Paired Validation Set (Cross-Lingual)...")
    pair_texts_a = [pair[0] for pair in PAIRED_EVALUATION_DATA]
    pair_texts_b = [pair[1] for pair in PAIRED_EVALUATION_DATA]
    ground_truth = np.array([pair[2] for pair in PAIRED_EVALUATION_DATA])

    emb_a = embedder.encode(pair_texts_a, convert_to_numpy=True, normalize_embeddings=True)
    emb_b = embedder.encode(pair_texts_b, convert_to_numpy=True, normalize_embeddings=True)

    # Cosine similarities
    similarities = np.sum(emb_a * emb_b, axis=1)

    threshold_candidates = [0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90]
    calibration_results = []
    best_threshold = 0.75
    best_f1 = -1.0

    print("\n   Threshold | Precision | Recall | F1-Score | Status")
    print("   " + "-" * 50)

    for th in threshold_candidates:
        preds = (similarities >= th).astype(int)
        prec, rec, f1, _ = precision_recall_fscore_support(ground_truth, preds, average="binary", zero_division=0)
        calibration_results.append({
            "threshold": th,
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1": round(float(f1), 4)
        })
        is_best = f1 > best_f1
        if is_best:
            best_f1 = f1
            best_threshold = th
        status = " <-- Optimal F1" if is_best else ""
        print(f"      {th:0.2f}   |   {prec*100:5.1f}%  | {rec*100:5.1f}% |  {f1*100:5.1f}%  |{status}")

    # Save threshold configuration
    threshold_config = {
        "calibrated_threshold": best_threshold,
        "target_metric": "F1",
        "best_f1": round(float(best_f1), 4),
        "calibration_table": calibration_results,
        "sample_count": len(PAIRED_EVALUATION_DATA),
        "model_name": MODEL_NAME
    }
    config_path = os.path.join(MODELS_DIR, "threshold_config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(threshold_config, f, indent=2)
    print(f"[SAVED] Calibrated threshold config ({best_threshold}): {config_path}")

    print("\n" + "=" * 70)
    print(f"[DONE] Training & Calibration complete! Calibrated Threshold = {best_threshold} (F1: {best_f1 * 100:.1f}%)")
    print("=" * 70)

if __name__ == "__main__":
    run_training_pipeline()
