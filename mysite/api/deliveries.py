
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.database.db import get_db
from mysite.database.models import Delivery, Warehouse, Courier, TrackingEvent, DeliveryStatus, CourierStatus
from mysite.database.schema import DeliveryCreate, DeliveryUpdate, DeliveryRead

delivery_router = APIRouter(prefix="/deliveries", tags=["Deliveries"])

ACTIVE_STATUSES = [DeliveryStatus.assigned, DeliveryStatus.picked_up, DeliveryStatus.in_transit]
ALLOWED_TRANSITIONS = {
    DeliveryStatus.pending: [DeliveryStatus.assigned, DeliveryStatus.cancelled],
    DeliveryStatus.assigned: [DeliveryStatus.picked_up, DeliveryStatus.cancelled],
    DeliveryStatus.picked_up: [DeliveryStatus.in_transit, DeliveryStatus.cancelled],
    DeliveryStatus.in_transit: [DeliveryStatus.delivered],
    DeliveryStatus.delivered: [],
    DeliveryStatus.cancelled: [],
}


def add_tracking_event(db: Session, delivery: Delivery, description: str | None = None):
    db.add(TrackingEvent(delivery_id=delivery.id, status=delivery.status, latitude=delivery.destination_latitude,
                         longitude=delivery.destination_longitude, description=description))


@delivery_router.post("/", response_model=DeliveryRead, status_code=201)
def create_delivery(data: DeliveryCreate, db: Session = Depends(get_db)):
    if not db.get(Warehouse, data.warehouse_id):
        raise HTTPException(404, "Склад не найден")
    if db.query(Delivery).filter_by(order_id=data.order_id).first():
        raise HTTPException(409, "Для этого заказа доставка уже создана")
    if not -90 <= data.destination_latitude <= 90 or not -180 <= data.destination_longitude <= 180:
        raise HTTPException(400, "Некорректные GPS-координаты")

    delivery = Delivery(**data.model_dump(), tracking_code=uuid4().hex[:12].upper(), status=DeliveryStatus.pending)
    db.add(delivery)
    db.flush()
    add_tracking_event(db, delivery, "Доставка создана")
    db.commit()
    db.refresh(delivery)
    return delivery


@delivery_router.get("/", response_model=list[DeliveryRead])
def get_deliveries(db: Session = Depends(get_db), skip: int = 0, limit: int = 100, status: DeliveryStatus | None = None):
    query = db.query(Delivery)
    if status:
        query = query.filter(Delivery.status == status)
    return query.order_by(Delivery.created_at.desc()).offset(skip).limit(limit).all()


@delivery_router.get("/tracking/{tracking_code}", response_model=DeliveryRead)
def get_delivery_by_tracking(tracking_code: str, db: Session = Depends(get_db)):
    delivery = db.query(Delivery).filter_by(tracking_code=tracking_code).first()
    if not delivery:
        raise HTTPException(404, "Доставка по tracking-коду не найдена")
    return delivery


@delivery_router.get("/{delivery_id}", response_model=DeliveryRead)
def get_delivery(delivery_id: int, db: Session = Depends(get_db)):
    delivery = db.get(Delivery, delivery_id)
    if not delivery:
        raise HTTPException(404, "Доставка не найдена")
    return delivery


@delivery_router.patch("/{delivery_id}", response_model=DeliveryRead)
def update_delivery(delivery_id: int, data: DeliveryUpdate, db: Session = Depends(get_db)):
    delivery = db.get(Delivery, delivery_id)
    if not delivery:
        raise HTTPException(404, "Доставка не найдена")

    values = data.model_dump(exclude_unset=True)
    if "courier_id" in values and values["courier_id"] is not None:
        courier = db.get(Courier, values["courier_id"])
        if not courier:
            raise HTTPException(404, "Курьер не найден")
        if courier.status != CourierStatus.available:
            raise HTTPException(400, "Курьер недоступен")
        active_count = db.query(Delivery).filter(Delivery.courier_id == courier.id, Delivery.status.in_(ACTIVE_STATUSES), Delivery.id != delivery.id).count()
        if active_count >= courier.max_active_orders:
            raise HTTPException(400, "Курьер достиг лимита активных доставок")
        if delivery.status != DeliveryStatus.pending:
            raise HTTPException(400, "Назначать курьера можно только для новой доставки")
        delivery.status = DeliveryStatus.assigned

    if "status" in values:
        new_status = values.pop("status")
        if new_status not in ALLOWED_TRANSITIONS[delivery.status]:
            raise HTTPException(400, "Недопустимый переход статуса доставки")
        delivery.status = new_status
        if new_status == DeliveryStatus.delivered:
            from datetime import datetime, timezone
            delivery.delivered_at = datetime.now(timezone.utc)
        if new_status == DeliveryStatus.cancelled:
            delivery.courier_id = None

    for key, value in values.items():
        setattr(delivery, key, value)

    db.flush()
    add_tracking_event(db, delivery, "Статус доставки обновлён")
    db.commit()
    db.refresh(delivery)
    return delivery


@delivery_router.delete("/{delivery_id}", status_code=204)
def delete_delivery(delivery_id: int, db: Session = Depends(get_db)):
    delivery = db.get(Delivery, delivery_id)
    if not delivery:
        raise HTTPException(404, "Доставка не найдена")
    if delivery.status not in [DeliveryStatus.pending, DeliveryStatus.cancelled]:
        raise HTTPException(400, "Можно удалить только новую или отменённую доставку")
    if delivery.route_stops:
        raise HTTPException(400, "Сначала удалите остановки маршрута")
    db.delete(delivery)
    db.commit()
