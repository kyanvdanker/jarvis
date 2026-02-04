import requests

API_KEY = "YOUR_OCTOPRINT_API_KEY"
OCTO_URL = "http://YOUR_OCTOPRINT_IP/api"

def send_to_printer(stl_path):
    try:
        # Upload file
        files = {'file': open(stl_path, 'rb')}
        r = requests.post(
            f"{OCTO_URL}/files/local",
            files=files,
            headers={"X-Api-Key": API_KEY}
        )

        if r.status_code not in (200, 201):
            return False

        filename = r.json()["files"]["local"]["name"]

        # Start print
        r = requests.post(
            f"{OCTO_URL}/printer/print",
            json={"command": "select", "print": True, "file": filename},
            headers={"X-Api-Key": API_KEY}
        )

        return r.status_code == 204

    except Exception as e:
        print("Printer error:", e)
        return False
