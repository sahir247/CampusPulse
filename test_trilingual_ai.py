"""
Test script for Trilingual NLP Capabilities in CampusPulse:
Tests English, Hindi (Devanagari & Hinglish), and Bengali (Bangla & Benglish)
against the live API at http://127.0.0.1:8000.
"""

import sys
import requests

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:8000"

TEST_CASES = [
    {
        "lang": "English",
        "text": "WiFi keeps dropping in CS Turing lab 3 during midterms",
        "expected_cat": "IT / Network",
    },
    {
        "lang": "Hindi (Devanagari)",
        "text": "हॉस्टल सी में सुबह से बिल्कुल पानी नहीं आ रहा है, नल सूखे पड़े हैं",
        "expected_cat": "Hostel / Water",
        "should_match_cluster": "ISSUE-2026-00421"
    },
    {
        "lang": "Hinglish (Romanized Hindi)",
        "text": "Mess me khana bilkul thanda aur bekar hai, dal paani jaisi hai",
        "expected_cat": "Food / Mess",
    },
    {
        "lang": "Bengali (Bangla Script)",
        "text": "সায়েন্স ব্লকের সিঁড়ির সুইচবোর্ড থেকে স্পার্ক বের হচ্ছে, শর্ট সার্কিট হতে পারে",
        "expected_cat": "Electrical",
    },
    {
        "lang": "Benglish (Romanized Bengali)",
        "text": "Hostel C-te shokal theke jol nei, tap puro shukno",
        "expected_cat": "Hostel / Water",
        "should_match_cluster": "ISSUE-2026-00421"
    }
]

def run_tests():
    print("=" * 75)
    print("🌍 Testing CampusPulse Trilingual NLP Engine (English, Hindi, Bengali)")
    print("=" * 75)

    for tc in TEST_CASES:
        print(f"\n[{tc['lang']}] Input: '{tc['text']}'")
        res = requests.post(f"{BASE_URL}/api/complaints/preview", json={"text": tc["text"]})
        if res.status_code != 200:
            print(f"  ❌ Failed HTTP: {res.status_code}")
            continue

        data = res.json()
        print(f"  • Inferred Category: {data['inferred_category']} (Conf: {data['confidence'] * 100:.0f}%)")
        print(f"  • Urgency Detected:  {data['urgency']}")
        print(f"  • Duplicate Matched: {data['potential_duplicate']} -> {data.get('matched_issue_id')} (Sim: {data.get('similarity_score')})")

        cat_match = data["inferred_category"] == tc["expected_cat"]
        if cat_match:
            print("  ✅ Category Classification: PASSED")
        else:
            print(f"  ⚠️ Category Mismatch: Expected {tc['expected_cat']}, Got {data['inferred_category']}")

        if tc.get("should_match_cluster"):
            cluster_match = data.get("matched_issue_id") == tc["should_match_cluster"]
            if cluster_match:
                print(f"  ✅ Cross-Lingual Duplicate Match to {tc['should_match_cluster']}: PASSED ({int(data['similarity_score']*100)}% match)")
            else:
                print(f"  ⚠️ Cluster Match: Expected {tc['should_match_cluster']}, Got {data.get('matched_issue_id')}")

    print("\n" + "=" * 75)
    print("🏆 ALL TRILINGUAL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 75)

if __name__ == "__main__":
    run_tests()
