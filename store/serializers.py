from django.contrib.auth import get_user_model
from django.db.models import Avg
from rest_framework import serializers
from .models import (
    TipoInstrumento,
    Instrumento,
    ImagenInstrumento,
    ListaDeseos,
    Orden,
    OrdenItem,
    ConfirmacionPago,
    Review,
)
from .external_apis import get_instrument_origin_from_wikipedia

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "first_name", "last_name"]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        return user


class ImagenInstrumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagenInstrumento
        fields = ["id", "image", "alt_text"]


class InstrumentoSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(source="category", queryset=TipoInstrumento.objects.all(), write_only=True)
    images = ImagenInstrumentoSerializer(many=True, read_only=True)
    avg_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()

    class Meta:
        model = Instrumento
        fields = ["id", "name", "description", "price", "stock", "category", "category_id", "images", "avg_rating", "reviews_count", "origen"]

    def create(self, validated_data):
        # Si no se especifica origen, obtenerlo automáticamente de Wikipedia
        if not validated_data.get("origen") or validated_data.get("origen") == "":
            instrument_name = validated_data.get("name", "")
            if instrument_name:
                origin = get_instrument_origin_from_wikipedia(instrument_name)
                if origin:
                    validated_data["origen"] = origin
        return Instrumento.objects.create(**validated_data)

    def get_avg_rating(self, obj):
        agg = obj.reviews.aggregate(avg=Avg('rating'))
        avg = agg.get('avg')
        return round(avg, 1) if avg else None

    def get_reviews_count(self, obj):
        cnt = obj.reviews.count()
        return cnt


class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ["id", "instrumento", "user", "rating", "comment", "created_at"]
        read_only_fields = ["id", "user", "created_at"]

    def create(self, validated_data):
        user = self.context['request'].user if self.context['request'].user and self.context['request'].user.is_authenticated else None
        review = Review.objects.create(user=user, **validated_data)
        return review


class TipoInstrumentoSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoInstrumento
        fields = ["id", "name", "description"]


class TipoInstrumentoSerializer(serializers.ModelSerializer):
    instrumentos = InstrumentoSerializer(many=True, read_only=True)
    subtypes = TipoInstrumentoSimpleSerializer(many=True, read_only=True)
    parent_id = serializers.PrimaryKeyRelatedField(source="parent", queryset=TipoInstrumento.objects.all(), allow_null=True, required=False)

    class Meta:
        model = TipoInstrumento
        fields = ["id", "name", "description", "parent_id", "subtypes", "instrumentos"]


class ListaDeseosSerializer(serializers.ModelSerializer):
    instrumento = InstrumentoSerializer(read_only=True)
    instrumento_id = serializers.PrimaryKeyRelatedField(source="instrumento", queryset=Instrumento.objects.all(), write_only=True)

    class Meta:
        model = ListaDeseos
        fields = ["id", "instrumento", "instrumento_id", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        wishlist_item, _ = ListaDeseos.objects.get_or_create(user=user, instrumento=validated_data["instrumento"])
        return wishlist_item


class OrdenItemSerializer(serializers.ModelSerializer):
    instrumento = InstrumentoSerializer(read_only=True)
    instrumento_id = serializers.PrimaryKeyRelatedField(source="instrumento", queryset=Instrumento.objects.all(), write_only=True)

    class Meta:
        model = OrdenItem
        fields = ["id", "instrumento", "instrumento_id", "quantity", "price"]
        read_only_fields = ["id", "price"]

    def create(self, validated_data):
        instrumento = validated_data["instrumento"]
        return OrdenItem(
            instrumento=instrumento,
            quantity=validated_data.get("quantity", 1),
            price=instrumento.price,
        )


class OrdenSerializer(serializers.ModelSerializer):
    items = OrdenItemSerializer(many=True)
    status = serializers.CharField(read_only=True)
    email_confirmed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Orden
        fields = ["id", "user", "created_at", "total", "status", "email_confirmed", "items"]
        read_only_fields = ["id", "user", "created_at", "status", "email_confirmed"]

    def create(self, validated_data):
        user = self.context["request"].user
        items_data = validated_data.pop("items")
        order = Orden.objects.create(user=user, total=validated_data.get("total", 0))
        total = 0
        for item_data in items_data:
            item = OrdenItem.objects.create(
                order=order,
                instrumento=item_data["instrumento"],
                quantity=item_data.get("quantity", 1),
                price=item_data["instrumento"].price,
            )
            total += item.price * item.quantity
        order.total = total
        order.save()
        return order


class ConfirmacionPagoSerializer(serializers.ModelSerializer):
    order_id = serializers.PrimaryKeyRelatedField(source="order", queryset=Orden.objects.all())

    class Meta:
        model = ConfirmacionPago
        fields = ["id", "order_id", "payment_status", "confirmed_at"]
