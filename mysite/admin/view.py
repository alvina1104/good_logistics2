from sqladmin import ModelView
from mysite.database.models import (Warehouse, Inventory, InventoryReservation, Courier,
                                    CourierLocation, Delivery, Route, RouteStop, TrackingEvent)


class WarehouseAdmin(ModelView, model=Warehouse):
    column_list = [Warehouse.id, Warehouse.code, Warehouse.name, Warehouse.city_id, Warehouse.status, Warehouse.capacity]
    column_searchable_list = [Warehouse.code, Warehouse.name]
    column_sortable_list = [Warehouse.id, Warehouse.name, Warehouse.status]


class InventoryAdmin(ModelView, model=Inventory):
    column_list = [Inventory.id, Inventory.warehouse_id, Inventory.product_id,
                   Inventory.quantity, Inventory.reserved_quantity]
    column_sortable_list = [Inventory.id, Inventory.quantity]


class InventoryReservationAdmin(ModelView, model=InventoryReservation):
    column_list = [InventoryReservation.id, InventoryReservation.order_id, InventoryReservation.inventory_id,
                   InventoryReservation.quantity, InventoryReservation.status]
    column_sortable_list = [InventoryReservation.id, InventoryReservation.status]


class CourierAdmin(ModelView, model=Courier):
    column_list = [Courier.id, Courier.user_id, Courier.warehouse_id, Courier.transport_type, Courier.status]
    column_searchable_list = [Courier.user_id]
    column_sortable_list = [Courier.id, Courier.status]


class CourierLocationAdmin(ModelView, model=CourierLocation):
    column_list = [CourierLocation.id, CourierLocation.courier_id, CourierLocation.latitude,
                   CourierLocation.longitude, CourierLocation.recorded_at]


class DeliveryAdmin(ModelView, model=Delivery):
    column_list = [Delivery.id, Delivery.order_id, Delivery.warehouse_id,
                   Delivery.courier_id, Delivery.tracking_code, Delivery.status]
    column_searchable_list = [Delivery.tracking_code]
    column_sortable_list = [Delivery.id, Delivery.status]


class RouteAdmin(ModelView, model=Route):
    column_list = [Route.id, Route.courier_id, Route.status,
                   Route.total_distance_km, Route.estimated_duration_min]
    column_sortable_list = [Route.id, Route.status]


class RouteStopAdmin(ModelView, model=RouteStop):
    column_list = [RouteStop.id, RouteStop.route_id, RouteStop.delivery_id,
                   RouteStop.stop_type, RouteStop.sequence, RouteStop.status]
    column_sortable_list = [RouteStop.id, RouteStop.sequence, RouteStop.status]


class TrackingEventAdmin(ModelView, model=TrackingEvent):
    column_list = [TrackingEvent.id, TrackingEvent.delivery_id, TrackingEvent.status,
                   TrackingEvent.latitude, TrackingEvent.longitude, TrackingEvent.created_at]
    column_sortable_list = [TrackingEvent.id, TrackingEvent.created_at]
