from django.core.mail import send_mail
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import (
    TipoInstrumento,
    Instrumento,
    ImagenInstrumento,
    ListaDeseos,
    Orden,
    ConfirmacionPago,
    Review,
)
from .permissions import IsAdminUser
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    TipoInstrumentoSerializer,
    InstrumentoSerializer,
    ImagenInstrumentoSerializer,
    ListaDeseosSerializer,
    OrdenSerializer,
    ConfirmacionPagoSerializer,
    ReviewSerializer,
)
import os


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer


class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class TipoInstrumentoViewSet(viewsets.ModelViewSet):
    queryset = TipoInstrumento.objects.all()
    serializer_class = TipoInstrumentoSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        parent = self.request.query_params.get("parent")
        if parent is not None:
            if parent.lower() == "null":
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent__id=parent)
        return queryset


class InstrumentoViewSet(viewsets.ModelViewSet):
    queryset = Instrumento.objects.select_related("category").prefetch_related("images")
    serializer_class = InstrumentoSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsAdminUser()]
        if self.action == "additional_info":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset().annotate(
            wishlisted_count=Count('wishlisted_by', distinct=True),
            reviews_count=Count('reviews', distinct=True),
            avg_rating=Avg('reviews__rating')
        )
        category = self.request.query_params.get("category")
        search = self.request.query_params.get("search")
        price_min = self.request.query_params.get("price_min")
        price_max = self.request.query_params.get("price_max")
        ordering = self.request.query_params.get("ordering")

        if category:
            queryset = queryset.filter(
                Q(category__id=category) | Q(category__parent__id=category)
            )
        if search:
            queryset = queryset.filter(name__icontains=search)
        if price_min:
            try:
                queryset = queryset.filter(price__gte=float(price_min))
            except ValueError:
                pass
        if price_max:
            try:
                queryset = queryset.filter(price__lte=float(price_max))
            except ValueError:
                pass

        # Ordering options: popular (wishlists desc), price_asc, price_desc, newest, rating
        if ordering:
            if ordering == 'popular':
                queryset = queryset.order_by('-wishlisted_count')
            elif ordering == 'price_asc':
                queryset = queryset.order_by('price')
            elif ordering == 'price_desc':
                queryset = queryset.order_by('-price')
            elif ordering == 'newest':
                queryset = queryset.order_by('-created_at')
            elif ordering == 'rating':
                queryset = queryset.order_by('-avg_rating')

        return queryset

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdminUser])
    def generate_audio(self, request, pk=None):
        """Genera una muestra de audio usando Hugging Face MusicGen y la guarda en `audio_sample`.

        Espera un body opcional: { "prompt": "texto que describe el sonido" }
        Requiere la variable de entorno `HF_TOKEN` y una opción opcional `HF_MODEL`.
        """
        instrumento = get_object_or_404(Instrumento, pk=pk)
        prompt = request.data.get("prompt") or f"Genera un breve audio de muestra para el instrumento {instrumento.name}."

        token = os.environ.get("HF_TOKEN")
        model = os.environ.get("HF_MODEL", "facebook/musicgen-small")
        if not token:
            return Response({"detail": "HF_TOKEN not configured."}, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(
                f"https://api-inference.huggingface.co/models/{model}",
                json={"inputs": prompt},
                headers=headers,
                timeout=60,
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            return Response({"detail": f"Error calling Hugging Face API: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            audio_bytes = resp.content
            if not audio_bytes:
                return Response({"detail": "No audio data returned from Hugging Face."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            filename = f"instrument_{instrumento.id}_sample.wav"
            instrumento.audio_sample.save(filename, ContentFile(audio_bytes), save=True)
            serializer = InstrumentoSerializer(instrumento, context={"request": request})
            return Response(serializer.data)
        except Exception as e:
            return Response({"detail": f"Error saving audio file: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["get"], permission_classes=[AllowAny])
    def additional_info(self, request, pk=None):
        """Obtiene información adicional del instrumento: origen, categoría, etc."""
        instrumento = get_object_or_404(Instrumento, pk=pk)
        
        result = {
            "instrumento_id": instrumento.id,
            "instrumento_name": instrumento.name,
            "categoria": str(instrumento.category),
            "origen": instrumento.origen or "No especificado",
        }
        
        return Response(result)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related('user', 'instrumento').all()
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.action in ['create']:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        qs = super().get_queryset()
        instrumento = self.request.query_params.get('instrumento')
        if instrumento:
            qs = qs.filter(instrumento__id=instrumento).order_by('-created_at')
        return qs

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def generate_audio(self, request, pk=None):
        """Genera una muestra de audio usando Hugging Face MusicGen y la guarda en `audio_sample`.

        Espera un body opcional: { "prompt": "texto que describe el sonido" }
        Requiere la variable de entorno `HF_TOKEN` y una opción opcional `HF_MODEL`.
        """
        instrumento = get_object_or_404(Instrumento, pk=pk)
        prompt = request.data.get("prompt") or f"Genera un breve audio de muestra para el instrumento {instrumento.name}."

        token = os.environ.get("HF_TOKEN")
        model = os.environ.get("HF_MODEL", "facebook/musicgen-small")
        if not token:
            return Response({"detail": "HF_TOKEN not configured."}, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(
                f"https://api-inference.huggingface.co/models/{model}",
                json={"inputs": prompt},
                headers=headers,
                timeout=60,
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            return Response({"detail": f"Error calling Hugging Face API: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            audio_bytes = resp.content
            if not audio_bytes:
                return Response({"detail": "No audio data returned from Hugging Face."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            filename = f"instrument_{instrumento.id}_sample.wav"
            instrumento.audio_sample.save(filename, ContentFile(audio_bytes), save=True)
            serializer = InstrumentoSerializer(instrumento, context={"request": request})
            return Response(serializer.data)
        except Exception as e:
            return Response({"detail": f"Error saving audio file: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ImagenInstrumentoUploadView(generics.CreateAPIView):
    serializer_class = ImagenInstrumentoSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = ListaDeseosSerializer

    def get_queryset(self):
        return ListaDeseos.objects.filter(user=self.request.user)

    def get_permissions(self):
        if self.action in ["list", "create", "destroy"]:
            return [IsAuthenticated()]
        return [IsAuthenticated()]


class OrdenViewSet(viewsets.ModelViewSet):
    serializer_class = OrdenSerializer

    def get_queryset(self):
        if self.request.user.is_admin():
            return Orden.objects.all()
        return Orden.objects.filter(user=self.request.user)

    def get_permissions(self):
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        order = serializer.save()
        send_mail(
            subject="Confirmación de compra EnFA",
            message=f"Gracias por tu compra. Tu orden #{order.id} ha sido registrada con un total de {order.total}.",
            from_email=None,
            recipient_list=[order.user.email],
            fail_silently=True,
        )
        order.email_confirmed = True
        order.status = "paid"
        order.save()


class ConfirmacionPagoViewSet(viewsets.ModelViewSet):
    queryset = ConfirmacionPago.objects.all()
    serializer_class = ConfirmacionPagoSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]
