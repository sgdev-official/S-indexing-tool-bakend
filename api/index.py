import requests

GOOGLE_SHEET_API = "https://script.google.com/macros/s/AKfycbzG1fAg6CKkbsOLaNgGRsuqvYoyg8tva6VwPQusEfzsISyJXmVchP_72Vjj9_jY3zATEQ/exec"

def push_to_google_sheet(target_url: str):
    try:
        # JSON Body আকারে পাঠানো
        response = requests.post(
            GOOGLE_SHEET_API, 
            json={"url": target_url}, 
            headers={"Content-Type": "application/json"},
            allow_redirects=True,
            timeout=10
        )
        print(f"Sync Success: {response.status_code}")
    except Exception as e:
        print(f"Sync Failed: {e}")
