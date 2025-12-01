import httpx

INVENTORY_URL = "http://127.0.0.1:9004"

async def reserve_items(order_items):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{INVENTORY_URL}/inventory/reserve", json={
            "items": order_items
        })
        return response.json()
