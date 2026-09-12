import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_full_system():
    print("Testing Full System via HTTP at", BASE_URL)

    # Reset demo state first
    requests.post(f"{BASE_URL}/api/demo/seed")

    # 1. Test Static Frontend
    r = requests.get(f"{BASE_URL}/")
    print(f"GET / (Frontend index.html): {r.status_code}, length={len(r.text)}")
    assert r.status_code == 200
    assert "CampusPulse" in r.text
    assert "Incident Log" in r.text

    r_js = requests.get(f"{BASE_URL}/app.js")
    print(f"GET /app.js: {r_js.status_code}, length={len(r_js.text)}")
    assert r_js.status_code == 200
    assert "switchView" in r_js.text

    # 2. Test Dashboard Summary
    r_summary = requests.get(f"{BASE_URL}/api/dashboard/summary")
    print(f"GET /api/dashboard/summary: {r_summary.status_code}, data={r_summary.json()}")
    assert r_summary.status_code == 200
    s_data = r_summary.json()
    assert s_data["active_clusters"] >= 4

    # 3. Test NLP Preview
    r_prev = requests.post(f"{BASE_URL}/api/complaints/preview", json={
        "text": "Water is completely stopped on Block C floor 2, taps are dry."
    })
    print(f"POST /api/complaints/preview: {r_prev.status_code}, data={r_prev.json()}")
    assert r_prev.status_code == 200
    prev_data = r_prev.json()
    assert prev_data["potential_duplicate"] is True
    assert prev_data["matched_issue_id"] == "ISSUE-2026-00421"

    # 4. Test Student Submission (Deduplication into Issue 421)
    r_sub = requests.post(f"{BASE_URL}/api/complaints", json={
        "text": "Water pressure completely failed on Block C 2nd floor, washrooms unusable since 7 AM",
        "location_id": "hostel-c-2",
        "is_anonymous": True,
        "student_name": "Anonymous Student",
        "student_id": "STD-89"
    })
    print(f"POST /api/complaints: {r_sub.status_code}, data={r_sub.json()}")
    assert r_sub.status_code == 200
    sub_data = r_sub.json()
    assert sub_data["merged_into_existing"] is True
    assert sub_data["case_id"] == "ISSUE-2026-00421"

    # 5. Test Upvoting
    r_upvote = requests.post(f"{BASE_URL}/api/issues/issue-421/upvote")
    print(f"POST /api/issues/issue-421/upvote: {r_upvote.status_code}, data={r_upvote.json()}")
    assert r_upvote.status_code == 200

    # 6. Test Issue Detail and Inspection
    r_detail = requests.get(f"{BASE_URL}/api/issues/ISSUE-2026-00421")
    print(f"GET /api/issues/ISSUE-2026-00421: {r_detail.status_code}")
    assert r_detail.status_code == 200
    det = r_detail.json()
    print(f"  - Case: {det['case_id']}, Reports: {det['complaint_count']}, Upvotes: {det['upvote_count']}")
    print(f"  - Raw child complaints attached: {len(det['complaints'])}")
    assert len(det['complaints']) >= 4

    # 7. Test Hotspots
    r_hotspots = requests.get(f"{BASE_URL}/api/dashboard/hotspots")
    print(f"GET /api/dashboard/hotspots: {r_hotspots.status_code}")
    assert r_hotspots.status_code == 200
    hotspots = r_hotspots.json()
    assert len(hotspots) >= 4

    # 8. Test Active Learning Feedback
    r_fb = requests.post(f"{BASE_URL}/api/issues/issue-418/feedback", json={
        "field": "category",
        "predicted_value": "IT / Network",
        "corrected_value": "IT / Network",
        "notes": "Confirmed IT team assignment",
        "corrected_by": "Dean E. Vance"
    })
    print(f"POST /api/issues/issue-418/feedback: {r_fb.status_code}, data={r_fb.json()}")
    assert r_fb.status_code == 200

    # 9. Test Jira Webhook Sync
    r_jira = requests.post(f"{BASE_URL}/api/webhooks/jira", json={
        "issue": {
            "key": "CAMP-421",
            "fields": {
                "status": {"name": "Resolved"}
            }
        }
    })
    print(f"POST /api/webhooks/jira: {r_jira.status_code}, data={r_jira.json()}")
    assert r_jira.status_code == 200
    jira_res = r_jira.json()
    assert jira_res["new_status"] == "RESOLVED"

    # Verify status changed to RESOLVED
    r_verify = requests.get(f"{BASE_URL}/api/issues/ISSUE-2026-00421")
    assert r_verify.json()["status"] == "RESOLVED"

    # Reset back to IN_PROGRESS for pristine demo state
    requests.patch(f"{BASE_URL}/api/issues/issue-421/status", json={"status": "IN_PROGRESS", "note": "Re-opened for demo"})

    print("\nALL HTTP ENDPOINTS AND STATIC ASSETS VERIFIED 100% OPERATIONAL! [OK]")

if __name__ == "__main__":
    test_full_system()
