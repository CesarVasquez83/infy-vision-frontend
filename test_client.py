import requests

with open("tablero.png", "rb") as f:
    files = {"file": ("tablero.png", f, "image/png")}
    r = requests.post("http://127.0.0.1:8000/vision-analysis", files=files)
    print(r.status_code)
    print(r.json())
