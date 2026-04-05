from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AnalyticsView,
    ApiCsrfCookieView,
    BulkPhotoUploadView,
    CityViewSet,
    CompanyGalleryImageViewSet,
    DistrictViewSet,
    FavoriteViewSet,
    LeadInquiryViewSet,
    LoginView,
    LogoutView,
    MeView,
    MyChatThreadsView,
    MyNotificationMetaView,
    MyPropertyViewSet,
    MyRealtorStatsDashboardView,
    PropertyChatView,
    PropertyImageViewSet,
    PropertyTypeViewSet,
    PropertyViewSet,
    RegisterView,
    SimilarPropertiesView,
)

router = DefaultRouter()
router.register(r"property-types", PropertyTypeViewSet, basename="property-type")
router.register(r"cities", CityViewSet, basename="city")
router.register(r"districts", DistrictViewSet, basename="district")
router.register(r"properties", PropertyViewSet, basename="property")
router.register(r"company-gallery", CompanyGalleryImageViewSet, basename="company-gallery")
router.register(r"property-images", PropertyImageViewSet, basename="property-image")
router.register(r"inquiries", LeadInquiryViewSet, basename="inquiry")
router.register(r"favorites", FavoriteViewSet, basename="favorite")
router.register(r"my/properties", MyPropertyViewSet, basename="my-property")

urlpatterns = [
    path("my/notifications/meta/", MyNotificationMetaView.as_view(), name="my-notifications-meta"),
    path("my/stats/dashboard/", MyRealtorStatsDashboardView.as_view(), name="realtor-stats-dashboard"),
    path("analytics/", AnalyticsView.as_view(), name="analytics"),
    path("auth/csrf/", ApiCsrfCookieView.as_view(), name="api-csrf-cookie"),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("similar/<int:pk>/", SimilarPropertiesView.as_view(), name="similar-properties"),
    path("properties/<int:pk>/chat/", PropertyChatView.as_view(), name="property-chat"),
    path("my/chat/threads/", MyChatThreadsView.as_view(), name="my-chat-threads"),
    path("upload-photo/", BulkPhotoUploadView.as_view(), name="upload-photo"),
    path("", include(router.urls)),
]
