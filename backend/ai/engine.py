import os
import re
import json
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

# Optional PyTorch & SentenceTransformers import with resilient fallback
try:
    import torch
    import joblib
    from sentence_transformers import SentenceTransformer
    DEEP_LEARNING_AVAILABLE = True
except ImportError:
    DEEP_LEARNING_AVAILABLE = False


class CampusPulseAIEngine:
    """
    CampusPulse Unified Deep Semantic AI Engine
    - Dense Multilingual Vector Embeddings: paraphrase-multilingual-mpnet-base-v2 (768-d)
    - Hardware Acceleration: CUDA on NVIDIA GeForce RTX 4050 Laptop GPU (or CPU fallback)
    - Trilingual Support: English, Hindi (Devanagari & Hinglish), Bengali (Bangla & Benglish)
    - Branch A: Supervised LogisticRegression on 768-d embeddings for 7-class category prediction
    - Branch B: Dense Cosine Similarity with empirical calibration for duplicate issue clustering
    - Deterministic Multi-Factor Priority Engine (Urgency + Affected + Recurrence + Age + Category)
    """

    def __init__(self):
        # 1. Device and Model Setup
        self.device = "cuda" if (DEEP_LEARNING_AVAILABLE and torch.cuda.is_available()) else "cpu"
        self.model_name = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
        self.embedder: Optional[Any] = None
        self.classifier_bundle: Optional[Dict[str, Any]] = None
        self.calibrated_threshold: float = 0.65
        self.embedding_cache: Dict[str, np.ndarray] = {}

        # 2. English / Multilingual Stopwords for preprocessing
        self.stopwords = {
            'the', 'a', 'an', 'in', 'on', 'at', 'since', 'for', 'is', 'was', 'and', 'or',
            'of', 'to', 'by', 'from', 'with', 'it', 'my', 'our', 'be', 'has', 'have', 'had',
            'been', 'are', 'were', 'am', 'pm', 'there', 'this', 'that', 'all', 'any', 'both',
            'each', 'few', 'more', 'most', 'other', 'some', 'such', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'up', 'down', 'out', 'off', 'over', 'under',
            'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
            'hai', 'ho', 'tha', 'thi', 'the', 'mein', 'se', 'ko', 'aur', 'par', 'bhi',
            'ache', 'hobe', 'kora', 'theke', 'te', 'er', 'ei', 'shei'
        }

        # 3. Heuristic Keyword Dictionary (Used for location, urgency & fallback)
        self.categories_keywords = {
            "Hostel / Water": [
                "water", "tap", "taps", "faucet", "shower", "flush", "dry", "leak", "leaking",
                "pipe", "plumbing", "bathroom", "washroom", "toilet", "tank", "booster", "pump",
                "hydro", "hostel", "block c", "floor 2", "room", "geyser", "drain",
                "पानी", "नल", "गीजर", "जल", "কল", "বাথরুম", "paani", "jol"
            ],
            "IT / Network": [
                "wifi", "wi-fi", "internet", "network", "ethernet", "router", "lan", "subnet",
                "ping", "packet", "latency", "portal", "login", "lab 3", "terminal", "workstation",
                "turing", "computer", "dns", "gateway", "access point", "वाईफाई", "ওয়াইফাই"
            ],
            "Electrical": [
                "electricity", "power", "light", "lights", "lighting", "bulb", "switch", "wire",
                "spark", "sparking", "short circuit", "fan", "ac", "air conditioner", "stairwell",
                "emergency lighting", "blackout", "corridor", "plug", "socket",
                "बिजली", "चिंगारी", "বিদ্যুৎ", "স্পার্ক"
            ],
            "Food / Mess": [
                "food", "mess", "dining", "meal", "lunch", "dinner", "breakfast", "canteen",
                "cold", "hygiene", "taste", "heater", "bain-marie", "stale", "caterer", "cook",
                "खाना", "मेस", "খাবার", "ডাইনিং"
            ],
            "Sanitation": [
                "garbage", "trash", "dustbin", "cleaning", "dirt", "smell", "odor", "waste",
                "pest", "drain", "drainage", "sweeper", "cockroach", "dirty",
                "कचरा", "बदबू", "ময়লা", "দুর্গন্ধ"
            ],
            "Security": [
                "security", "guard", "theft", "stolen", "lock", "gate", "stranger", "unsafe",
                "harassment", "emergency", "cctv", "camera", "id card",
                "सुरक्षा", "चोरी", "নিরাপত্তা"
            ],
            "Academics / Facilities": [
                "chair", "desk", "bench", "projector", "whiteboard", "marker", "podium",
                "library", "handrail", "staircase", "classroom", "door", "window", "furniture",
                "marks", "syllabus", "exam", "portal", "নম্বর", "পরীক্ষা"
            ]
        }

        # Urgency keywords (multilingual)
        self.critical_keywords = [
            "completely dry", "no water", "outage", "hazard", "fire", "spark", "sparking",
            "pitch dark", "emergency", "flood", "flooding", "burst", "urgent", "danger", "unusable",
            "पानी बंद", "बिल्कुल पानी नहीं", "जल নেই", "चिंगारी", "স্পার্ক", "খুব জরুরি", "danger", "short circuit"
        ]
        self.high_keywords = [
            "exam", "midterm", "stopped", "failed", "broken", "zero pressure", "not working",
            "down", "unable", "blocked", "cut off", "severe", "paani nahi", "jol nei", "net down", "toot gaya"
        ]
        self.medium_keywords = [
            "cold", "slow", "delayed", "flickering", "poor", "low pressure", "intermittent",
            "thanda", "baje"
        ]

        # 4. Initialize Deep Learning Model & Classifier Artifacts
        self._load_models()

    def _load_models(self):
        """Loads SentenceTransformer and the trained category classifier."""
        models_dir = os.path.join(os.path.dirname(__file__), "models")
        classifier_path = os.path.join(models_dir, "category_classifier.joblib")
        config_path = os.path.join(models_dir, "threshold_config.json")

        # Load calibrated threshold config
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.calibrated_threshold = cfg.get("calibrated_threshold", 0.65)
            except Exception as e:
                print(f"[AI Engine] Error loading threshold config: {e}")

        # Load embedding model & classifier
        if DEEP_LEARNING_AVAILABLE:
            try:
                print(f"[AI Engine] Initializing {self.model_name} on {self.device}...")
                self.embedder = SentenceTransformer(self.model_name, device=self.device)
                print(f"[AI Engine] Multilingual MPNet embedder loaded successfully on {self.device}.")

                if os.path.exists(classifier_path):
                    self.classifier_bundle = joblib.load(classifier_path)
                    print(f"[AI Engine] Supervised category classifier loaded successfully from {classifier_path}.")
            except Exception as e:
                print(f"[AI Engine] Initialization warning on {self.device}: {e}. Retrying on CPU...")
                try:
                    self.device = "cpu"
                    self.embedder = SentenceTransformer(self.model_name, device="cpu")
                    if os.path.exists(classifier_path):
                        self.classifier_bundle = joblib.load(classifier_path)
                    print(f"[AI Engine] Multilingual MPNet embedder loaded successfully on CPU.")
                except Exception as e2:
                    print(f"[AI Engine] Deep learning fallback to heuristic mode: {e2}")
                    self.embedder = None
                    self.classifier_bundle = None

    def preprocess(self, text: str) -> str:
        """Clean and normalize student text while preserving Hindi & Bengali Unicode characters."""
        text = text.strip()
        # Mask emails and phone numbers
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        text = re.sub(r'\b\d{10}\b', '[PHONE]', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def get_dense_embedding(self, text: str) -> np.ndarray:
        """Compute 768-d L2-normalized dense embedding using MPNet."""
        if text in self.embedding_cache:
            return self.embedding_cache[text]

        if self.embedder is not None:
            emb = self.embedder.encode(
                [text],
                convert_to_numpy=True,
                show_progress_bar=False,
                normalize_embeddings=True
            )[0]
            # Keep cache bounded
            if len(self.embedding_cache) > 1000:
                self.embedding_cache.clear()
            self.embedding_cache[text] = emb
            return emb

        # Fallback sparse-to-pseudo-dense vector if deep learning is disabled
        return np.zeros(768, dtype=np.float32)

    def get_vector(self, text: str) -> Dict[str, float]:
        """Compute compact vector dictionary for database storage and telemetry."""
        dense = self.get_dense_embedding(text)
        return {f"dim_{i}": round(float(val), 4) for i, val in enumerate(dense[:32])}

    def classify_category(self, text: str) -> Tuple[str, float]:
        """
        Classifies complaint into one of the 7 campus categories.
        Uses trained MPNet LogisticRegression classifier if available, with heuristic fallback.
        """
        cleaned = self.preprocess(text)

        # Branch A: Supervised MPNet Classifier
        if self.classifier_bundle is not None and self.embedder is not None:
            try:
                emb = self.get_dense_embedding(cleaned).reshape(1, -1)
                clf = self.classifier_bundle["classifier"]
                classes = self.classifier_bundle["classes"]
                probs = clf.predict_proba(emb)[0]
                best_idx = int(np.argmax(probs))
                predicted_cat = classes[best_idx]
                confidence = float(probs[best_idx])
                return (predicted_cat, round(confidence, 2))
            except Exception as e:
                print(f"[AI Engine] Classifier inference error: {e}")

        # Fallback Heuristic Classifier
        normalized = cleaned.lower()
        scores = {}
        for cat, keywords in self.categories_keywords.items():
            score = 0.0
            for kw in keywords:
                if kw in normalized:
                    score += 2.0
            scores[cat] = score

        best_cat = max(scores, key=scores.get)
        max_score = scores[best_cat]
        if max_score == 0:
            return ("Academics / Facilities", 0.65)

        total_score = sum(scores.values())
        confidence = round(min(0.99, max(0.60, (max_score / (total_score + 1.0)) * 1.2)), 2)
        return (best_cat, confidence)

    def compute_semantic_match(
        self,
        query_text: str,
        query_cat: str,
        query_loc: Optional[str],
        candidate_text: str,
        candidate_cat: str,
        candidate_loc: Optional[str]
    ) -> float:
        """
        Computes calibrated cross-lingual semantic similarity between two complaints:
        1. Dense MPNet Cosine Similarity (paraphrase-multilingual-mpnet-base-v2, 768-d)
        2. Domain category alignment boost (+0.12)
        3. Physical campus location proximity boost (+0.12)
        """
        cleaned_query = self.preprocess(query_text)
        cleaned_candidate = self.preprocess(candidate_text)

        if self.embedder is not None:
            v1 = self.get_dense_embedding(cleaned_query)
            v2 = self.get_dense_embedding(cleaned_candidate)
            # Dot product of L2-normalized vectors is cosine similarity
            raw_sim = float(np.dot(v1, v2))
        else:
            # Fallback keyword overlap without stopwords
            q_words = set(re.findall(r'\w+', cleaned_query.lower())) - self.stopwords
            c_words = set(re.findall(r'\w+', cleaned_candidate.lower())) - self.stopwords
            intersection = len(q_words & c_words)
            union = len(q_words | c_words) or 1
            raw_sim = (intersection / union) * 1.3

        sim = raw_sim

        # Domain category alignment boost
        if query_cat and candidate_cat:
            if query_cat.lower() == candidate_cat.lower() or query_cat in candidate_cat or candidate_cat in query_cat:
                sim += 0.12

        # Geographic proximity boost
        if query_loc and candidate_loc and query_loc == candidate_loc:
            sim += 0.12

        return min(0.99, max(0.05, round(sim, 2)))

    def extract_location(self, text: str) -> Optional[str]:
        """Extract campus location ID if mentioned in text (multilingual)."""
        t = text.lower()
        if "block c" in t or "hostel c" in t or "ब्लॉक सी" in t or "হোস্টেল সি" in t or "hostel-c" in t:
            return "hostel-c-2"
        if "lab 3" in t or "turing" in t or "computer lab" in t or "लैब 3" in t or "ল্যাব ৩" in t:
            return "cs-lab-3"
        if "dining" in t or "mess" in t or "canteen" in t or "मेस" in t or "ডাইনিং" in t:
            return "dining-1"
        if "science" in t or "staircase" in t or "academic wing" in t or "साइंस" in t or "সায়েন্স" in t:
            return "science-quad"
        if "library" in t or "reading" in t or "लाइब्रेरी" in t or "লাইব্রেরি" in t:
            return "lib-3-east"
        return None

    def detect_urgency(self, text: str, category: str) -> str:
        """Determine urgency based on safety keywords across English, Hindi, and Bengali."""
        t = text.lower()
        for kw in self.critical_keywords:
            if kw in t:
                return "CRITICAL"

        if category in ["Hostel / Water", "Electrical", "Security"]:
            for kw in self.high_keywords:
                if kw in t:
                    return "CRITICAL"
            return "HIGH"

        for kw in self.high_keywords:
            if kw in t:
                return "HIGH"

        for kw in self.medium_keywords:
            if kw in t:
                return "MEDIUM"

        return "LOW"

    def calculate_priority(
        self,
        urgency: str,
        complaint_count: int,
        upvote_count: int,
        category: str,
        age_hours: float = 1.0,
        hotspot_index: int = 50
    ) -> Tuple[int, str, str]:
        """
        Deterministic multi-factor priority calculator:
        Priority = 0.40 * Urgency + 0.25 * Affected + 0.20 * Recurrence + 0.10 * Age + 0.05 * CategoryWeight
        """
        urgency_map = {"CRITICAL": 95, "HIGH": 80, "MEDIUM": 60, "LOW": 35}
        u_score = urgency_map.get(urgency, 60)

        effective_affected = complaint_count * 2.0 + upvote_count * 1.0
        affected_score = min(100.0, 30.0 + (effective_affected * 1.8))

        recurrence_score = min(100.0, float(hotspot_index))
        age_score = min(100.0, 40.0 + (age_hours * 5.0))

        cat_weights = {
            "Hostel / Water": 92,
            "Electrical": 88,
            "Security": 95,
            "IT / Network": 78,
            "Sanitation": 70,
            "Food / Mess": 65,
            "Academics / Facilities": 50
        }
        c_score = cat_weights.get(category, 60)

        final_score = (
            0.40 * u_score +
            0.25 * affected_score +
            0.20 * recurrence_score +
            0.10 * age_score +
            0.05 * c_score
        )

        score_int = int(round(final_score))
        score_int = min(100, max(10, score_int))

        if score_int >= 85:
            level = "CRITICAL"
            sla = "2h"
        elif score_int >= 70:
            level = "HIGH"
            sla = "6h"
        elif score_int >= 50:
            level = "MEDIUM"
            sla = "24h"
        else:
            level = "LOW"
            sla = "48h"

        return (score_int, level, sla)

    def route_team(self, category: str, location_id: Optional[str] = None) -> str:
        """Route issue to operational campus team."""
        routing_map = {
            "Hostel / Water": "hostel-maint",
            "Electrical": "electrical",
            "IT / Network": "it-ops",
            "Food / Mess": "mess",
            "Sanitation": "facilities",
            "Security": "security",
            "Academics / Facilities": "facilities"
        }
        return routing_map.get(category, "hostel-maint")


# Singleton instance
ai_engine = CampusPulseAIEngine()
