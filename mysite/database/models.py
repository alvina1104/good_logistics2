from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (String, Integer, Float, DateTime, ForeignKey,Enum, CheckConstraint, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from mysite.database.db import Base


class WarehouseStatus(str, PyEnum):
    active = "active"
    inactive = "inactive"
    maintenance = "maintenance"


class ReservationStatus(str, PyEnum):
    active = "active"
    committed = "committed"
    released = "released"
    expired = "expired"


class TransportType(str, PyEnum):
    walking = "walking"
    bicycle = "bicycle"
    motorcycle = "motorcycle"
    car = "car"


class CourierStatus(str, PyEnum):
    offline = "offline"
    available = "available"
    busy = "busy"
    suspended = "suspended"


class DeliveryStatus(str, PyEnum):
    pending = "pending"
    assigned = "assigned"
    picked_up = "picked_up"
    in_transit = "in_transit"
    delivered = "delivered"
    cancelled = "cancelled"


class RouteStatus(str, PyEnum):
    planned = "planned"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


class StopType(str, PyEnum):
    pickup = "pickup"
    dropoff = "dropoff"


class StopStatus(str, PyEnum):
    pending = "pending"
    arrived = "arrived"
    completed = "completed"
    skipped = "skipped"


class Warehouse(Base):
    __tablename__ = "warehouse"
    __table_args__ = (
        CheckConstraint("capacity >= 0", name="check_warehouse_capacity"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    city_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    street: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[WarehouseStatus] = mapped_column(
        Enum(WarehouseStatus), default=WarehouseStatus.active, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    inventory = relationship("Inventory", back_populates="warehouse")
    couriers = relationship("Courier", back_populates="warehouse")
    deliveries = relationship("Delivery", back_populates="warehouse")


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "product_id", name="uq_warehouse_product"),
        CheckConstraint("quantity >= 0", name="check_inventory_quantity"),
        CheckConstraint(
            "reserved_quantity >= 0 AND reserved_quantity <= quantity",
            name="check_reserved_quantity"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouse.id"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    warehouse = relationship("Warehouse", back_populates="inventory")
    reservations = relationship("InventoryReservation", back_populates="inventory")


class InventoryReservation(Base):
    __tablename__ = "inventory_reservation"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_reservation_quantity"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    inventory_id: Mapped[int] = mapped_column(
        ForeignKey("inventory.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus), default=ReservationStatus.active, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    inventory = relationship("Inventory", back_populates="reservations")


class Courier(Base):
    __tablename__ = "courier"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouse.id"), nullable=False
    )
    transport_type: Mapped[TransportType] = mapped_column(
        Enum(TransportType), nullable=False
    )
    status: Mapped[CourierStatus] = mapped_column(
        Enum(CourierStatus), default=CourierStatus.offline, nullable=False
    )
    max_active_orders: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    warehouse = relationship("Warehouse", back_populates="couriers")
    locations = relationship("CourierLocation", back_populates="courier")
    deliveries = relationship("Delivery", back_populates="courier")
    routes = relationship("Route", back_populates="courier")


class CourierLocation(Base):
    __tablename__ = "courier_location"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    courier_id: Mapped[int] = mapped_column(
        ForeignKey("courier.id"), nullable=False, index=True
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    courier = relationship("Courier", back_populates="locations")


class Delivery(Base):
    __tablename__ = "delivery"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouse.id"), nullable=False
    )
    courier_id: Mapped[int | None] = mapped_column(ForeignKey("courier.id"))
    tracking_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus), default=DeliveryStatus.pending, nullable=False
    )
    destination_address: Mapped[str] = mapped_column(String(255), nullable=False)
    destination_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    destination_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_delivery_at: Mapped[datetime | None] = mapped_column(DateTime)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    warehouse = relationship("Warehouse", back_populates="deliveries")
    courier = relationship("Courier", back_populates="deliveries")
    route_stops = relationship("RouteStop", back_populates="delivery")
    tracking_events = relationship("TrackingEvent", back_populates="delivery")


class Route(Base):
    __tablename__ = "route"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    courier_id: Mapped[int] = mapped_column(ForeignKey("courier.id"), nullable=False)
    status: Mapped[RouteStatus] = mapped_column(
        Enum(RouteStatus), default=RouteStatus.planned, nullable=False
    )
    total_distance_km: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    estimated_duration_min: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    courier = relationship("Courier", back_populates="routes")
    stops = relationship("RouteStop", back_populates="route")


class RouteStop(Base):
    __tablename__ = "route_stop"
    __table_args__ = (
        UniqueConstraint("route_id", "sequence", name="uq_route_stop_sequence"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("route.id"), nullable=False)
    delivery_id: Mapped[int] = mapped_column(ForeignKey("delivery.id"), nullable=False)
    stop_type: Mapped[StopType] = mapped_column(Enum(StopType), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[StopStatus] = mapped_column(
        Enum(StopStatus), default=StopStatus.pending, nullable=False
    )
    arrived_at: Mapped[datetime | None] = mapped_column(DateTime)

    route = relationship("Route", back_populates="stops")
    delivery = relationship("Delivery", back_populates="route_stops")


class TrackingEvent(Base):
    __tablename__ = "tracking_event"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    delivery_id: Mapped[int] = mapped_column(
        ForeignKey("delivery.id"), nullable=False, index=True
    )
    status: Mapped[DeliveryStatus] = mapped_column(Enum(DeliveryStatus), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    description: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    delivery = relationship("Delivery", back_populates="tracking_events")
