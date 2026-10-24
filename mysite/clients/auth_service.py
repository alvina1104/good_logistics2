import httpx
from fastapi import HTTPException
from mysite.config import AUTH_SERVICE_URL


async def get_current_user(token: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{AUTH_SERVICE_URL}/auth/me/",headers={"Authorization": f"Bearer {token}"})
            response.raise_for_status()
            user = response.json()

            if not user.get("id"):
                raise HTTPException(status_code=502,detail="Сервис авторизации не вернул ID пользователя")

            return user

        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                raise HTTPException(status_code=401,detail="Токен недействителен или истёк")
            raise HTTPException(status_code=502,detail="Ошибка сервиса авторизации")
        except httpx.RequestError:
            raise HTTPException(status_code=503,detail="Сервис авторизации недоступен")