import httpx
from fastapi import HTTPException
from mysite.config import ORDER_SERVICE_URL


async def get_product(product_id: int, token: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{ORDER_SERVICE_URL}/products/{product_id}",headers={"Authorization": f"Bearer {token}"})
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404,detail="Товар не найден")
            if e.response.status_code in (401, 403):
                raise HTTPException(status_code=e.response.status_code,
                    detail="Нет доступа к товару или токен недействителен")
            raise HTTPException(status_code=502,detail="Ошибка сервиса товаров")
        except httpx.RequestError:
            raise HTTPException(status_code=503,detail="Сервис товаров недоступен")