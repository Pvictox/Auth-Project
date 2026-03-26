from . import auth_router, perfil_router, system_router, test, usuario_router

# List of all routers to be included in the main application (used in main.py)
routers = [
    usuario_router,
    system_router,
    perfil_router,
    auth_router,
    test,
]
