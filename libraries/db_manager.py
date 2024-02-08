import json
import gc
import time
import asyncio


class DbManager():
    def __init__(self):
        self.db = "db.json"

    async def r_d(self):
        with open(self.db, "r") as f:
            data = json.load(f)
        gc.collect()
        return data

    async def w_d(self, data):
        try:
            with open(self.db, "w") as f:
                json.dump(data, f)
            gc.collect()
            return True  # Indicate success
        except Exception as e:
            print(f"Error writing to file: {e}")
            return False

    async def get_trx(self):
        try:
            db = await self.r_d()
            trx = db.get("transactions", [])
            gc.collect()
            if not trx:
                return None
            else:
                return trx
        except Exception as e:
            print("reading transaction failed", e)
            return None

    async def add_trx(self, data):
        try:
            db = await self.r_d()
            trx = db.get("transactions", [])
            if data not in trx:
                trx.append(data)
            db["transactions"] = trx
            gc.collect()
            return await self.w_d(db)
        except Exception as e:
            return False

    async def rm_trx(self, data):
        try:
            db = await self.r_d()
            trx = db.get("transactions", [])
            if data in trx:
                trx.remove(data)
                db["transactions"] = trx
                return await self.w_d(db)
            else:
                return False
            gc.collect()
        except Exception as e:
            return False

    async def sv_bal(self, dt, crd):
        try:
            db = await self.r_d()
            users = db.get("users", [])
            for u in users:
                if str(crd) in u:
                    u[crd] = dt
                    break
            gc.collect()
            return await self.w_d(db)
        except Exception as e:
            return False
