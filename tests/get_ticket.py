import os, requests
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")
SK = os.environ["CLERK_SECRET_KEY"]
r = requests.post("https://api.clerk.com/v1/sign_in_tokens", headers={"Authorization": f"Bearer {SK}"},
                  json={"user_id": "user_3L6hhploCiep0mzXWVPKBKQmMP8"})
print(r.json()["token"])
