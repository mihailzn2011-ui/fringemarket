import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # sb_secret_... ключ


class DBManager:
    def __init__(self):
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def get_points(self, user_id: int) -> int:
        try:
            res = self.client.table("points").select("points").eq("user_id", str(user_id)).execute()
            if res.data:
                return res.data[0]["points"]
            return 0
        except Exception as e:
            print(f"get_points error: {e}")
            return 0

    def set_points(self, user_id: int, points: int, username: str = ""):
        try:
            existing = self.client.table("points").select("user_id").eq("user_id", str(user_id)).execute()
            if existing.data:
                self.client.table("points").update({
                    "points": points,
                    "username": username
                }).eq("user_id", str(user_id)).execute()
            else:
                self.client.table("points").insert({
                    "user_id": str(user_id),
                    "username": username,
                    "points": points
                }).execute()
        except Exception as e:
            print(f"set_points error: {e}")

    def add_points(self, user_id: int, amount: int, username: str = "") -> int:
        current = self.get_points(user_id)
        new_total = current + amount
        self.set_points(user_id, new_total, username)
        return new_total
