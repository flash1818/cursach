from decimal import Decimal

from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, IntegerField, Max, Q, Value
from django.db.models.functions import Abs
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from rest_framework import filters, permissions, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .chat_utils import (
    broadcast_listing_chat_message,
    process_listing_chat_message,
    user_can_access_property_chat,
)
from .models import (
    City,
    Client,
    CompanyGalleryImage,
    Deal,
    District,
    Favorite,
    LeadInquiry,
    ListingStats,
    Notification,
    Property,
    PropertyChatMessage,
    PropertyImage,
    PropertyType,
    Realtor,
)
from .serializers import (
    CitySerializer,
    CompanyGalleryImageSerializer,
    DistrictSerializer,
    FavoriteSerializer,
    LeadInquirySerializer,
    LoginSerializer,
    PropertyChatMessageSerializer,
    PropertyImageSerializer,
    PropertySerializer,
    PropertyTypeSerializer,
    RegisterSerializer,
    SimilarPropertySerializer,
    UserSerializer,
)


def record_property_view(prop: Property) -> None:
    now = timezone.now()
    stats, created = ListingStats.objects.get_or_create(
        property=prop,
        defaults={
            "view_count": 1,
            "inquiry_count": 0,
            "first_view_at": now,
            "last_view_at": now,
        },
    )
    if not created:
        ListingStats.objects.filter(pk=stats.pk).update(view_count=F("view_count") + 1, last_view_at=now)


def record_property_inquiry(prop: Property) -> None:
    ListingStats.objects.get_or_create(
        property=prop,
        defaults={"view_count": 0, "inquiry_count": 0},
    )
    ListingStats.objects.filter(property=prop).update(inquiry_count=F("inquiry_count") + 1)


def _annotate_similar_order(qs, base: Property, station_ids: list[int]):
    if station_ids:
        qs = qs.annotate(
            _mc=Count("metro_links", filter=Q(metro_links__station_id__in=station_ids), distinct=True)
        )
    else:
        qs = qs.annotate(_mc=Value(0, output_field=IntegerField()))
    return qs.annotate(_pd=Abs(F("price") - base.price)).order_by("-_mc", "_pd")


def _similar_extend(take: list, seen: set, qs, base: Property, station_ids: list[int], limit: int = 3):
    cand = _annotate_similar_order(qs, base, station_ids)
    for row in cand:
        if row.pk in seen:
            continue
        take.append(row)
        seen.add(row.pk)
        if len(take) >= limit:
            break
    return take, seen


class SimilarPropertiesView(APIView):
    """До 3 похожих: город, сделка, комнаты (с ослаблением), цена, этаж, метро."""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        base = get_object_or_404(
            Property.objects.select_related("city").prefetch_related("metro_links"),
            pk=pk,
        )
        station_ids = list(base.metro_links.values_list("station_id", flat=True))

        def pool(same_rooms: bool):
            qs = (
                Property.objects.filter(city_id=base.city_id, deal_type=base.deal_type)
                .exclude(pk=base.pk)
                .exclude(status__in=["sold", "archived"])
                .select_related("city")
                .prefetch_related("images", "metro_links")
            )
            if same_rooms and base.rooms is not None:
                qs = qs.filter(rooms=base.rooms)
            return qs

        take = []
        seen = set()

        for low_m, high_m in (
            (Decimal("0.88"), Decimal("1.12")),
            (Decimal("0.78"), Decimal("1.22")),
            (Decimal("0.68"), Decimal("1.32")),
            (Decimal("0.58"), Decimal("1.45")),
        ):
            qs = pool(True).filter(price__gte=base.price * low_m, price__lte=base.price * high_m)
            if base.floor is not None:
                qs = qs.filter(
                    Q(floor__isnull=True) | Q(floor__gte=base.floor - 3, floor__lte=base.floor + 3)
                )
            take, seen = _similar_extend(take, seen, qs, base, station_ids)
            if len(take) >= 3:
                break

        if len(take) < 3:
            take, seen = _similar_extend(take, seen, pool(True), base, station_ids)

        if len(take) < 3 and base.rooms is not None:
            for low_m, high_m in ((Decimal("0.72"), Decimal("1.28")), (Decimal("0.55"), Decimal("1.5"))):
                qs = pool(False).filter(price__gte=base.price * low_m, price__lte=base.price * high_m)
                take, seen = _similar_extend(take, seen, qs, base, station_ids)
                if len(take) >= 3:
                    break

        if len(take) < 3:
            take, seen = _similar_extend(take, seen, pool(False), base, station_ids)

        ser = SimilarPropertySerializer(take[:3], many=True, context={"request": request})
        return Response(ser.data)


class PropertyChatView(APIView):
    """История и отправка сообщений по объекту (дублирует логику WebSocket для кабинетов)."""

    permission_classes = [IsAuthenticated]
    authentication_classes = (SessionAuthentication,)

    def get(self, request, pk):
        prop = get_object_or_404(
            Property.objects.select_related("city", "realtor"),
            pk=pk,
        )
        if not user_can_access_property_chat(request.user, prop):
            return Response(
                {"detail": "Нет доступа к чату по этому объекту."},
                status=status.HTTP_403_FORBIDDEN,
            )
        msgs = (
            PropertyChatMessage.objects.filter(property=prop)
            .select_related("sender")
            .order_by("created_at")
        )
        return Response(PropertyChatMessageSerializer(msgs, many=True).data)

    def post(self, request, pk):
        prop = get_object_or_404(Property, pk=pk)
        if not user_can_access_property_chat(request.user, prop):
            return Response({"detail": "Нет доступа."}, status=status.HTTP_403_FORBIDDEN)
        body = (request.data.get("message") if isinstance(request.data, dict) else None) or ""
        try:
            msg = process_listing_chat_message(pk, request.user, body)
        except Property.DoesNotExist:
            return Response({"detail": "Объект не найден."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        payload = {
            "message": msg.body,
            "username": request.user.get_username(),
            "id": msg.id,
            "created_at": msg.created_at.isoformat(),
        }
        broadcast_listing_chat_message(pk, payload)
        return Response(PropertyChatMessageSerializer(msg).data, status=status.HTTP_201_CREATED)


class MyChatThreadsView(APIView):
    """Список диалогов для клиента (избранное + переписка) или риэлтора (объекты с сообщениями)."""

    permission_classes = [IsAuthenticated]
    authentication_classes = (SessionAuthentication,)

    def get(self, request):
        user = request.user
        prop_by_id = {}

        if hasattr(user, "realtor_profile"):
            r = user.realtor_profile
            for p in (
                Property.objects.filter(realtor=r, chat_messages__isnull=False)
                .distinct()
                .select_related("city")
            ):
                prop_by_id[p.id] = p
        elif hasattr(user, "client_profile"):
            cp = user.client_profile
            ids = set(PropertyChatMessage.objects.filter(sender=user).values_list("property_id", flat=True))
            ids.update(Favorite.objects.filter(client=cp).values_list("property_id", flat=True))
            for p in Property.objects.filter(pk__in=ids).select_related("city"):
                prop_by_id[p.id] = p
        else:
            return Response({"threads": []})

        threads = []
        for p in prop_by_id.values():
            last = (
                PropertyChatMessage.objects.filter(property=p)
                .select_related("sender")
                .order_by("-created_at")
                .first()
            )
            threads.append(
                {
                    "property_id": p.id,
                    "title": p.title,
                    "city_name": p.city.name if p.city_id else "",
                    "last_message": (last.body[:240] if last else ""),
                    "last_at": last.created_at.isoformat() if last else None,
                    "last_sender": last.sender.get_username() if last else "",
                    "has_messages": last is not None,
                }
            )

        threads.sort(
            key=lambda t: t["last_at"] or "1970-01-01T00:00:00+00:00",
            reverse=True,
        )
        return Response({"threads": threads})


class MyRealtorStatsDashboardView(APIView):
    """Просмотры, заявки «К сделке», конверсия и среднее время до закрытия сделки."""

    permission_classes = [IsAuthenticated]
    authentication_classes = (SessionAuthentication,)

    def get(self, request):
        try:
            realtor = request.user.realtor_profile
        except Realtor.DoesNotExist:
            return Response({"detail": "Доступно только риэлторам."}, status=status.HTTP_403_FORBIDDEN)

        props = (
            Property.objects.filter(realtor=realtor)
            .select_related("city")
            .prefetch_related("listing_stats")
            .order_by("-created_at")
        )

        listings_payload = []
        total_views = 0
        total_inquiries = 0

        for p in props:
            try:
                st = p.listing_stats
            except ListingStats.DoesNotExist:
                st = None
            views = st.view_count if st else 0
            inq = st.inquiry_count if st else 0
            total_views += views
            total_inquiries += inq
            conv = round((inq / views) * 100, 1) if views else 0.0

            closed = Deal.objects.filter(property=p, status="closed").exclude(closed_at__isnull=True)
            avg_days = None
            if closed.exists():
                agg = closed.annotate(
                    dur=ExpressionWrapper(F("closed_at") - F("created_at"), output_field=DurationField())
                ).aggregate(avg=Avg("dur"))
                if agg["avg"] is not None:
                    avg_days = round(agg["avg"].total_seconds() / 86400, 1)

            listings_payload.append(
                {
                    "property_id": p.id,
                    "title": p.title,
                    "views": views,
                    "inquiries": inq,
                    "conversion_pct": conv,
                    "avg_days_to_close": avg_days,
                }
            )

        all_closed = Deal.objects.filter(realtor=realtor, status="closed").exclude(closed_at__isnull=True)
        global_avg_days = None
        if all_closed.exists():
            gagg = all_closed.annotate(
                dur=ExpressionWrapper(F("closed_at") - F("created_at"), output_field=DurationField())
            ).aggregate(avg=Avg("dur"))
            if gagg["avg"] is not None:
                global_avg_days = round(gagg["avg"].total_seconds() / 86400, 1)

        summary = {
            "total_views": total_views,
            "total_inquiries": total_inquiries,
            "overall_conversion_pct": round((total_inquiries / total_views) * 100, 1) if total_views else 0.0,
            "avg_days_to_close_all": global_avg_days,
        }

        return Response({"listings": listings_payload, "summary": summary})


class BulkPhotoUploadView(APIView):
    """Массовая загрузка фото (multipart, поле images)."""

    permission_classes = [IsAuthenticated]
    authentication_classes = (SessionAuthentication,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        prop_id = request.data.get("property")
        if not prop_id:
            return Response({"detail": "Укажите property."}, status=status.HTTP_400_BAD_REQUEST)
        prop = get_object_or_404(Property, pk=prop_id)
        user = request.user
        if not hasattr(user, "realtor_profile") or prop.realtor_id != user.realtor_profile.id:
            return Response({"detail": "Нет доступа к этому объекту."}, status=status.HTTP_403_FORBIDDEN)

        files = request.FILES.getlist("images")
        if not files:
            return Response({"detail": "Добавьте файлы в поле images."}, status=status.HTTP_400_BAD_REQUEST)

        caption = f"Загружено {user.get_username()}"
        ids = []
        for f in files[:20]:
            img = PropertyImage.objects.create(property=prop, image=f, caption=caption)
            ids.append(img.id)

        return Response({"detail": "ok", "ids": ids}, status=status.HTTP_201_CREATED)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class ApiCsrfCookieView(APIView):
    """Выставляет cookie csrftoken для POST из SPA."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"detail": "ok"})


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


def _finalize_deal_interest(user, prop) -> str | None:
    """
    Создаёт уведомления клиенту и риэлтору по запросу «К сделке».
    Требуется: у user есть client_profile, у объекта назначен риэлтор.
    Возвращает текст ошибки или None.
    """
    if not prop.realtor_id:
        return "У этого объекта пока не назначен ответственный риэлтор."
    if prop.status in ("sold", "archived"):
        return "Этот объект снят с показа — запрос к сделке недоступен."

    realtor = prop.realtor
    ru = realtor.user
    display_name = (ru.get_full_name() or "").strip() or ru.username
    deal_label = "Продажа" if prop.deal_type == "sale" else "Аренда"

    body_lines = [
        "Вы запросили сопровождение сделки по объекту из каталога.",
        "",
        "Ответственный риэлтор",
        f"Имя: {display_name}",
        f"Телефон: {realtor.phone or 'уточняйте в агентстве'}",
        f"E-mail: {ru.email or 'не указан'}",
    ]
    if realtor.position:
        body_lines.append(f"Должность: {realtor.position}")
    if realtor.bio:
        short_bio = realtor.bio.strip()
        if len(short_bio) > 280:
            short_bio = short_bio[:277] + "…"
        body_lines.extend(["", "О специалисте", short_bio])

    body_lines.extend(
        [
            "",
            "Объект",
            f"«{prop.title}»",
            f"Адрес: {prop.address}",
            f"Город: {prop.city.name}",
            f"Цена: {prop.price} ₽ · {deal_label}",
            f"Статус в каталоге: {prop.get_status_display()}",
            "",
            "Дальнейшие шаги: свяжитесь с риэлтором, согласуйте просмотр и перечень документов. "
            "Сообщите адрес объекта или номер объявления — так быстрее откроют карточку сделки.",
        ]
    )

    Notification.objects.create(
        user=user,
        kind=Notification.Kind.GENERIC,
        title=f"Контакты по сделке: {prop.title}",
        body="\n".join(body_lines),
        related_property=prop,
    )

    client = user.client_profile
    cu = user
    client_display = (cu.get_full_name() or "").strip() or cu.username
    realtor_lines = [
        "Клиент нажал «К сделке» по вашему объекту и хочет сопровождение.",
        "",
        "Контактные данные клиента",
        f"Имя: {client_display}",
        f"Логин: {cu.username}",
        f"Телефон: {client.phone or 'не указан в профиле'}",
        f"E-mail: {cu.email or 'не указан'}",
        "",
        "Объект",
        f"«{prop.title}»",
        f"Адрес: {prop.address}",
        f"Город: {prop.city.name}",
        f"Цена: {prop.price} ₽ · {deal_label}",
        "",
        "Откройте уведомление в профиле и нажмите «Начать сделку», чтобы клиент увидел сделку в своём кабинете.",
    ]
    Notification.objects.create(
        user=realtor.user,
        kind=Notification.Kind.DEAL_INQUIRY,
        title=f"Запрос на сделку: {prop.title}",
        body="\n".join(realtor_lines),
        related_property=prop,
        related_client=client,
    )
    record_property_inquiry(prop)
    return None


class PropertyViewSet(viewsets.ModelViewSet):
    queryset = (
        Property.objects.select_related("property_type", "city", "district", "realtor__user")
        .prefetch_related("images")
    )
    serializer_class = PropertySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ("title", "address", "description", "city__name", "district__name", "property_type__name")
    ordering_fields = ("price", "area", "created_at", "updated_at")

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        if self.action == "deal_interest":
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        record_property_view(instance)
        return super().retrieve(request, *args, **kwargs)

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

        if self.action == "list":
            queryset = queryset.exclude(status__in=["sold", "archived"])

        return queryset

    @action(
        detail=True,
        methods=["post"],
        url_path="deal-interest",
        permission_classes=[IsAuthenticated],
        authentication_classes=[SessionAuthentication],
    )
    def deal_interest(self, request, pk=None):
        """
        Клиент запрашивает переход к сделке: создаётся уведомление с контактами риэлтора.
        """
        prop = self.get_object()
        user = request.user

        if hasattr(user, "realtor_profile") and not hasattr(user, "client_profile"):
            raise PermissionDenied(
                "Запрос контактов доступен аккаунтам клиентов. Войдите как клиент или зарегистрируйтесь."
            )

        if not hasattr(user, "client_profile"):
            Client.objects.get_or_create(user=user)

        err = _finalize_deal_interest(user, prop)
        if err:
            return Response({"detail": err}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"detail": "Контакты и детали отправлены в раздел «Уведомления» вашего профиля."},
            status=status.HTTP_201_CREATED,
        )


class MyPropertyViewSet(viewsets.ModelViewSet):
    """
    CRUD по объектам конкретного риелтора.
    """

    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = (SessionAuthentication,)

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

        hidden = self.request.query_params.get("hidden")
        if str(hidden).lower() in ("1", "true", "yes"):
            return queryset.filter(status__in=["sold", "archived"]).order_by("-updated_at")
        return queryset.exclude(status__in=["sold", "archived"]).order_by("-created_at")

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
    authentication_classes = (SessionAuthentication,)
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
        user = self.request.user
        cap = (serializer.validated_data.get("caption") or "").strip()
        if not cap:
            serializer.save(caption=f"Загружено {user.get_username()}")
        else:
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
    authentication_classes = (SessionAuthentication,)

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


def _handle_realtor_start_deal(request, user):
    """Создание Deal по уведомлению DEAL_INQUIRY и уведомление клиента."""
    realtor = user.realtor_profile
    raw_id = request.POST.get("notification_id")
    try:
        nid = int(raw_id)
    except (TypeError, ValueError):
        messages.error(request, "Некорректный запрос.")
        return redirect("profile")

    note = (
        Notification.objects.filter(
            id=nid,
            user=user,
            kind=Notification.Kind.DEAL_INQUIRY,
        )
        .select_related("related_property", "related_client", "related_client__user")
        .first()
    )
    if not note or not note.related_client_id or not note.related_property_id:
        messages.error(request, "Уведомление не найдено или устарело.")
        return redirect("profile")

    prop = note.related_property
    client = note.related_client
    if prop.realtor_id != realtor.id:
        messages.error(request, "Этот объект не относится к вашим объявлениям.")
        return redirect("profile")

    if Deal.objects.filter(client=client, property=prop).exists():
        messages.warning(request, "Сделка с этим клиентом по данному объекту уже оформлена.")
        return redirect("profile")

    Deal.objects.create(
        property=prop,
        client=client,
        realtor=realtor,
        deal_type=prop.deal_type,
        price=prop.price,
        status="draft",
    )
    note.is_read = True
    note.save(update_fields=["is_read"])

    cu = client.user
    realtor_name = (user.get_full_name() or "").strip() or user.username
    Notification.objects.create(
        user=cu,
        kind=Notification.Kind.GENERIC,
        title=f"Сделка начата: {prop.title}",
        body=(
            f"Риэлтор {realtor_name} оформил сделку по объекту «{prop.title}».\n\n"
            f"Сумма в карточке: {prop.price} ₽\n"
            f"Тип: {prop.get_deal_type_display()}\n"
            f"Статус сделки: в процессе — ожидайте контакт для согласования документов и просмотра."
        ),
        related_property=prop,
    )
    messages.success(request, "Сделка создана. Клиент получил уведомление и видит сделку в профиле.")
    return redirect("profile")


def _handle_realtor_complete_deal(request, user):
    realtor = user.realtor_profile
    try:
        did = int(request.POST.get("deal_id"))
    except (TypeError, ValueError):
        messages.error(request, "Некорректный запрос.")
        return redirect("profile")

    deal = (
        Deal.objects.filter(id=did, realtor=realtor)
        .select_related("property", "client", "client__user")
        .first()
    )
    if not deal:
        messages.error(request, "Сделка не найдена.")
        return redirect("profile")
    if deal.status not in ("draft", "signed"):
        messages.warning(request, "Эту сделку уже нельзя завершить.")
        return redirect("profile")

    prop = deal.property
    deal.status = "closed"
    deal.closed_at = timezone.now()
    deal.save(update_fields=["status", "closed_at"])

    if prop.deal_type == "sale":
        prop.status = "sold"
    else:
        prop.status = "archived"
    prop.save(update_fields=["status"])

    rn = (user.get_full_name() or "").strip() or user.username
    Notification.objects.create(
        user=deal.client.user,
        kind=Notification.Kind.GENERIC,
        title=f"Сделка завершена: {prop.title}",
        body=(
            f"Риэлтор {rn} отметил сделку по объекту «{prop.title}» как завершённую.\n\n"
            f"Объявление снято с витрины. Сумма в карточке сделки: {deal.price} ₽.\n"
            f"При вопросах свяжитесь с агентством."
        ),
        related_property=prop,
    )
    messages.success(request, "Сделка завершена. Объект скрыт в активном списке; клиент получил уведомление.")
    return redirect("profile")


def _handle_realtor_cancel_deal(request, user):
    realtor = user.realtor_profile
    try:
        did = int(request.POST.get("deal_id"))
    except (TypeError, ValueError):
        messages.error(request, "Некорректный запрос.")
        return redirect("profile")

    deal = (
        Deal.objects.filter(id=did, realtor=realtor)
        .select_related("property", "client", "client__user")
        .first()
    )
    if not deal:
        messages.error(request, "Сделка не найдена.")
        return redirect("profile")
    if deal.status not in ("draft", "signed"):
        messages.warning(request, "Эту сделку уже нельзя отменить.")
        return redirect("profile")

    prop = deal.property
    deal.status = "cancelled"
    deal.closed_at = timezone.now()
    deal.save(update_fields=["status", "closed_at"])

    rn = (user.get_full_name() or "").strip() or user.username
    Notification.objects.create(
        user=deal.client.user,
        kind=Notification.Kind.GENERIC,
        title=f"Сделка отменена: {prop.title}",
        body=(
            f"Риэлтор {rn} отменил сделку по объекту «{prop.title}».\n\n"
            f"Объект остаётся в каталоге. Уточните детали у агентства, если нужна помощь с другим вариантом."
        ),
        related_property=prop,
    )
    messages.success(request, "Сделка отменена. Клиент получил уведомление.")
    return redirect("profile")


def _handle_delete_notification(request, user):
    try:
        nid = int(request.POST.get("notification_id"))
    except (TypeError, ValueError):
        messages.error(request, "Некорректный запрос.")
        return redirect("profile")
    deleted, _ = Notification.objects.filter(id=nid, user=user).delete()
    if deleted:
        messages.success(request, "Уведомление удалено.")
    else:
        messages.warning(request, "Уведомление не найдено.")
    return redirect("profile")


def _handle_clear_notifications(request, user):
    n, _ = Notification.objects.filter(user=user).delete()
    messages.success(
        request,
        f"Удалено уведомлений: {n}." if n else "Список уведомлений уже был пуст.",
    )
    return redirect("profile")


def _handle_remove_favorite(request, user):
    if not hasattr(user, "client_profile"):
        return redirect("profile")
    favorite_id = request.POST.get("favorite_id")
    if favorite_id:
        Favorite.objects.filter(id=favorite_id, client=user.client_profile).delete()
    return redirect("profile")


def _handle_favorite_deal_interest(request, user):
    if hasattr(user, "realtor_profile") and not hasattr(user, "client_profile"):
        messages.error(request, "Запрос «К сделке» из избранного доступен клиентам.")
        return redirect("profile")
    if not hasattr(user, "client_profile"):
        Client.objects.get_or_create(user=user)
    favorite_id = request.POST.get("favorite_id")
    fav = (
        Favorite.objects.filter(id=favorite_id, client=user.client_profile)
        .select_related("property", "property__city")
        .first()
    )
    if not fav:
        messages.error(request, "Запись в избранном не найдена.")
        return redirect("profile")
    err = _finalize_deal_interest(user, fav.property)
    if err:
        messages.error(request, err)
    else:
        messages.success(
            request,
            "Запрос отправлен. Контакты риэлтора и ответ — в разделе «Уведомления».",
        )
    return redirect("profile")


class MyNotificationMetaView(APIView):
    """Для опроса новых уведомлений с страницы профиля (без перезагрузки)."""

    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = (SessionAuthentication,)

    def get(self, request):
        qs = Notification.objects.filter(user=request.user)
        agg = qs.aggregate(m=Max("id"), c=Count("id"))
        mid = agg["m"] or 0
        title = ""
        if mid:
            title = qs.filter(id=mid).values_list("title", flat=True).first() or ""
        return Response({"max_id": mid, "count": agg["c"] or 0, "title": title})


@login_required
def profile_page(request):
    """
    Профиль пользователя / кабинет риэлтора.
    Для клиентов отображается личный кабинет с избранным и сделками,
    для риэлтора — отдельная админ-панель с объектами.
    """
    user = request.user

    if request.method == "POST":
        if "start_deal" in request.POST and hasattr(user, "realtor_profile"):
            return _handle_realtor_start_deal(request, user)
        if "complete_deal" in request.POST and hasattr(user, "realtor_profile"):
            return _handle_realtor_complete_deal(request, user)
        if "cancel_deal" in request.POST and hasattr(user, "realtor_profile"):
            return _handle_realtor_cancel_deal(request, user)
        if "delete_notification" in request.POST:
            return _handle_delete_notification(request, user)
        if "clear_notifications" in request.POST:
            return _handle_clear_notifications(request, user)
        if "favorite_deal_interest" in request.POST:
            return _handle_favorite_deal_interest(request, user)
        if "remove_favorite" in request.POST:
            return _handle_remove_favorite(request, user)

    # Ветвление: если это риэлтор — показываем другой шаблон.
    if hasattr(user, "realtor_profile"):
        realtor = user.realtor_profile
        notifications = (
            Notification.objects.filter(user=user)
            .select_related(
                "related_property",
                "related_property__city",
                "related_client",
                "related_client__user",
            )
            .order_by("-created_at")
        )
        existing_pairs = set(
            Deal.objects.filter(realtor=realtor).values_list("client_id", "property_id")
        )
        for n in notifications:
            n.show_start_deal = (
                n.kind == Notification.Kind.DEAL_INQUIRY
                and n.related_client_id
                and n.related_property_id
                and (n.related_client_id, n.related_property_id) not in existing_pairs
            )

        deals_active = (
            Deal.objects.filter(realtor=realtor, status__in=["draft", "signed"])
            .select_related("property", "property__city", "client", "client__user")
            .order_by("-created_at")
        )
        deals_done = (
            Deal.objects.filter(realtor=realtor, status__in=["closed", "cancelled"])
            .select_related("property", "property__city", "client", "client__user")
            .order_by("-closed_at", "-created_at")
        )

        latest_notification_id = (
            Notification.objects.filter(user=user).order_by("-id").values_list("id", flat=True).first()
            or 0
        )
        return render(
            request,
            "realtor_dashboard.html",
            {
                "realtor": realtor,
                "notifications": notifications,
                "deals_active": deals_active,
                "deals_done": deals_done,
                "latest_notification_id": latest_notification_id,
            },
        )

    # ----- Стандартный клиентский профиль -----

    role_display = "Пользователь"
    phone = None

    if hasattr(user, "client_profile"):
        role_display = "Клиент"
        phone = user.client_profile.phone

    favorites = []
    deals_active = []
    deals_done = []
    notifications = []
    if hasattr(user, "client_profile"):
        favorites = (
            Favorite.objects.filter(client=user.client_profile)
            .select_related("property", "property__city", "property__district")
            .order_by("-created_at")
        )
        deals_active = (
            Deal.objects.filter(client=user.client_profile, status__in=["draft", "signed"])
            .select_related("property", "property__city", "realtor", "realtor__user")
            .order_by("-created_at")
        )
        deals_done = (
            Deal.objects.filter(client=user.client_profile, status__in=["closed", "cancelled"])
            .select_related("property", "property__city", "realtor", "realtor__user")
            .order_by("-closed_at", "-created_at")
        )
    notifications = (
        Notification.objects.filter(user=user)
        .select_related("related_property", "related_property__city")
        .order_by("-created_at")
    )
    latest_notification_id = (
        Notification.objects.filter(user=user).order_by("-id").values_list("id", flat=True).first() or 0
    )

    return render(
        request,
        "profile.html",
        {
            "role_display": role_display,
            "phone": phone,
            "favorites": favorites,
            "deals_active": deals_active,
            "deals_done": deals_done,
            "notifications": notifications,
            "latest_notification_id": latest_notification_id,
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
