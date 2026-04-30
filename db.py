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

    def get_all_points(self) -> dict:
        """Получает баллы всех игроков в формате {user_id: points}"""
        try:
            res = self.client.table("points").select("user_id, points").execute()
            result = {}
            if res.data:
                for row in res.data:
                    try:
                        user_id = int(row["user_id"])
                        points = row["points"]
                        result[user_id] = points
                    except (ValueError, KeyError):
                        continue
            return result
        except Exception as e:
            print(f"get_all_points error: {e}")
            return {}

    def set_dayoff(self, user_id: int, start_date: str, end_date: str, days: int):
        """Устанавливает отгул для игрока"""
        try:
            existing = self.client.table("dayoffs").select("user_id").eq("user_id", str(user_id)).execute()
            if existing.data:
                self.client.table("dayoffs").update({
                    "start_date": start_date,
                    "end_date": end_date,
                    "days": days
                }).eq("user_id", str(user_id)).execute()
            else:
                self.client.table("dayoffs").insert({
                    "user_id": str(user_id),
                    "start_date": start_date,
                    "end_date": end_date,
                    "days": days
                }).execute()
        except Exception as e:
            print(f"set_dayoff error: {e}")

    def remove_dayoff(self, user_id: int):
        """Удаляет отгул игрока"""
        try:
            self.client.table("dayoffs").delete().eq("user_id", str(user_id)).execute()
        except Exception as e:
            print(f"remove_dayoff error: {e}")

    def get_all_dayoffs(self) -> dict:
        """Получает все отгулы в формате {user_id: {start_date, end_date, days}}"""
        try:
            res = self.client.table("dayoffs").select("user_id, start_date, end_date, days").execute()
            result = {}
            if res.data:
                for row in res.data:
                    try:
                        user_id = int(row["user_id"])
                        result[user_id] = {
                            "start_date": row["start_date"],
                            "end_date": row["end_date"],
                            "days": row["days"]
                        }
                    except (ValueError, KeyError):
                        continue
            return result
        except Exception as e:
            print(f"get_all_dayoffs error: {e}")
            return {}
