from django.db.models import Avg, Count
from django.utils import timezone
from django.shortcuts import redirect, render
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from rest_framework import filters, permissions, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import City, Client, CompanyGalleryImage, Deal, District, Favorite, LeadInquiry, Notification, Property, PropertyImage, PropertyType, Realtor
from .auth import CsrfExemptSessionAuthentication
from .serializers import (
    CitySerializer,
    CompanyGalleryImageSerializer,
    DistrictSerializer,
    FavoriteSerializer,
    LeadInquirySerializer,
    LoginSerializer,
    PropertyImageSerializer,
    PropertySerializer,
    PropertyTypeSerializer,
    RegisterSerializer,
    UserSerializer,
)


class PropertyTypeViewSet(viewsets.ModelViewSet):
    queryset = PropertyType.objects.all().order_by("name")
    serializer_class = PropertyTypeSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ("name",)
    ordering_fields = ("name",)


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all().order_by("name")
    serializer_class = CitySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ("name",)
    ordering_fields = ("name",)


class DistrictViewSet(viewsets.ModelViewSet):
    queryset = District.objects.select_related("city").all().order_by("city__name", "name")
    serializer_class = DistrictSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ("name", "city__name")
    ordering_fields = ("name", "city__name")

    def get_queryset(self):
        queryset = super().get_queryset()
        city_id = self.request.query_params.get("city")
        if city_id:
            queryset = queryset.filter(city_id=city_id)
        return queryset


class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.select_related("property_type", "city", "district").prefetch_related("images")
    serializer_class = PropertySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ("title", "address", "description", "city__name", "district__name", "property_type__name")
    ordering_fields = ("price", "area", "created_at", "updated_at")

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        city_id = params.get("city")
        district_id = params.get("district")
        property_type_id = params.get("property_type")
        deal_type = params.get("deal_type")
        status = params.get("status")
        min_price = params.get("min_price")
        max_price = params.get("max_price")
        min_area = params.get("min_area")
        max_area = params.get("max_area")
        rooms = params.get("rooms")
        featured = params.get("featured")

        if city_id:
            queryset = queryset.filter(city_id=city_id)
        if district_id:
            queryset = queryset.filter(district_id=district_id)
        if property_type_id:
            queryset = queryset.filter(property_type_id=property_type_id)
        if deal_type:
            queryset = queryset.filter(deal_type=deal_type)
        if status:
            queryset = queryset.filter(status=status)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if min_area:
            queryset = queryset.filter(area__gte=min_area)
        if max_area:
            queryset = queryset.filter(area__lte=max_area)
        if rooms:
            queryset = queryset.filter(rooms=rooms)
        if featured in {"1", "true", "True", "yes"}:
            queryset = queryset.filter(is_featured=True)

        return queryset


class MyPropertyViewSet(viewsets.ModelViewSet):
    """
    CRUD по объектам конкретного риелтора.
    """

    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = (CsrfExemptSessionAuthentication,)

    def get_queryset(self):
        user = self.request.user
        try:
            realtor = user.realtor_profile
        except Realtor.DoesNotExist:
            return Property.objects.none()

        queryset = (
            Property.objects.select_related("property_type", "city", "district", "realtor")
            .prefetch_related("images")
            .filter(realtor=realtor)
        )

        return queryset

    def _get_realtor(self):
        user = self.request.user
        try:
            return user.realtor_profile
        except Realtor.DoesNotExist:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Только риэлторы могут управлять объектами.")

    def perform_create(self, serializer):
        realtor = self._get_realtor()
        serializer.save(realtor=realtor)

    def perform_update(self, serializer):
        realtor = self._get_realtor()
        # Гарантируем, что объект остаётся за этим риэлтором
        serializer.save(realtor=realtor)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        realtor = self._get_realtor()
        if instance.realtor_id != realtor.id:
            return Response(
                {"detail": "Вы не можете удалить объект другого риэлтора."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


class CompanyGalleryImageViewSet(viewsets.ReadOnlyModelViewSet):
    """Фотографии для главной страницы (галерея компании)."""

    queryset = CompanyGalleryImage.objects.all().order_by("sort_order", "id")
    serializer_class = CompanyGalleryImageSerializer
    permission_classes = [permissions.AllowAny]


class PropertyImageViewSet(viewsets.ModelViewSet):
    queryset = PropertyImage.objects.select_related("property", "property__realtor").all().order_by("id")
    serializer_class = PropertyImageSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    authentication_classes = (CsrfExemptSessionAuthentication,)
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAuthenticated()]

    def _assert_realtor_owns(self, prop):
        user = self.request.user
        if not hasattr(user, "realtor_profile"):
            raise PermissionDenied("Только риэлтор может добавлять или менять фотографии объектов.")
        if prop.realtor_id != user.realtor_profile.id:
            raise PermissionDenied("Можно работать только со своими объектами.")

    def perform_create(self, serializer):
        prop = serializer.validated_data["property"]
        self._assert_realtor_owns(prop)
        serializer.save()

    def perform_update(self, serializer):
        self._assert_realtor_owns(serializer.instance.property)
        serializer.save()

    def perform_destroy(self, instance):
        self._assert_realtor_owns(instance.property)
        instance.delete()


class LeadInquiryViewSet(viewsets.ModelViewSet):
    queryset = LeadInquiry.objects.select_related("city", "property_type").all().order_by("-created_at")
    serializer_class = LeadInquirySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ("full_name", "phone", "email", "message", "city__name", "property_type__name")
    ordering_fields = ("created_at", "updated_at", "status")


class AnalyticsView(APIView):
    def get(self, request):
        properties = Property.objects.all()
        inquiries = LeadInquiry.objects.all()

        now = timezone.now()
        days_30_ago = now - timezone.timedelta(days=30)

        properties_30 = properties.filter(created_at__gte=days_30_ago)
        inquiries_30 = inquiries.filter(created_at__gte=days_30_ago)

        response_data = {
            "supply": {
                "total_properties": properties.count(),
                "active_properties": properties.filter(status="active").count(),
                "sale_properties": properties.filter(deal_type="sale").count(),
                "rent_properties": properties.filter(deal_type="rent").count(),
                "featured_properties": properties.filter(is_featured=True).count(),
            },
            "demand": {
                "total_inquiries": inquiries.count(),
                "new_inquiries": inquiries.filter(status="new").count(),
                "in_progress_inquiries": inquiries.filter(status="in_progress").count(),
            },
            "last_30_days": {
                "new_properties": properties_30.count(),
                "new_inquiries": inquiries_30.count(),
                "avg_price_30": properties_30.aggregate(value=Avg("price"))["value"] or 0,
                "avg_price_all": properties.aggregate(value=Avg("price"))["value"] or 0,
            },
            "average": {
                "price": properties.aggregate(value=Avg("price"))["value"] or 0,
                "area": properties.aggregate(value=Avg("area"))["value"] or 0,
            },
            "by_city": list(
                properties.values("city__name")
                .annotate(count=Count("id"))
                .order_by("-count", "city__name")
            ),
            "by_property_type": list(
                properties.values("property_type__name")
                .annotate(count=Count("id"))
                .order_by("-count", "property_type__name")
            ),
            "inquiries_by_city": list(
                inquiries.values("city__name")
                .annotate(count=Count("id"))
                .order_by("-count", "city__name")
            ),
        }

        return Response(response_data)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user)
        return Response(UserSerializer(user).data, status=201)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"detail": "Вы вышли из системы."})


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        user = request.user
        for field in ("first_name", "last_name", "email"):
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()
        return Response(UserSerializer(user).data)


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = (CsrfExemptSessionAuthentication,)

    def get_queryset(self):
        user = self.request.user
        try:
            client = user.client_profile
        except Client.DoesNotExist:
            return Favorite.objects.none()
        return Favorite.objects.filter(client=client).select_related("property")

    def perform_create(self, serializer):
        user = self.request.user
        # Риэлторам нельзя добавлять избранное: в UI для них
        # кнопки должны быть неактивны, а на всякий случай
        # и на уровне API блокируем создание.
        if hasattr(user, "realtor_profile") and not hasattr(user, "client_profile"):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Риэлтор не может добавлять объекты в избранное.")

        client = getattr(user, "client_profile", None)
        if client is None:
            client, _ = Client.objects.get_or_create(user=user)
        serializer.save(client=client)


# ---------- HTML-страницы (вход/регистрация/профиль) ----------


def login_page(request):
    """
    Красивое окно входа, использующее тот же LoginSerializer, что и API.
    """
    errors = []
    form_data = {}

    if request.method == "POST":
        from .serializers import LoginSerializer  # локальный импорт, чтобы избежать циклов

        form_data = request.POST.dict()
        serializer = LoginSerializer(data=form_data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            login(request, user)
            return redirect("profile")
        else:
            # Собираем текст ошибок в удобном виде
            for field, msgs in serializer.errors.items():
                for msg in msgs:
                    if field == "non_field_errors":
                        errors.append(str(msg))
                    else:
                        errors.append(f"{field}: {msg}")

    return render(
        request,
        "auth/login.html",
        {
            "errors": errors,
            "form_data": form_data,
        },
    )


def register_page(request):
    """
    Окно регистрации, повторно использующее RegisterSerializer.
    """
    errors = []
    form_data = {}

    if request.method == "POST":
        from .serializers import RegisterSerializer  # локальный импорт, чтобы избежать циклов

        form_data = request.POST.dict()
        serializer = RegisterSerializer(data=form_data)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)
            return redirect("profile")
        else:
            for field, msgs in serializer.errors.items():
                for msg in msgs:
                    if field == "non_field_errors":
                        errors.append(str(msg))
                    else:
                        errors.append(f"{field}: {msg}")

    return render(
        request,
        "auth/register.html",
        {
            "errors": errors,
            "form_data": form_data,
        },
    )


@login_required
def profile_page(request):
    """
    Профиль пользователя / кабинет риэлтора.
    Для клиентов отображается личный кабинет с избранным и сделками,
    для риэлтора — отдельная админ-панель с объектами.
    """
    user = request.user

    # Ветвление: если это риэлтор — показываем другой шаблон.
    if hasattr(user, "realtor_profile"):
        # Здесь можно позже дополнить выборкой объектов через API/JS.
        return render(
            request,
            "realtor_dashboard.html",
            {
                "realtor": user.realtor_profile,
            },
        )

    # ----- Стандартный клиентский профиль -----

    # Обработка удаления избранного
    if request.method == "POST" and "remove_favorite" in request.POST:
        favorite_id = request.POST.get("favorite_id")
        if favorite_id:
            try:
                client = user.client_profile
                Favorite.objects.filter(id=favorite_id, client=client).delete()
            except Client.DoesNotExist:
                pass
        return redirect("profile")

    role_display = "Пользователь"
    phone = None

    if hasattr(user, "client_profile"):
        role_display = "Клиент"
        phone = user.client_profile.phone

    favorites = []
    deals = []
    notifications = []
    if hasattr(user, "client_profile"):
        favorites = (
            Favorite.objects.filter(client=user.client_profile)
            .select_related("property", "property__city", "property__district")
            .order_by("-created_at")
        )
        deals = (
            Deal.objects.filter(client=user.client_profile)
            .select_related("property", "property__city")
            .order_by("-created_at")
        )
    notifications = (
        Notification.objects.filter(user=user)
        .select_related("related_property", "related_property__city")
        .order_by("-created_at")
    )

    return render(
        request,
        "profile.html",
        {
            "role_display": role_display,
            "phone": phone,
            "favorites": favorites,
            "deals": deals,
            "notifications": notifications,
        },
    )


def logout_page(request):
    """
    Простой выход через HTML-интерфейс.
    """
    if request.method == "POST":
        logout(request)
        return redirect("login-page")

    # Для удобства можно выходить и по GET-запросу
    logout(request)
    return redirect("login-page")
