from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.database.db import get_db
from mysite.database.models import Inventory, InventoryReservation, ReservationStatus
from mysite.database.schema import InventoryReservationCreate, InventoryReservationUpdate, InventoryReservationRead

reservation_router = APIRouter(prefix="/reservations", tags=["Reservations"])


@reservation_router.post("/", response_model=InventoryReservationRead, status_code=201)
def create_reservation(data: InventoryReservationCreate, db: Session = Depends(get_db)):
    inventory = db.get(Inventory, data.inventory_id)
    if not inventory:
        raise HTTPException(404, "Товар на складе не найден")
    if data.quantity <= 0:
        raise HTTPException(400, "Количество должно быть больше нуля")
    if inventory.quantity - inventory.reserved_quantity < data.quantity:
        raise HTTPException(400, "Недостаточно свободного товара на складе")

    reservation = InventoryReservation(**data.model_dump(), status=ReservationStatus.active)
    inventory.reserved_quantity += data.quantity
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


@reservation_router.get("/", response_model=list[InventoryReservationRead])
def get_reservations(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return db.query(InventoryReservation).offset(skip).limit(limit).all()


@reservation_router.get("/{reservation_id}", response_model=InventoryReservationRead)
def get_reservation(reservation_id: int, db: Session = Depends(get_db)):
    reservation = db.get(InventoryReservation, reservation_id)
    if not reservation:
        raise HTTPException(404, "Резерв не найден")
    return reservation


@reservation_router.patch("/{reservation_id}", response_model=InventoryReservationRead)
def update_reservation(reservation_id: int, data: InventoryReservationUpdate, db: Session = Depends(get_db)):
    reservation = db.get(InventoryReservation, reservation_id)
    if not reservation:
        raise HTTPException(404, "Резерв не найден")
    if reservation.status != ReservationStatus.active:
        raise HTTPException(400, "Изменять можно только активный резерв")

    values = data.model_dump(exclude_unset=True)
    if "quantity" in values:
        new_quantity = values["quantity"]
        if new_quantity <= 0:
            raise HTTPException(400, "Количество должно быть больше нуля")
        inventory = reservation.inventory
        difference = new_quantity - reservation.quantity
        if inventory.quantity - inventory.reserved_quantity < difference:
            raise HTTPException(400, "Недостаточно свободного товара на складе")
        inventory.reserved_quantity += difference

    if "status" in values or "quantity" in values:
        raise HTTPException(400, "Для изменения резерва используйте /release или /commit")

    for key, value in values.items():
        setattr(reservation, key, value)
    db.commit()
    db.refresh(reservation)
    return reservation


@reservation_router.post("/{reservation_id}/release", response_model=InventoryReservationRead)
def release_reservation(reservation_id: int, db: Session = Depends(get_db)):
    reservation = db.get(InventoryReservation, reservation_id)
    if not reservation:
        raise HTTPException(404, "Резерв не найден")
    if reservation.status != ReservationStatus.active:
        raise HTTPException(400, "Резерв уже обработан")

    reservation.inventory.reserved_quantity -= reservation.quantity
    reservation.status = ReservationStatus.released
    db.commit()
    db.refresh(reservation)
    return reservation


@reservation_router.post("/{reservation_id}/commit", response_model=InventoryReservationRead)
def commit_reservation(reservation_id: int, db: Session = Depends(get_db)):
    reservation = db.get(InventoryReservation, reservation_id)
    if not reservation:
        raise HTTPException(404, "Резерв не найден")
    if reservation.status != ReservationStatus.active:
        raise HTTPException(400, "Резерв уже обработан")

    inventory = reservation.inventory
    if inventory.quantity < reservation.quantity or inventory.reserved_quantity < reservation.quantity:
        raise HTTPException(400, "Некорректное состояние складских остатков")

    inventory.quantity -= reservation.quantity
    inventory.reserved_quantity -= reservation.quantity
    reservation.status = ReservationStatus.committed
    db.commit()
    db.refresh(reservation)
    return reservation


@reservation_router.delete("/{reservation_id}", status_code=204)
def delete_reservation(reservation_id: int, db: Session = Depends(get_db)):
    reservation = db.get(InventoryReservation, reservation_id)
    if not reservation:
        raise HTTPException(404, "Резерв не найден")
    if reservation.status == ReservationStatus.active:
        reservation.inventory.reserved_quantity -= reservation.quantity
    db.delete(reservation)
    db.commit()
