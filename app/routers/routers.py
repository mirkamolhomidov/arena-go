from app.routers import regions, stadiums

class Routes:
    def __init__(self, prefix, app):
        self.app = app
        self.app.include_router(regions.regionsRouter, prefix=prefix)
        self.app.include_router(stadiums.stadiumsRouter, prefix=prefix)