from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AnalyticsView,
    CityViewSet,
    DistrictViewSet,
    FavoriteViewSet,
    LeadInquiryViewSet,
    LoginView,
    LogoutView,
    MeView,
    MyPropertyViewSet,
    PropertyImageViewSet,
    PropertyTypeViewSet,
    PropertyViewSet,
    RegisterView,
)

router = DefaultRouter()
router.register(r"property-types", PropertyTypeViewSet, basename="property-type")
router.register(r"cities", CityViewSet, basename="city")
router.register(r"districts", DistrictViewSet, basename="district")
router.register(r"properties", PropertyViewSet, basename="property")
router.register(r"property-images", PropertyImageViewSet, basename="property-image")
router.register(r"inquiries", LeadInquiryViewSet, basename="inquiry")
router.register(r"favorites", FavoriteViewSet, basename="favorite")
router.register(r"my/properties", MyPropertyViewSet, basename="my-property")

urlpatterns = [
    path("analytics/", AnalyticsView.as_view(), name="analytics"),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("", include(router.urls)),
]
