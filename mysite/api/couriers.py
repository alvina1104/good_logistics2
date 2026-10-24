
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.database.db import get_db
from mysite.database.models import Courier, Warehouse, Delivery, CourierStatus, DeliveryStatus
from mysite.database.schema import CourierCreate, CourierUpdate, CourierRead

courier_router = APIRouter(prefix="/couriers", tags=["Couriers"])


@courier_router.post("/", response_model=CourierRead, status_code=201)
def create_courier(data: CourierCreate, db: Session = Depends(get_db)):
    if not db.get(Warehouse, data.warehouse_id):
        raise HTTPException(404, "Склад не найден")
    if data.max_active_orders < 1:
        raise HTTPException(400, "Количество активных заказов должно быть больше нуля")
    courier = Courier(**data.model_dump(), status=CourierStatus.offline)
    db.add(courier)
    db.commit()
    db.refresh(courier)
    return courier


@courier_router.get("/", response_model=list[CourierRead])
def get_couriers(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return db.query(Courier).offset(skip).limit(limit).all()


@courier_router.get("/{courier_id}", response_model=CourierRead)
def get_courier(courier_id: int, db: Session = Depends(get_db)):
    courier = db.get(Courier, courier_id)
    if not courier:
        raise HTTPException(404, "Курьер не найден")
    return courier


@courier_router.patch("/{courier_id}", response_model=CourierRead)
def update_courier(courier_id: int, data: CourierUpdate, db: Session = Depends(get_db)):
    courier = db.get(Courier, courier_id)
    if not courier:
        raise HTTPException(404, "Курьер не найден")

    values = data.model_dump(exclude_unset=True)
    if "warehouse_id" in values and not db.get(Warehouse, values["warehouse_id"]):
        raise HTTPException(404, "Склад не найден")
    if values.get("max_active_orders", courier.max_active_orders) < 1:
        raise HTTPException(400, "Количество активных заказов должно быть больше нуля")
    if values.get("status") == CourierStatus.suspended and any(d.status in [DeliveryStatus.assigned, DeliveryStatus.picked_up, DeliveryStatus.in_transit] for d in courier.deliveries):
        raise HTTPException(400, "Нельзя приостановить курьера с активными доставками")

    for key, value in values.items():
        setattr(courier, key, value)
    db.commit()
    db.refresh(courier)
    return courier


@courier_router.delete("/{courier_id}", status_code=204)
def delete_courier(courier_id: int, db: Session = Depends(get_db)):
    courier = db.get(Courier, courier_id)
    if not courier:
        raise HTTPException(404, "Курьер не найден")
    if courier.deliveries:
        raise HTTPException(400, "Нельзя удалить курьера, связанного с доставками")
    if courier.routes:
        raise HTTPException(400, "Нельзя удалить курьера, связанного с маршрутами")
    db.delete(courier)
    db.commit()
