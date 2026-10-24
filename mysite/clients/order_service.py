import httpx
from fastapi import HTTPException
from mysite.config import ORDER_SERVICE_URL
from mysite.clients.auth_service import get_current_user


async def get_order(order_id: int, token: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{ORDER_SERVICE_URL}/orders/{order_id}",headers={"Authorization": f"Bearer {token}"})
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404,detail="Заказ не найден")
            if e.response.status_code in (401, 403):
                raise HTTPException(status_code=e.response.status_code,detail="Нет доступа к заказу или токен недействителен")
            raise HTTPException(status_code=502,detail="Ошибка сервиса заказов")
        except httpx.RequestError:
            raise HTTPException(status_code=503,detail="Сервис заказов недоступен")


async def get_user_order(order_id: int, token: str):
    user = await get_current_user(token)
    order = await get_order(order_id, token)

    if order.get("user_id") != user["id"]:
        raise HTTPException(status_code=403,detail="Этот заказ принадлежит другому пользователю")

    return order