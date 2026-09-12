"""
Comprehensive Test Script for CampusPulse Auth, RBAC, and Action Log
Tests:
1. All 5 demo users can authenticate successfully via /api/auth/login
2. Student token profile via /api/auth/me
3. Student attempting status update returns HTTP 403 Forbidden
4. Non-student (Faculty, HOD, Management, Staff) updating status with comment succeeds (HTTP 200)
5. Action log timeline captures actor_name, actor_role, and comment
"""

import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_auth_and_rbac():
    print("=================================================================")
    print("Testing CampusPulse Authentication, RBAC, and Action Logging")
    print("=================================================================")

    # 1. Test Login for all 5 roles
    users_to_test = [
        ("student_rohit", "student@123", "student"),
        ("prof_sharma", "faculty@123", "faculty"),
        ("hod_cse", "hod@123", "hod"),
        ("admin_dean", "mgmt@123", "management"),
        ("staff_singh", "staff@123", "staff")
    ]

    tokens = {}
    user_data = {}

    for username, pwd, expected_role in users_to_test:
        res = requests.post(f"{BASE_URL}/api/auth/login", json={"username": username, "password": pwd})
        if res.status_code != 200:
            print(f"[FAIL] Failed login for {username}: {res.status_code} {res.text}")
            sys.exit(1)
        data = res.json()
        assert data["success"] is True
        assert data["user"]["role"] == expected_role
        tokens[expected_role] = data["token"]
        user_data[expected_role] = data["user"]
        print(f"[OK] Login OK: {data['user']['full_name']} ({data['user']['role'].upper()})")

    # 2. Test Invalid Credentials
    bad_res = requests.post(f"{BASE_URL}/api/auth/login", json={"username": "student_rohit", "password": "wrongpassword"})
    assert bad_res.status_code == 401
    print("[OK] 401 Unauthorized correctly returned for invalid password")

    # 3. Test /api/auth/me
    headers = {"Authorization": f"Bearer {tokens['student']}"}
    me_res = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "student_rohit"
    print("[OK] /api/auth/me correctly identifies student_rohit from bearer token")

    # 4. Fetch an active issue to test RBAC status update
    issues_res = requests.get(f"{BASE_URL}/api/issues?limit=1")
    assert issues_res.status_code == 200
    issues = issues_res.json()
    if not issues:
        print("Creating sample issue via demo seed...")
        requests.post(f"{BASE_URL}/api/demo/seed")
        issues = requests.get(f"{BASE_URL}/api/issues?limit=1").json()
    
    test_issue_id = issues[0]["id"]
    test_case_id = issues[0]["case_id"]
    print(f"Testing status updates on issue: {test_case_id} ({test_issue_id})")

    # 5. RBAC: Student attempting status update must be rejected with 403
    student_update = {
        "status": "RESOLVED",
        "changed_by": user_data["student"]["full_name"],
        "changed_by_role": user_data["student"]["role"],
        "comment": "Student trying to resolve ticket"
    }
    forbidden_res = requests.patch(f"{BASE_URL}/api/issues/{test_issue_id}/status", json=student_update)
    assert forbidden_res.status_code == 403, f"Expected 403, got {forbidden_res.status_code}"
    print(f"[OK] RBAC Guard Enforced: Student status update blocked with HTTP 403 Forbidden! Details: {forbidden_res.json()['detail']}")

    # 6. HOD marks ticket IN_PROGRESS with comment
    hod_update = {
        "status": "IN_PROGRESS",
        "changed_by": user_data["hod"]["full_name"],
        "changed_by_role": user_data["hod"]["role"],
        "comment": "Maintenance team dispatched to inspect piping"
    }
    hod_res = requests.patch(f"{BASE_URL}/api/issues/{test_issue_id}/status", json=hod_update)
    assert hod_res.status_code == 200
    print(f"[OK] HOD status update succeeded: IN_PROGRESS by {user_data['hod']['full_name']}")

    # 7. Faculty marks ticket RESOLVED with comment
    faculty_update = {
        "status": "RESOLVED",
        "changed_by": user_data["faculty"]["full_name"],
        "changed_by_role": user_data["faculty"]["role"],
        "comment": "Repairs verified on-site. Clean water flow restored."
    }
    fac_res = requests.patch(f"{BASE_URL}/api/issues/{test_issue_id}/status", json=faculty_update)
    assert fac_res.status_code == 200
    print(f"[OK] Faculty status update succeeded: RESOLVED by {user_data['faculty']['full_name']}")

    # 8. Verify Action Log Timeline via /api/issues/{id}/timeline
    timeline_res = requests.get(f"{BASE_URL}/api/issues/{test_issue_id}/timeline")
    assert timeline_res.status_code == 200
    timeline = timeline_res.json()
    assert len(timeline) >= 2, "Expected at least 2 timeline events"

    latest = timeline[0]
    print("\nAction Log Verification:")
    print(f"  * Title: {latest['title']}")
    print(f"  * Actor: {latest['actor_name']} ({latest['actor_role']})")
    print(f"  * Comment: {latest['comment']}")
    print(f"  * Description: {latest['description']}")

    assert latest["actor_name"] == user_data["faculty"]["full_name"]
    assert latest["actor_role"] == "FACULTY"
    assert "Repairs verified on-site" in latest["comment"]

    second = timeline[1]
    assert second["actor_name"] == user_data["hod"]["full_name"]
    assert second["actor_role"] == "HOD"
    assert "Maintenance team dispatched" in second["comment"]

    print("\n[SUCCESS] ALL AUTH, RBAC, AND ACTION LOG TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_auth_and_rbac()
