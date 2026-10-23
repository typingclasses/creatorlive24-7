# Prints a Clerk sign-in ticket for UI testing (usage: python make_ticket.py email)
import sys
sys.path.insert(0, '/app/backend/tests')
from conftest import bapi, make_user
u, _ = make_user(sys.argv[1])
print(bapi("/sign_in_tokens", {"user_id": u["id"], "expires_in_seconds": 3600})["token"])
