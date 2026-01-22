import httpx


ADS_API = "http://localhost:50325/api/v1"


class ADSClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30)

    async def start_profile(self, profile_id: str) -> str:
        r = await self.client.get(f"{ADS_API}/browser/start", params={"user_id": profile_id})
        r.raise_for_status()
        data = r.json()
        return data["data"]["ws"]["puppeteer"]

    async def stop_profile(self, profile_id: str):
        await self.client.get(f"{ADS_API}/browser/stop", params={"user_id": profile_id})

    async def close(self):
        await self.client.aclose()
