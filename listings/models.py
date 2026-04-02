from django.conf import settings
from django.db import models


class PropertyType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Тип объекта"
        verbose_name_plural = "Типы объектов"

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "Города"

    def __str__(self):
        return self.name


class District(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="districts")
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Район"
        verbose_name_plural = "Районы"
        unique_together = ("city", "name")

    def __str__(self):
        return f"{self.city.name}, {self.name}"


class Property(models.Model):
    DEAL_CHOICES = [
        ("sale", "Продажа"),
        ("rent", "Аренда"),
    ]

    STATUS_CHOICES = [
        ("new", "Новый"),
        ("active", "Активный"),
        ("reserved", "Забронирован"),
        ("sold", "Продан"),
        ("archived", "Архив"),
    ]

    title = models.CharField(max_length=200)
    property_type = models.ForeignKey(
        PropertyType,
        on_delete=models.PROTECT,
        related_name="properties",
    )
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name="properties")
    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name="properties",
        null=True,
        blank=True,
    )
    deal_type = models.CharField(max_length=10, choices=DEAL_CHOICES, default="sale")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    price = models.DecimalField(max_digits=14, decimal_places=2)
    area = models.DecimalField(max_digits=10, decimal_places=2)
    rooms = models.PositiveSmallIntegerField(null=True, blank=True)
    floor = models.PositiveSmallIntegerField(null=True, blank=True)
    total_floors = models.PositiveSmallIntegerField(null=True, blank=True)
    address = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    realtor = models.ForeignKey(
        "Realtor",
        on_delete=models.SET_NULL,
        related_name="properties",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Объект недвижимости"
        verbose_name_plural = "Объекты недвижимости"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["city", "district"]),
            models.Index(fields=["deal_type", "status"]),
            models.Index(fields=["price"]),
        ]

    def __str__(self):
        return self.title


class PropertyImage(models.Model):
    """Фото объекта: загрузка файла; старые записи могли содержать только image_url."""

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="properties/", blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    caption = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Фото объекта"
        verbose_name_plural = "Фото объектов"
        ordering = ["id"]

    def __str__(self):
        return f"Фото для {self.property.title}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            from .image_utils import resize_image_field

            resize_image_field(self.image, max_width=1400, max_height=1050)
            super().save(update_fields=["image"])


class CompanyGalleryImage(models.Model):
    """Фотографии для блока «О компании» на главной странице."""

    image = models.ImageField(upload_to="gallery/")
    caption = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Фото галереи компании"
        verbose_name_plural = "Галерея компании"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.caption or f"Фото #{self.pk}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            from .image_utils import resize_image_field

            resize_image_field(self.image, max_width=1200, max_height=800)
            super().save(update_fields=["image"])


class PropertyDocument(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=200)
    file_url = models.URLField(max_length=500)
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Документ по объекту"
        verbose_name_plural = "Документы по объектам"

    def __str__(self):
        return self.title


class LeadInquiry(models.Model):
    DEAL_CHOICES = Property.DEAL_CHOICES
    STATUS_CHOICES = [
        ("new", "Новая"),
        ("in_progress", "В работе"),
        ("closed", "Закрыта"),
    ]

    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=32)
    email = models.EmailField(blank=True)
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        related_name="inquiries",
        null=True,
        blank=True,
    )
    property_type = models.ForeignKey(
        PropertyType,
        on_delete=models.SET_NULL,
        related_name="inquiries",
        null=True,
        blank=True,
    )
    deal_type = models.CharField(max_length=10, choices=DEAL_CHOICES, default="sale")
    preferred_rooms = models.PositiveSmallIntegerField(null=True, blank=True)
    budget_min = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    budget_max = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Заявка клиента"
        verbose_name_plural = "Заявки клиентов"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} - {self.get_status_display()}"


class Client(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_profile",
    )
    phone = models.CharField(max_length=32, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

    def __str__(self):
        return self.user.get_username()


class Realtor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="realtor_profile",
    )
    phone = models.CharField(max_length=32, blank=True)
    position = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Риэлтор"
        verbose_name_plural = "Риэлторы"

    def __str__(self):
        return self.user.get_username()


class Favorite(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="favorites")
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Избранный объект"
        verbose_name_plural = "Избранные объекты"
        unique_together = ("client", "property")

    def __str__(self):
        return f"{self.client} → {self.property}"


class Appointment(models.Model):
    STATUS_CHOICES = [
        ("new", "Новая"),
        ("confirmed", "Подтверждена"),
        ("completed", "Проведена"),
        ("cancelled", "Отменена"),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="appointments")
    realtor = models.ForeignKey(
        Realtor,
        on_delete=models.SET_NULL,
        related_name="appointments",
        null=True,
        blank=True,
    )
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="appointments")
    scheduled_at = models.DateTimeField()
    comment = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Запись на просмотр"
        verbose_name_plural = "Записи на просмотр"
        ordering = ["-scheduled_at"]

    def __str__(self):
        return f"{self.client} → {self.property} @ {self.scheduled_at}"


class Deal(models.Model):
    DEAL_TYPE_CHOICES = Property.DEAL_CHOICES
    STATUS_CHOICES = [
        ("draft", "Черновик"),
        ("signed", "Подписана"),
        ("closed", "Закрыта"),
        ("cancelled", "Отменена"),
    ]

    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name="deals")
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="deals")
    realtor = models.ForeignKey(Realtor, on_delete=models.SET_NULL, related_name="deals", null=True)
    deal_type = models.CharField(max_length=10, choices=DEAL_TYPE_CHOICES)
    price = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    signed_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Сделка"
        verbose_name_plural = "Сделки"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.property} – {self.price}"


class MetroStation(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="metro_stations")
    name = models.CharField(max_length=150)
    line = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name = "Станция метро"
        verbose_name_plural = "Станции метро"
        unique_together = ("city", "name")

    def __str__(self):
        return f"{self.name} ({self.city.name})"


class PropertyMetro(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="metro_links")
    station = models.ForeignKey(MetroStation, on_delete=models.CASCADE, related_name="properties")
    distance_meters = models.PositiveIntegerField()
    walking_time_minutes = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Расстояние до метро"
        verbose_name_plural = "Расстояния до метро"
        unique_together = ("property", "station")

    def __str__(self):
        return f"{self.property} → {self.station}"


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    related_property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class MarketAnalyticsSnapshot(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True)
    payload = models.JSONField()

    class Meta:
        verbose_name = "Снимок аналитики"
        verbose_name_plural = "Снимки аналитики"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Снимок от {self.created_at:%Y-%m-%d %H:%M}"
