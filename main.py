from fastapi import FastAPI
import uvicorn
from mysite.api import (deliveries, inventory, locations, reservations,
                        router_stop, router, tracking, warehouse, couriers)
from mysite.admin.setup import setup_admin


logistic_app = FastAPI(title=" Seconds microservice")
logistic_app.include_router(warehouse.warehouse_router)
logistic_app.include_router(inventory.inventory_router)
logistic_app.include_router(reservations.reservation_router)
logistic_app.include_router(couriers.courier_router)
logistic_app.include_router(locations.location_router)
logistic_app.include_router(deliveries.delivery_router)
logistic_app.include_router(router.route_router)
logistic_app.include_router(router_stop.router_stop_router)
logistic_app.include_router(tracking.tracking_router)
setup_admin(logistic_app)


if __name__ == "__main__":
    uvicorn.run(logistic_app, host='127.0.0.1', port=8001)