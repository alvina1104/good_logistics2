from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from mysite.database.db import get_db
from mysite.database.models import Inventory, Warehouse, InventoryReservation
from mysite.database.schema import InventoryCreate, InventoryUpdate, InventoryRead

inventory_router = APIRouter(prefix="/inventory", tags=["Inventory"])


@inventory_router.post("/", response_model=InventoryRead, status_code=201)
def create_inventory(data: InventoryCreate, db: Session = Depends(get_db)):
    warehouse = db.query(Warehouse).filter(
        Warehouse.id == data.warehouse_id
    ).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Склад не найден")

    if data.quantity < 0 or data.reserved_quantity < 0:
        raise HTTPException(status_code=422, detail="Количество не может быть отрицательным")

    if data.reserved_quantity > data.quantity:
        raise HTTPException(
            status_code=422,detail="Зарезервированное количество не может превышать общий остаток",)
    inventory = db.query(Inventory).filter(
        Inventory.warehouse_id == data.warehouse_id,
        Inventory.product_id == data.product_id,).first()
    if inventory:
        raise HTTPException(status_code=409,detail="Этот товар уже добавлен на данный склад")

    inventory = Inventory(**data.model_dump())
    db.add(inventory)
    db.commit()
    db.refresh(inventory)
    return inventory


@inventory_router.get("/", response_model=list[InventoryRead])
def get_inventory(db: Session = Depends(get_db)):
    return db.query(Inventory).all()


@inventory_router.get("/{inventory_id}", response_model=InventoryRead)
def get_inventory_item(inventory_id: int, db: Session = Depends(get_db)):
    inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Запись остатков не найдена")
    return inventory


@inventory_router.put("/{inventory_id}", response_model=InventoryRead)
def update_inventory(
    inventory_id: int,
    data: InventoryUpdate,
    db: Session = Depends(get_db),
):
    inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Запись остатков не найдена")

    changes = data.model_dump(exclude_unset=True)
    quantity = changes.get("quantity", inventory.quantity)
    reserved = changes.get("reserved_quantity", inventory.reserved_quantity)

    if quantity < 0 or reserved < 0:
        raise HTTPException(status_code=422, detail="Количество не может быть отрицательным")

    if reserved > quantity:
        raise HTTPException(status_code=422,detail="Резерв не может превышать общий остаток")

    for key, value in changes.items():
        setattr(inventory, key, value)

    db.commit()
    db.refresh(inventory)
    return inventory


@inventory_router.delete("/{inventory_id}")
def delete_inventory(inventory_id: int, db: Session = Depends(get_db)):
    inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Запись остатков не найдена")

    if inventory.reservations:
        raise HTTPException(status_code=409,detail="Нельзя удалить товар, у которого есть резервы",)

    db.delete(inventory)
    db.commit()
    return {"message": "Запись остатков успешно удалена"}