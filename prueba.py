import requests

TOKEN = "8488886057:AAH8PkpvspCgwGWNY4ImAKgJ7bf58fzpzjo"
url = f"https://api.telegram.org/bot{TOKEN}/getMe"

r = requests.get(url)
print(r.text)
