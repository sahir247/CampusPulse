from backend.database import init_db, get_connection
from backend.routers.demo import seed_demo_data
from backend.routers.complaints import preview_complaint_nlp, submit_complaint
from backend.models import ComplaintPreviewRequest, ComplaintCreate, UpvoteRequest
from backend.routers.issues import list_issues, get_issue_detail, upvote_issue
from backend.routers.dashboard import get_dashboard_summary, get_hotspots

def run_tests():
    print("1. Initializing database and seeding demo data...")
    init_db()
    seed_res = seed_demo_data()
    print("Seed result:", seed_res)

    print("\n2. Testing Dashboard summary...")
    summary = get_dashboard_summary()
    print(f"Summary: Total Complaints: {summary.total_complaints}, Active: {summary.active_clusters}, Critical: {summary.critical_issues}")
    assert summary.active_clusters >= 4

    print("\n3. Testing Issue listing...")
    issues = list_issues()
    print(f"Found {len(issues)} issues.")
    for iss in issues[:3]:
        print(f"  - [{iss.case_id}] {iss.title} ({iss.priority_level} {iss.priority_score}) - {iss.complaint_count} reports")

    print("\n4. Testing NLP Preview...")
    preview = preview_complaint_nlp(ComplaintPreviewRequest(text="No water in Block C since morning, shower dry"))
    print(f"Preview: Inferred={preview.inferred_category}, Urgency={preview.urgency}, Matched={preview.matched_issue_id}, Sim={preview.similarity_score}")
    assert preview.potential_duplicate is True
    assert preview.matched_issue_id == "ISSUE-2026-00421"

    print("\n5. Testing Complaint Submission (Deduplication into ISSUE-2026-00421)...")
    submit_res = submit_complaint(ComplaintCreate(
        text="Water supply stopped in C block washroom on floor 2",
        location_id="hostel-c-2",
        is_anonymous=False,
        student_name="Test Student",
        student_id="STD-99"
    ))
    print("Submit Result:", submit_res)
    assert submit_res["merged_into_existing"] is True
    assert submit_res["case_id"] == "ISSUE-2026-00421"

    detail = get_issue_detail("ISSUE-2026-00421")
    print(f"Updated Issue 421 complaint count: {detail.complaint_count} (was 37)")
    assert detail.complaint_count >= 38

    print("\n6. Testing Upvoting...")
    upvote_res = upvote_issue(detail.id, UpvoteRequest(user_id="std-rohit", username="student_rohit", user_role="student"))
    print(f"Upvote Result: success={upvote_res.success}, new_upvotes={upvote_res.upvote_count}, new_score={upvote_res.new_priority_score}")
    assert upvote_res.success is True

    print("\n7. Testing Hotspots calculation...")
    hotspots = get_hotspots()
    print(f"Rank 1 Hotspot: {hotspots[0].location_name} (Index: {hotspots[0].hotspot_index})")
    assert hotspots[0].hotspot_index >= 90

    print("\nALL BACKEND AUTOMATED TESTS PASSED SUCCESSFULLY! [OK]")

if __name__ == "__main__":
    run_tests()
