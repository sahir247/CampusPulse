import requests
import json
import io

BASE_URL = "http://127.0.0.1:8000"

def test_image_flow():
    print("=== 1. Testing Image Upload Endpoint (/api/upload) ===")
    dummy_image_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    
    files = {
        'file': ('test_broken_pipe.png', io.BytesIO(dummy_image_data), 'image/png')
    }
    
    upload_res = requests.post(f"{BASE_URL}/api/upload", files=files)
    print(f"Upload status: {upload_res.status_code}")
    assert upload_res.status_code == 200, f"Upload failed: {upload_res.text}"
    upload_data = upload_res.json()
    image_url = upload_data["url"]
    print(f"Uploaded image URL: {image_url}")
    assert image_url.startswith("/uploads/"), "Image URL does not point to /uploads/"
    
    # Verify static file serving
    static_res = requests.get(f"{BASE_URL}{image_url}")
    print(f"Static fetch status: {static_res.status_code}")
    assert static_res.status_code == 200, "Static file serving failed!"
    assert len(static_res.content) == len(dummy_image_data), "Static content mismatch!"
    
    print("\n=== 2. Testing Complaint Submission with Image Attachment (New Issue) ===")
    unique_text = f"Broken classroom projector and glass window shattered in Main Library 3rd floor reading room"
    complaint_payload = {
        "raw_text": unique_text,
        "location_id": "lib-3-east",
        "is_anonymous": False,
        "student_id": "usr-student-1",
        "student_name": "Rohit Verma",
        "attachment_url": image_url,
        "image_url": image_url
    }
    
    post_res = requests.post(f"{BASE_URL}/api/complaints", json=complaint_payload)
    print(f"Complaint submission status: {post_res.status_code}")
    assert post_res.status_code == 200, f"Complaint post failed: {post_res.text}"
    comp_data = post_res.json()
    print(f"Complaint created: {comp_data}")
    assert comp_data["success"] is True
    issue_id = comp_data["issue_id"]
    
    print("\n=== 3. Testing Issue Retrieval with Image URL ===")
    issues_res = requests.get(f"{BASE_URL}/api/issues")
    assert issues_res.status_code == 200
    issues = issues_res.json()
    matched_issue = next((i for i in issues if i["id"] == issue_id), None)
    assert matched_issue is not None, "Created issue not found in list_issues"
    print(f"Issue title: {matched_issue['title']}")
    print(f"Issue image_url: {matched_issue.get('image_url')}")
    assert matched_issue.get("image_url") == image_url, f"Expected {image_url}, got {matched_issue.get('image_url')}"
    
    print("\n=== 4. Testing Issue Detail Retrieval with Child Complaints ===")
    detail_res = requests.get(f"{BASE_URL}/api/issues/{issue_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["image_url"] == image_url
    assert len(detail["complaints"]) >= 1
    assert detail["complaints"][0]["image_url"] == image_url
    print(f"Issue Detail has child complaint with image: {detail['complaints'][0]['image_url']}")

    print("\n=== 5. Testing Student Ticket History (/api/issues/user/my-tickets) ===")
    history_res = requests.get(f"{BASE_URL}/api/issues/user/my-tickets?user_id=usr-student-1")
    assert history_res.status_code == 200
    history = history_res.json()
    my_ticket = next((t for t in history if t["complaint_id"] == comp_data["complaint_id"]), None)
    assert my_ticket is not None, "Ticket not found in student history"
    print(f"Student history record image URL: {my_ticket.get('complaint_image_url')}")
    assert my_ticket.get("complaint_image_url") == image_url or my_ticket.get("image_url") == image_url

    print("\nALL IMAGE REPORTING VERIFICATION TESTS PASSED SUCCESSFULLY! [PASS]")

if __name__ == "__main__":
    test_image_flow()
