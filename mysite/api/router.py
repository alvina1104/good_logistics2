
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.database.db import get_db
from mysite.database.models import Route, Courier, RouteStatus, CourierStatus
from mysite.database.schema import RouteCreate, RouteUpdate, RouteRead

route_router = APIRouter(prefix="/routes", tags=["Routes"])


@route_router.post("/", response_model=RouteRead, status_code=201)
def create_route(data: RouteCreate, db: Session = Depends(get_db)):
    courier = db.get(Courier, data.courier_id)
    if not courier:
        raise HTTPException(404, "Курьер не найден")
    if courier.status != CourierStatus.available:
        raise HTTPException(400, "Курьер недоступен")

    route = Route(courier_id=data.courier_id, status=RouteStatus.planned, total_distance_km=0, estimated_duration_min=0)
    db.add(route)
    db.commit()
    db.refresh(route)
    return route


@route_router.get("/", response_model=list[RouteRead])
def get_routes(db: Session = Depends(get_db), skip: int = 0, limit: int = 100, status: RouteStatus | None = None):
    query = db.query(Route)
    if status:
        query = query.filter(Route.status == status)
    return query.order_by(Route.created_at.desc()).offset(skip).limit(limit).all()


@route_router.get("/{route_id}", response_model=RouteRead)
def get_route(route_id: int, db: Session = Depends(get_db)):
    route = db.get(Route, route_id)
    if not route:
        raise HTTPException(404, "Маршрут не найден")
    return route


@route_router.patch("/{route_id}", response_model=RouteRead)
def update_route(route_id: int, data: RouteUpdate, db: Session = Depends(get_db)):
    route = db.get(Route, route_id)
    if not route:
        raise HTTPException(404, "Маршрут не найден")

    values = data.model_dump(exclude_unset=True)
    if values.get("total_distance_km", route.total_distance_km) < 0:
        raise HTTPException(400, "Расстояние не может быть отрицательным")
    if values.get("estimated_duration_min", route.estimated_duration_min) < 0:
        raise HTTPException(400, "Продолжительность не может быть отрицательной")

    if "status" in values:
        new_status = values["status"]
        transitions = {
            RouteStatus.planned: [RouteStatus.active, RouteStatus.cancelled],
            RouteStatus.active: [RouteStatus.completed, RouteStatus.cancelled],
            RouteStatus.completed: [],
            RouteStatus.cancelled: [],
        }
        if new_status != route.status and new_status not in transitions[route.status]:
            raise HTTPException(400, "Недопустимый переход статуса маршрута")
        if new_status == RouteStatus.active and route.started_at is None:
            route.started_at = datetime.now(timezone.utc)
        if new_status == RouteStatus.completed:
            route.completed_at = datetime.now(timezone.utc)

    for key, value in values.items():
        setattr(route, key, value)
    db.commit()
    db.refresh(route)
    return route


@route_router.delete("/{route_id}", status_code=204)
def delete_route(route_id: int, db: Session = Depends(get_db)):
    route = db.get(Route, route_id)
    if not route:
        raise HTTPException(404, "Маршрут не найден")
    if route.status == RouteStatus.active:
        raise HTTPException(400, "Нельзя удалить активный маршрут")
    if route.stops:
        raise HTTPException(400, "Сначала удалите остановки маршрута")
    db.delete(route)
    db.commit()
