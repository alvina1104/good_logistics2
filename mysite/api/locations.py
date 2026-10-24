
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.database.db import get_db
from mysite.database.models import Courier, CourierLocation
from mysite.database.schema import CourierLocationCreate, CourierLocationRead

location_router = APIRouter(prefix="/locations", tags=["Courier Locations"])


@location_router.post("/", response_model=CourierLocationRead, status_code=201)
def create_location(data: CourierLocationCreate, db: Session = Depends(get_db)):
    if not db.get(Courier, data.courier_id):
        raise HTTPException(404, "Курьер не найден")
    if not -90 <= data.latitude <= 90 or not -180 <= data.longitude <= 180:
        raise HTTPException(400, "Некорректные GPS-координаты")

    location = CourierLocation(**data.model_dump())
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


@location_router.get("/courier/{courier_id}/latest", response_model=CourierLocationRead)
def get_latest_location(courier_id: int, db: Session = Depends(get_db)):
    if not db.get(Courier, courier_id):
        raise HTTPException(404, "Курьер не найден")
    location = db.query(CourierLocation).filter_by(courier_id=courier_id).order_by(CourierLocation.recorded_at.desc()).first()
    if not location:
        raise HTTPException(404, "Местоположение курьера не найдено")
    return location


@location_router.get("/courier/{courier_id}/history", response_model=list[CourierLocationRead])
def get_location_history(courier_id: int, db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    if not db.get(Courier, courier_id):
        raise HTTPException(404, "Курьер не найден")
    return db.query(CourierLocation).filter_by(courier_id=courier_id).order_by(CourierLocation.recorded_at.desc()).offset(skip).limit(limit).all()


@location_router.get("/{location_id}", response_model=CourierLocationRead)
def get_location(location_id: int, db: Session = Depends(get_db)):
    location = db.get(CourierLocation, location_id)
    if not location:
        raise HTTPException(404, "Местоположение не найдено")
    return location


@location_router.delete("/{location_id}", status_code=204)
def delete_location(location_id: int, db: Session = Depends(get_db)):
    location = db.get(CourierLocation, location_id)
    if not location:
        raise HTTPException(404, "Местоположение не найдено")
    db.delete(location)
    db.commit()
