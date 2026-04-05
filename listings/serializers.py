from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from .models import (
    City,
    Client,
    CompanyGalleryImage,
    District,
    Favorite,
    LeadInquiry,
    Property,
    PropertyChatMessage,
    PropertyImage,
    PropertyMetro,
    PropertyType,
    Realtor,
)


User = get_user_model()


class PropertyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyType
        fields = ("id", "name")


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ("id", "name")


class DistrictSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)

    class Meta:
        model = District
        fields = ("id", "name", "city", "city_name")


class PropertyImageSerializer(serializers.ModelSerializer):
    """Фото объекта: загрузка файла `image`; в ответе `image_url` — полный URL."""

    image = serializers.ImageField(write_only=True, required=False)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PropertyImage
        fields = ("id", "property", "image", "image_url", "caption", "created_at")
        read_only_fields = ("created_at",)

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get("request")
            url = obj.image.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return obj.image_url or ""

    def validate(self, attrs):
        if self.instance is None and not attrs.get("image"):
            raise serializers.ValidationError(
                {"image": "Загрузите файл изображения JPG, PNG или WebP."}
            )
        return attrs


class CompanyGalleryImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = CompanyGalleryImage
        fields = ("id", "image_url", "caption", "sort_order", "created_at")

    def get_image_url(self, obj):
        if not obj.image:
            return ""
        request = self.context.get("request")
        url = obj.image.url
        if request:
            return request.build_absolute_uri(url)
        return url


class PropertyMetroSerializer(serializers.ModelSerializer):
    station_name = serializers.CharField(source="station.name", read_only=True)
    station_city = serializers.CharField(source="station.city.name", read_only=True)

    class Meta:
        model = PropertyMetro
        fields = (
            "id",
            "station_name",
            "station_city",
            "distance_meters",
            "walking_time_minutes",
        )


class PropertyChatMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.username", read_only=True)

    class Meta:
        model = PropertyChatMessage
        fields = ("id", "body", "sender_username", "created_at")


class SimilarPropertySerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = ("id", "title", "price", "city_name", "rooms", "floor", "deal_type", "image_url")

    def get_image_url(self, obj):
        img = obj.images.first()
        if img and img.image:
            request = self.context.get("request")
            url = img.image.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return ""


class PropertySerializer(serializers.ModelSerializer):
    property_type_name = serializers.CharField(source="property_type.name", read_only=True)
    city_name = serializers.CharField(source="city.name", read_only=True)
    district_name = serializers.CharField(source="district.name", read_only=True, allow_null=True)
    realtor_id = serializers.IntegerField(source="realtor.id", read_only=True)
    images = PropertyImageSerializer(many=True, read_only=True)
    metro_links = PropertyMetroSerializer(many=True, read_only=True)

    class Meta:
        model = Property
        fields = (
            "id",
            "title",
            "property_type",
            "property_type_name",
            "city",
            "city_name",
            "district",
            "district_name",
            "deal_type",
            "status",
            "price",
            "area",
            "rooms",
            "floor",
            "total_floors",
            "address",
            "description",
            "latitude",
            "longitude",
            "is_featured",
            "realtor_id",
            "created_at",
            "updated_at",
            "images",
            "metro_links",
        )
        read_only_fields = ("created_at", "updated_at")


class LeadInquirySerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)
    property_type_name = serializers.CharField(source="property_type.name", read_only=True)

    class Meta:
        model = LeadInquiry
        fields = (
            "id",
            "full_name",
            "phone",
            "email",
            "city",
            "city_name",
            "property_type",
            "property_type_name",
            "deal_type",
            "preferred_rooms",
            "budget_min",
            "budget_max",
            "message",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    client_id = serializers.SerializerMethodField()
    realtor_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "client_id",
            "realtor_id",
        )

    def get_role(self, obj):
        if hasattr(obj, "realtor_profile"):
            return "realtor"
        if hasattr(obj, "client_profile"):
            return "client"
        return "user"

    def get_client_id(self, obj):
        if hasattr(obj, "client_profile"):
            return obj.client_profile.id
        return None

    def get_realtor_id(self, obj):
        if hasattr(obj, "realtor_profile"):
            return obj.realtor_profile.id
        return None


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    # Регистрация на сайте только для клиентов.
    role = serializers.ChoiceField(choices=[("client", "client")], default="client")
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)

    def validate_phone(self, value):
        from .phone_utils import normalize_ru_phone

        if not value or not str(value).strip():
            return ""
        try:
            return normalize_ru_phone(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Пользователь с таким логином уже существует.")
        return value

    def create(self, validated_data):
        # Принудительно фиксируем роль как client, даже если кто-то попытается
        # передать другое значение через API.
        validated_data["role"] = "client"
        role = validated_data.pop("role")
        phone = validated_data.pop("phone", "")
        password = validated_data.pop("password")

        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        Client.objects.create(user=user, phone=phone)

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Неверный логин или пароль.")
        attrs["user"] = user
        return attrs


class FavoriteSerializer(serializers.ModelSerializer):
    property_detail = PropertySerializer(source="property", read_only=True)

    class Meta:
        model = Favorite
        fields = ("id", "property", "property_detail", "created_at")
        read_only_fields = ("created_at",)
