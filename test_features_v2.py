import requests
import json
import sys

BASE = "http://127.0.0.1:8000"

def test_all():
    print("--- 1. Testing Recipients Directory ---")
    res = requests.get(f"{BASE}/api/recipients")
    assert res.status_code == 200
    recipients = res.json()
    print(f"Recipients found: {len(recipients)}")
    roles = {r["role"] for r in recipients}
    assert "hod" in roles and "management" in roles and "faculty" in roles and "staff" in roles
    print("[OK] Recipients directory verified with all 4 leadership roles.")

    print("\n--- 2. Testing Active-Only Feed ---")
    res = requests.get(f"{BASE}/api/issues?active_only=true")
    assert res.status_code == 200
    active_issues = res.json()
    print(f"Active issues count: {len(active_issues)}")
    for iss in active_issues:
        assert iss["status"] in ("OPEN", "ASSIGNED", "IN_PROGRESS"), f"Unexpected status: {iss['status']}"
    print("[OK] Active-only filter verified (zero resolved tickets in active feed).")

    test_issue_id = active_issues[0]["id"]
    print(f"Target issue for vote testing: {active_issues[0]['case_id']} ({test_issue_id})")

    print("\n--- 3. Testing Strict Single-Vote per Student & Non-Student Voting Block ---")
    # Non-student voting must return 403
    faculty_vote = requests.post(f"{BASE}/api/issues/{test_issue_id}/upvote", json={
        "user_id": "usr-faculty-1",
        "username": "prof_sharma",
        "user_role": "faculty"
    })
    print("Faculty vote status code:", faculty_vote.status_code)
    assert faculty_vote.status_code == 403, f"Expected 403 for faculty vote, got {faculty_vote.status_code}"
    print("[OK] Non-student voting strictly blocked with 403.")

    # Student first vote (should succeed)
    import uuid
    rand_suffix = uuid.uuid4().hex[:6]
    student_user_id = f"test_student_{rand_suffix}"
    student_username = f"student_{rand_suffix}"
    student_vote_1 = requests.post(f"{BASE}/api/issues/{test_issue_id}/upvote", json={
        "user_id": student_user_id,
        "username": student_username,
        "user_role": "student"
    })
    print("Student 1st vote status code:", student_vote_1.status_code)
    assert student_vote_1.status_code == 200
    data_v1 = student_vote_1.json()
    print(f"[OK] 1st Vote accepted: Total votes = {data_v1['upvote_count']}, Priority = {data_v1['new_priority_level']}")

    # Student duplicate vote on same ticket (must return 400)
    student_vote_2 = requests.post(f"{BASE}/api/issues/{test_issue_id}/upvote", json={
        "user_id": student_user_id,
        "username": student_username,
        "user_role": "student"
    })
    print("Student 2nd vote status code:", student_vote_2.status_code)
    assert student_vote_2.status_code == 400, f"Expected 400 for duplicate vote, got {student_vote_2.status_code}"
    print("[OK] Duplicate voting by same student on same ticket strictly rejected (400).")

    # Student can vote on a DIFFERENT ticket
    if len(active_issues) > 1:
        other_issue_id = active_issues[1]["id"]
        other_vote = requests.post(f"{BASE}/api/issues/{other_issue_id}/upvote", json={
            "user_id": student_user_id,
            "username": student_username,
            "user_role": "student"
        })
        assert other_vote.status_code == 200
        print("[OK] Student successfully voted on a second distinct ticket.")

    print("\n--- 4. Testing Submission Modes & Anonymity ---")
    # Public complaint
    res_pub = requests.post(f"{BASE}/api/complaints", json={
        "raw_text": "Classroom 401 projector bulb blown, screen completely black.",
        "location_id": "science-quad",
        "is_anonymous": False,
        "student_id": "usr-student-1",
        "student_name": "Rohit Verma"
    })
    assert res_pub.status_code == 200
    pub_data = res_pub.json()
    print(f"Public report submitted: {pub_data['case_id']}")

    # Anonymous complaint
    res_anon = requests.post(f"{BASE}/api/complaints", json={
        "raw_text": "Chemistry laboratory emergency eyewash valve is leaking water continuously.",
        "location_id": "science-quad",
        "is_anonymous": True,
        "student_id": "usr-student-1",
        "student_name": "Rohit Verma"
    })
    assert res_anon.status_code == 200
    anon_data = res_anon.json()
    print(f"Anonymous report submitted: {anon_data['case_id']}")

    # Verify in issues list
    check_issues = requests.get(f"{BASE}/api/issues?search=Chemistry").json()
    if check_issues:
        target = check_issues[0]
        assert target["is_anonymous"] == True
        assert target["creator_name"] == "Anonymous Student"
        print("[OK] Anonymous report strictly redacts creator identity.")

    print("\n--- 5. Testing Private Messaging & Strict Inbox Isolation ---")
    # Student sends private message to HOD
    priv_post = requests.post(f"{BASE}/api/messages/private", json={
        "sender_id": "usr-student-1",
        "sender_name": "Rohit Verma",
        "sender_role": "student",
        "is_anonymous": False,
        "recipient_role": "hod",
        "recipient_id": "usr-hod-1",
        "recipient_name": "Dr. Ananya Mukherjee",
        "recipient_dept": "Computer Science & Engineering",
        "subject": "Confidential query regarding lab workstation access",
        "message": "Dear HOD, lab terminals are locked after 6 PM during semester project week. Can access be extended?",
        "category": "Academic / Lab Policy",
        "urgency": "STANDARD"
    })
    assert priv_post.status_code == 200
    priv_data = priv_post.json()
    msg_id = priv_data["message_id"]
    print(f"Private message sent to HOD (ID: {msg_id})")

    # Student cannot read private inbox
    student_inbox = requests.get(f"{BASE}/api/messages/inbox?user_id=usr-student-1&role=student")
    assert student_inbox.status_code == 403
    print("[OK] Students blocked from accessing leadership private inbox (403).")

    # Faculty Sharma cannot read HOD Mukherjee's private message (isolation)
    faculty_inbox = requests.get(f"{BASE}/api/messages/inbox?user_id=usr-faculty-1&role=faculty")
    assert faculty_inbox.status_code == 200
    faculty_msgs = faculty_inbox.json()
    assert not any(m["id"] == msg_id for m in faculty_msgs), "Message leaked to unauthorized faculty!"
    print("[OK] Recipient isolation verified: Faculty member cannot see HOD's private messages.")

    # HOD Mukherjee reads inbox and finds message
    hod_inbox = requests.get(f"{BASE}/api/messages/inbox?user_id=usr-hod-1&role=hod")
    assert hod_inbox.status_code == 200
    hod_msgs = hod_inbox.json()
    matching = [m for m in hod_msgs if m["id"] == msg_id]
    assert len(matching) == 1
    print("[OK] HOD successfully received the confidential message in their private inbox.")

    # HOD replies to the private message
    reply_res = requests.patch(f"{BASE}/api/messages/{msg_id}/reply", json={
        "reply_note": "Request approved. Security staff has been informed to keep CS Lab 3 open until 9 PM this week.",
        "replied_by": "Dr. Ananya Mukherjee (HOD, CSE)"
    })
    assert reply_res.status_code == 200
    print("[OK] HOD successfully submitted confidential reply.")

    # Student checks their sent messages in 'My Ticket History'
    student_sent = requests.get(f"{BASE}/api/messages/sent?user_id=usr-student-1").json()
    sent_target = [m for m in student_sent if m["id"] == msg_id]
    assert len(sent_target) == 1
    assert sent_target[0]["status"] == "REPLIED"
    assert "Request approved" in sent_target[0]["reply_note"]
    print("[OK] Student receives and views the confidential reply note in 'My Ticket History'.")

    print("\n--- 6. Testing Student Ticket History & Resolved Archive ---")
    my_tickets = requests.get(f"{BASE}/api/issues/user/my-tickets?user_id=usr-student-1&username=student_rohit").json()
    assert len(my_tickets) > 0
    print(f"[OK] Student ticket history verified ({len(my_tickets)} records retrieved).")

    archive = requests.get(f"{BASE}/api/issues/archive/resolved").json()
    assert len(archive) > 0
    for r in archive:
        assert r["status"] in ("RESOLVED", "CLOSED")
    print(f"[OK] Resolved ticket archive verified ({len(archive)} past records retrieved).")

    print("\n=======================================================")
    print("SUCCESS: ALL ROLE-BASED & DYNAMIC TICKETING REQUIREMENTS PASSED!")
    print("=======================================================")

if __name__ == "__main__":
    test_all()
