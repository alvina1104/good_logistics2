from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.database.db import get_db
from mysite.database.models import Route, Delivery, RouteStop, RouteStatus, StopStatus
from mysite.database.schema import RouteStopCreate, RouteStopUpdate, RouteStopRead

router_stop_router = APIRouter(prefix="/route-stops", tags=["Route Stops"])


@router_stop_router.post("/", response_model=RouteStopRead, status_code=201)
def create_route_stop(data: RouteStopCreate, db: Session = Depends(get_db)):
    route = db.get(Route, data.route_id)
    delivery = db.get(Delivery, data.delivery_id)

    if not route:
        raise HTTPException(404, "Маршрут не найден")
    if not delivery:
        raise HTTPException(404, "Доставка не найдена")
    if route.status != RouteStatus.planned:
        raise HTTPException(400, "Остановки можно добавлять только в запланированный маршрут")
    if data.sequence < 1:
        raise HTTPException(400, "Номер остановки должен быть больше нуля")
    if not -90 <= data.latitude <= 90 or not -180 <= data.longitude <= 180:
        raise HTTPException(400, "Некорректные GPS-координаты")
    if db.query(RouteStop).filter_by(route_id=data.route_id, sequence=data.sequence).first():
        raise HTTPException(409, "Этот номер остановки уже занят")
    if db.query(RouteStop).filter_by(route_id=data.route_id, delivery_id=data.delivery_id, stop_type=data.stop_type).first():
        raise HTTPException(409, "Такая остановка уже есть в маршруте")

    stop = RouteStop(**data.model_dump(), status=StopStatus.pending)
    db.add(stop)
    db.commit()
    db.refresh(stop)
    return stop


@router_stop_router.get("/", response_model=list[RouteStopRead])
def get_route_stops(db: Session = Depends(get_db), route_id: int | None = None, skip: int = 0, limit: int = 100):
    query = db.query(RouteStop)
    if route_id is not None:
        query = query.filter(RouteStop.route_id == route_id)
    return query.order_by(RouteStop.sequence).offset(skip).limit(limit).all()


@router_stop_router.get("/{stop_id}", response_model=RouteStopRead)
def get_route_stop(stop_id: int, db: Session = Depends(get_db)):
    stop = db.get(RouteStop, stop_id)
    if not stop:
        raise HTTPException(404, "Остановка маршрута не найдена")
    return stop


@router_stop_router.patch("/{stop_id}", response_model=RouteStopRead)
def update_route_stop(stop_id: int, data: RouteStopUpdate, db: Session = Depends(get_db)):
    stop = db.get(RouteStop, stop_id)
    if not stop:
        raise HTTPException(404, "Остановка маршрута не найдена")

    values = data.model_dump(exclude_unset=True)
    if "status" in values:
        transitions = {
            StopStatus.pending: [StopStatus.arrived, StopStatus.skipped],
            StopStatus.arrived: [StopStatus.completed, StopStatus.skipped],
            StopStatus.completed: [],
            StopStatus.skipped: [],
        }
        if values["status"] != stop.status and values["status"] not in transitions[stop.status]:
            raise HTTPException(400, "Недопустимый переход статуса остановки")
        if values["status"] == StopStatus.arrived and not values.get("arrived_at"):
            from datetime import datetime, timezone
            values["arrived_at"] = datetime.now(timezone.utc)

    for key, value in values.items():
        setattr(stop, key, value)

    db.commit()
    db.refresh(stop)
    return stop


@router_stop_router.delete("/{stop_id}", status_code=204)
def delete_route_stop(stop_id: int, db: Session = Depends(get_db)):
    stop = db.get(RouteStop, stop_id)
    if not stop:
        raise HTTPException(404, "Остановка маршрута не найдена")
    if stop.route.status != RouteStatus.planned:
        raise HTTPException(400, "Удалять остановки можно только из запланированного маршрута")

    db.delete(stop)
    db.commit()
