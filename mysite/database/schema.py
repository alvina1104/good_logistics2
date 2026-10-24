from datetime import datetime
from pydantic import BaseModel, ConfigDict


class WarehouseCreate(BaseModel):
    city_id: int
    code: str
    name: str
    street: str
    latitude: float
    longitude: float
    capacity: int


class WarehouseUpdate(BaseModel):
    city_id: int | None = None
    code: str | None = None
    name: str | None = None
    street: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    capacity: int | None = None
    status: str | None = None


class WarehouseRead(BaseModel):
    id: int
    city_id: int
    code: str
    name: str
    street: str
    latitude: float
    longitude: float
    capacity: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryCreate(BaseModel):
    warehouse_id: int
    product_id: int
    quantity: int = 0
    reserved_quantity: int = 0


class InventoryUpdate(BaseModel):
    quantity: int | None = None
    reserved_quantity: int | None = None


class InventoryRead(BaseModel):
    id: int
    warehouse_id: int
    product_id: int
    quantity: int
    reserved_quantity: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryReservationCreate(BaseModel):
    order_id: int
    inventory_id: int
    quantity: int
    expires_at: datetime | None = None


class InventoryReservationUpdate(BaseModel):
    quantity: int | None = None
    status: str | None = None
    expires_at: datetime | None = None


class InventoryReservationRead(BaseModel):
    id: int
    order_id: int
    inventory_id: int
    quantity: int
    status: str
    expires_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourierCreate(BaseModel):
    user_id: int
    warehouse_id: int
    transport_type: str
    max_active_orders: int = 5


class CourierUpdate(BaseModel):
    warehouse_id: int | None = None
    transport_type: str | None = None
    status: str | None = None
    max_active_orders: int | None = None


class CourierRead(BaseModel):
    id: int
    user_id: int
    warehouse_id: int
    transport_type: str
    status: str
    max_active_orders: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourierLocationCreate(BaseModel):
    courier_id: int
    latitude: float
    longitude: float


class CourierLocationRead(BaseModel):
    id: int
    courier_id: int
    latitude: float
    longitude: float
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryCreate(BaseModel):
    order_id: int
    warehouse_id: int
    destination_address: str
    destination_latitude: float
    destination_longitude: float
    estimated_delivery_at: datetime | None = None


class DeliveryUpdate(BaseModel):
    courier_id: int | None = None
    status: str | None = None
    destination_address: str | None = None
    destination_latitude: float | None = None
    destination_longitude: float | None = None
    estimated_delivery_at: datetime | None = None
    delivered_at: datetime | None = None


class DeliveryRead(BaseModel):
    id: int
    order_id: int
    warehouse_id: int
    courier_id: int | None
    tracking_code: str
    status: str
    destination_address: str
    destination_latitude: float
    destination_longitude: float
    estimated_delivery_at: datetime | None
    delivered_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RouteCreate(BaseModel):
    courier_id: int


class RouteUpdate(BaseModel):
    status: str | None = None
    total_distance_km: float | None = None
    estimated_duration_min: int | None = None


class RouteRead(BaseModel):
    id: int
    courier_id: int
    status: str
    total_distance_km: float
    estimated_duration_min: int
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RouteStopCreate(BaseModel):
    route_id: int
    delivery_id: int
    stop_type: str
    sequence: int
    latitude: float
    longitude: float


class RouteStopUpdate(BaseModel):
    status: str | None = None
    arrived_at: datetime | None = None


class RouteStopRead(BaseModel):
    id: int
    route_id: int
    delivery_id: int
    stop_type: str
    sequence: int
    latitude: float
    longitude: float
    status: str
    arrived_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class TrackingEventCreate(BaseModel):
    delivery_id: int
    status: str
    latitude: float | None = None
    longitude: float | None = None
    description: str | None = None


class TrackingEventRead(BaseModel):
    id: int
    delivery_id: int
    status: str
    latitude: float | None
    longitude: float | None
    description: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)