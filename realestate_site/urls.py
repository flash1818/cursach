"""
URL configuration for realestate_site project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

from listings.views import login_page, logout_page, profile_page, register_page


def home_redirect(request):
    return redirect("login-page")


urlpatterns = [
    path("", home_redirect, name="home"),
    path("auth/login/", login_page, name="login-page"),
    # Отдельный URL, который можно использовать как "вход для риэлтора".
    # Использует тот же шаблон входа, но вы можете на фронтенде/в меню
    # подписать его как кабинет риэлтора.
    path("realtor/login/", login_page, name="realtor-login"),
    path("auth/register/", register_page, name="register-page"),
    path("auth/logout/", logout_page, name="logout-page"),
    path("profile/", profile_page, name="profile"),
    # Скрытая админка: путь изменён, чтобы ею пользовались только вы как разработчик
    path("internal-admin-only/", admin.site.urls),
    path("api/", include("listings.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
