# ============================================================
# MODELOS DE LA BASE DE DATOS
# ============================================================
# Aquí se definen todas las tablas de la base de datos

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models


# ============================================================
# Usuario personalizado
# ============================================================
# Extiende el usuario de Django con rol (admin o user)
class User(AbstractUser):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("user", "Usuario"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")

    def is_admin(self):
        return self.role == "admin" or self.is_staff


# ============================================================
# Tipo de Instrumento (categorías)
# ============================================================
# Guarda las categorías de instrumentos (Cuerdas, Viento, Percusión, etc.)
# parent: permite tener subcategorías (jerarquía)
class TipoInstrumento(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="subtypes",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Tipo de Instrumento"
        verbose_name_plural = "Tipos de Instrumento"

    def __str__(self):
        return self.name


# ============================================================
# Instrumento Musical
# ============================================================
# Guarda cada instrumento: nombre, precio, stock, imágenes, reseñas, etc.
# category: relación con TipoInstrumento
# origen: país o región de fabricación
class Instrumento(models.Model):
    category = models.ForeignKey(TipoInstrumento, related_name="instrumentos", on_delete=models.CASCADE)
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)])
    stock = models.PositiveIntegerField(default=0)
    origen = models.CharField(max_length=100, blank=True, help_text="País o región de origen del instrumento")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Instrumento"
        verbose_name_plural = "Instrumentos"

    def __str__(self):
        return self.name


# ============================================================
# Imágenes del Instrumento
# ============================================================
# Guarda múltiples imágenes por cada instrumento
class ImagenInstrumento(models.Model):
    instrumento = models.ForeignKey(Instrumento, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="instrumentos/")
    alt_text = models.CharField(max_length=180, blank=True)

    def __str__(self):
        return f"Imagen de {self.instrumento.name}"


# ============================================================
# Lista de Deseos (Wishlist)
# ============================================================
# Cada usuario puede tener una lista de instrumentos que le gustan
class ListaDeseos(models.Model):
    user = models.ForeignKey(User, related_name="wishlist", on_delete=models.CASCADE)
    instrumento = models.ForeignKey(Instrumento, related_name="wishlisted_by", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "instrumento")
        verbose_name = "Lista de Deseos"
        verbose_name_plural = "Listas de Deseos"

    def __str__(self):
        return f"{self.user.username} - {self.instrumento.name}"


# ============================================================
# Orden de Compra
# ============================================================
# Guarda cada compra que hace un usuario
# status: pending (pendiente), paid (pagado), cancelled (cancelado)
class Orden(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("paid", "Pagado"),
        ("cancelled", "Cancelado"),
    ]
    user = models.ForeignKey(User, related_name="orders", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    email_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"Orden #{self.id} - {self.user.username}"


# ============================================================
# Items de la Orden
# ============================================================
# Cada instrumento comprado en una orden (puede haber varios por orden)
class OrdenItem(models.Model):
    order = models.ForeignKey(Orden, related_name="items", on_delete=models.CASCADE)
    instrumento = models.ForeignKey(Instrumento, related_name="order_items", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.instrumento.name}"


# ============================================================
# Confirmación de Pago
# ============================================================
# Guarda el estado del pago de cada orden
class ConfirmacionPago(models.Model):
    order = models.OneToOneField(Orden, related_name="confirmacion", on_delete=models.CASCADE)
    payment_status = models.CharField(max_length=50, default="pending")
    confirmed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pago orden {self.order.id} - {self.payment_status}"


# ============================================================
# Reseñas y Calificaciones
# ============================================================
# Usuarios pueden dejar comentarios y calificaciones en instrumentos
class Review(models.Model):
    instrumento = models.ForeignKey(Instrumento, related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="reviews", on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Reseña"
        verbose_name_plural = "Reseñas"

    def __str__(self):
        u = self.user.username if self.user else "Anónimo"
        return f"{self.instrumento.name} - {u} ({self.rating})"
