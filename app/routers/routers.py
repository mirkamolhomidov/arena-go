from app.routers import regions

class Routes:
    def __init__(self, app):
        self.app = app
        self.app.include_router(regions.regionsRouter)