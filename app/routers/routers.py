"""Register API routers on the FastAPI application."""

from app.routers import bookings, regions, stadiums, users


class Routes:
    """Attach all application routers under a common prefix."""

    def __init__(self, prefix, app):
        """Register API routers on the provided FastAPI instance."""
        self.app = app
        self.app.include_router(regions.regionsRouter, prefix=prefix)
        self.app.include_router(stadiums.stadiumsRouter, prefix=prefix)
        self.app.include_router(bookings.bookingsRouter, prefix=prefix)
        self.app.include_router(users.usersRouter, prefix=prefix)
