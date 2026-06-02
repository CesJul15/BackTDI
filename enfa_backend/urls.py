# ============================================================
# RUTAS PRINCIPALES DE LA API
# ============================================================
# Aquí se definen todos los endpoints que usa el frontend

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from store.views import (
    RegisterView,
    CurrentUserView,
    TipoInstrumentoViewSet,
    InstrumentoViewSet,
    ImagenInstrumentoUploadView,
    WishlistViewSet,
    OrdenViewSet,
    ConfirmacionPagoViewSet,
    ReviewViewSet,
)

# Router automático para CRUD de recursos
router = DefaultRouter()
router.register(r"tipos", TipoInstrumentoViewSet, basename="tipo")
router.register(r"instrumentos", InstrumentoViewSet, basename="instrumento")
router.register(r"wishlist", WishlistViewSet, basename="wishlist")
router.register(r"ordenes", OrdenViewSet, basename="orden")
router.register(r"confirmaciones", ConfirmacionPagoViewSet, basename="confirmacion")
router.register(r"reviews", ReviewViewSet, basename="review")

urlpatterns = [
    # Admin panel
    path("admin/", admin.site.urls),
    
    # ============================================================
    # AUTENTICACIÓN
    # ============================================================
    # /api/auth/register/ - Crear nuevo usuario
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    # /api/auth/login/ - Obtener tokens JWT (username + password)
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    # /api/auth/refresh/ - Renovar token de acceso usando refresh token
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # /api/auth/me/ - Obtener datos del usuario actual
    path("api/auth/me/", CurrentUserView.as_view(), name="current_user"),
    
    # ============================================================
    # SUBIDA DE IMÁGENES
    # ============================================================
    # /api/upload-image/ - Subir imagen de instrumento (solo admin)
    path("api/upload-image/", ImagenInstrumentoUploadView.as_view(), name="upload_image"),
    
    # ============================================================
    # RECURSOS (CRUD automático generado por router)
    # ============================================================
    # /api/tipos/ - GET (listar categorías), POST (crear)
    # /api/instrumentos/ - GET (listar), POST (crear)
    # /api/wishlist/ - GET (lista de deseos usuario), POST (agregar)
    # /api/ordenes/ - GET (órdenes usuario), POST (crear orden)
    # /api/confirmaciones/ - GET, POST (pagos)
    # /api/reviews/ - GET (reseñas), POST (crear reseña)
    path("api/", include(router.urls)),
]

# Servir archivos estáticos y media (imágenes)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
