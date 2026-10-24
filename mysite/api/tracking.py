from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.database.db import get_db
from mysite.database.models import Delivery, TrackingEvent
from mysite.database.schema import TrackingEventCreate, TrackingEventRead

tracking_router = APIRouter(tags=["Tracking"])


@tracking_router.post("/tracking-events/", response_model=TrackingEventRead, status_code=201)
def create_tracking_event(data: TrackingEventCreate, db: Session = Depends(get_db)):
    delivery = db.get(Delivery, data.delivery_id)
    if not delivery:
        raise HTTPException(404, "Доставка не найдена")
    if data.latitude is not None and not -90 <= data.latitude <= 90:
        raise HTTPException(400, "Некорректная широта")
    if data.longitude is not None and not -180 <= data.longitude <= 180:
        raise HTTPException(400, "Некорректная долгота")

    event = TrackingEvent(**data.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@tracking_router.get("/tracking-events/", response_model=list[TrackingEventRead])
def get_tracking_events(db: Session = Depends(get_db), delivery_id: int | None = None, skip: int = 0, limit: int = 100):
    query = db.query(TrackingEvent)
    if delivery_id is not None:
        query = query.filter(TrackingEvent.delivery_id == delivery_id)
    return query.order_by(TrackingEvent.created_at.desc()).offset(skip).limit(limit).all()


@tracking_router.get("/deliveries/{delivery_id}/tracking", response_model=list[TrackingEventRead])
def get_delivery_tracking(delivery_id: int, db: Session = Depends(get_db)):
    if not db.get(Delivery, delivery_id):
        raise HTTPException(404, "Доставка не найдена")
    return db.query(TrackingEvent).filter_by(delivery_id=delivery_id).order_by(TrackingEvent.created_at.desc()).all()
