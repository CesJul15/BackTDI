from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, TipoInstrumento, Instrumento, ImagenInstrumento, ListaDeseos, Orden, OrdenItem, ConfirmacionPago
from .models import Review


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (("Rol EnFA", {"fields": ("role",)}),)
    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")


@admin.register(TipoInstrumento)
class TipoInstrumentoAdmin(admin.ModelAdmin):
    list_display = ("name", "parent")
    search_fields = ("name",)


class ImagenInstrumentoInline(admin.TabularInline):
    model = ImagenInstrumento
    extra = 1


@admin.register(Instrumento)
class InstrumentoAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock")
    list_filter = ("category",)
    search_fields = ("name", "description")
    inlines = [ImagenInstrumentoInline]
    


@admin.register(ListaDeseos)
class ListaDeseosAdmin(admin.ModelAdmin):
    list_display = ("user", "instrumento", "created_at")
    search_fields = ("user__username", "instrumento__name")


class OrdenItemInline(admin.TabularInline):
    model = OrdenItem
    readonly_fields = ("price",)
    extra = 0


@admin.register(Orden)
class OrdenAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total", "status", "email_confirmed", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username",)
    inlines = [OrdenItemInline]


@admin.register(ConfirmacionPago)
class ConfirmacionPagoAdmin(admin.ModelAdmin):
    list_display = ("order", "payment_status", "confirmed_at")
    search_fields = ("order__id",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("instrumento", "user", "rating", "created_at")
    search_fields = ("instrumento__name", "user__username", "comment")
    list_filter = ("rating",)
