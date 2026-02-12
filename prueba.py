import requests

TOKEN = ""
url = f"https://api.telegram.org/bot{TOKEN}/getMe"

r = requests.get(url)
print(r.text)
