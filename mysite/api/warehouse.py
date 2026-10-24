from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from mysite.database.db import get_db
from mysite.database.models import Warehouse, Inventory, Delivery, Courier
from mysite.database.schema import WarehouseCreate, WarehouseUpdate, WarehouseRead

warehouse_router = APIRouter(prefix="/warehouses", tags=["Warehouses"])


@warehouse_router.post("/", response_model=WarehouseRead, status_code=201)
def create_warehouse(data: WarehouseCreate, db: Session = Depends(get_db)):
    if db.query(Warehouse).filter(Warehouse.code == data.code).first():
        raise HTTPException(status_code=409, detail="Код склада уже существует")

    warehouse = Warehouse(**data.model_dump())
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return warehouse


@warehouse_router.get("/", response_model=list[WarehouseRead])
def get_warehouses(db: Session = Depends(get_db)):
    return db.query(Warehouse).all()


@warehouse_router.get("/{warehouse_id}", response_model=WarehouseRead)
def get_warehouse(warehouse_id: int, db: Session = Depends(get_db)):
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Склад не найден")
    return warehouse


@warehouse_router.put("/{warehouse_id}", response_model=WarehouseRead)
def update_warehouse(
    warehouse_id: int,
    data: WarehouseUpdate,
    db: Session = Depends(get_db),
):
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Склад не найден")

    changes = data.model_dump(exclude_unset=True)

    if "code" in changes:
        existing = db.query(Warehouse).filter(
            Warehouse.code == changes["code"],
            Warehouse.id != warehouse_id,
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Код склада уже используется")

    for key, value in changes.items():
        setattr(warehouse, key, value)

    db.commit()
    db.refresh(warehouse)
    return warehouse


@warehouse_router.delete("/{warehouse_id}")
def delete_warehouse(warehouse_id: int, db: Session = Depends(get_db)):
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Склад не найден")

    if (
        db.query(Inventory).filter(Inventory.warehouse_id == warehouse_id).first()
        or db.query(Delivery).filter(Delivery.warehouse_id == warehouse_id).first()
        or db.query(Courier).filter(Courier.warehouse_id == warehouse_id).first()
    ):
        raise HTTPException(
            status_code=409,
            detail="Нельзя удалить склад, связанный с товарами, доставками или курьерами",
        )

    db.delete(warehouse)
    db.commit()
    return {"message": "Склад успешно удалён"}