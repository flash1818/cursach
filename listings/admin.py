from django.contrib import admin

from .models import City, District, LeadInquiry, Property, PropertyImage, PropertyType


@admin.register(PropertyType)
class PropertyTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "city")
    list_filter = ("city",)
    search_fields = ("name", "city__name")


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "property_type",
        "city",
        "district",
        "deal_type",
        "status",
        "price",
        "is_featured",
        "created_at",
    )
    list_filter = ("deal_type", "status", "is_featured", "city", "property_type")
    search_fields = ("title", "address", "city__name", "district__name")
    list_select_related = ("property_type", "city", "district")
    inlines = [PropertyImageInline]


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ("id", "property", "image_url", "caption", "created_at")
    search_fields = ("property__title", "caption", "image_url")
    list_select_related = ("property",)


@admin.register(LeadInquiry)
class LeadInquiryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "phone",
        "email",
        "city",
        "property_type",
        "deal_type",
        "status",
        "created_at",
    )
    list_filter = ("status", "deal_type", "city", "property_type")
    search_fields = ("full_name", "phone", "email", "message")
    list_select_related = ("city", "property_type")
