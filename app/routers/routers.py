from app.routers import bookings, regions, stadiums, users

class Routes:
    def __init__(self, prefix, app):
        self.app = app
        self.app.include_router(regions.regionsRouter, prefix=prefix)
        self.app.include_router(stadiums.stadiumsRouter, prefix=prefix)
        self.app.include_router(bookings.bookingsRouter, prefix=prefix)
        self.app.include_router(users.usersRouter, prefix=prefix)