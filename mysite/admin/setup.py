from sqladmin import Admin
from mysite.database.db import engine
from mysite.admin.view import (
    WarehouseAdmin, InventoryAdmin, InventoryReservationAdmin,
    CourierAdmin, CourierLocationAdmin, DeliveryAdmin,
    RouteAdmin, RouteStopAdmin, TrackingEventAdmin,
)


def setup_admin(app):
    admin = Admin(app, engine, title="Logistic Admin")
    for view in [WarehouseAdmin, InventoryAdmin, InventoryReservationAdmin,
                 CourierAdmin, CourierLocationAdmin, DeliveryAdmin, RouteAdmin,
                 RouteStopAdmin, TrackingEventAdmin]:
        admin.add_view(view)
    return admin
