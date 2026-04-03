import os
from io import BytesIO

import django
from django.core.files.base import ContentFile
from PIL import Image


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "realestate_site.settings")
django.setup()

from django.contrib.auth import get_user_model
from listings.demo_assets import DEMO_IMAGES, ensure_demo_image_dirs
from listings.models import (
    City,
    CompanyGalleryImage,
    Deal,
    District,
    LeadInquiry,
    Notification,
    Property,
    PropertyImage,
    PropertyType,
    Realtor,
)


def jpeg_placeholder(color_rgb, w=1600, h=1200):
    buf = BytesIO()
    Image.new("RGB", (w, h), color=color_rgb).save(buf, format="JPEG", quality=92)
    return buf.getvalue()


User = get_user_model()


def reset_demo_state():
    """Удалить уведомления и сделки; вернуть объекты sold/archived в каталог (active)."""
    Notification.objects.all().delete()
    Deal.objects.all().delete()
    Property.objects.filter(status__in=["sold", "archived"]).update(status="active")


def main():
    reset_demo_state()
    ensure_demo_image_dirs()

    # Суперпользователь для Django Admin (URL см. realestate_site/urls.py → internal-admin-only)
    admin_user, _ = User.objects.get_or_create(
        username="demo_admin",
        defaults={
            "email": "admin@example.com",
            "is_staff": True,
            "is_superuser": True,
        },
    )
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.set_password("demo_admin_pass")
    admin_user.save()

    # Единственный демо-аккаунт риэлтора
    realtor_user, _ = User.objects.get_or_create(
        username="demo_realtor",
        defaults={
            "email": "realtor@example.com",
            "first_name": "Демо",
            "last_name": "Риэлтор",
        },
    )
    # Всегда ставим известный демо-пароль, чтобы логин точно работал.
    realtor_user.set_password("demo_realtor_pass")
    realtor_user.save()

    realtor_profile, _ = Realtor.objects.get_or_create(
        user=realtor_user,
        defaults={
            "phone": "+7 999 000 00 00",
            "position": "Ведущий специалист",
            "bio": "Сопровождаю сделки с недвижимостью с 2015 года.",
        },
    )

    apartment, _ = PropertyType.objects.get_or_create(name="Квартира")
    house, _ = PropertyType.objects.get_or_create(name="Дом")
    commercial, _ = PropertyType.objects.get_or_create(name="Коммерция")

    moscow, _ = City.objects.get_or_create(name="Москва")
    spb, _ = City.objects.get_or_create(name="Санкт-Петербург")
    kazan, _ = City.objects.get_or_create(name="Казань")

    central, _ = District.objects.get_or_create(city=moscow, name="Центральный")
    khamovniki, _ = District.objects.get_or_create(city=moscow, name="Хамовники")
    petrogradsky, _ = District.objects.get_or_create(city=spb, name="Петроградский")
    admiralteysky, _ = District.objects.get_or_create(city=spb, name="Адмиралтейский")
    sovetsky, _ = District.objects.get_or_create(city=kazan, name="Советский")

    properties = [
        {
            "title": "2-комнатная квартира в центре Москвы",
            "property_type": apartment,
            "city": moscow,
            "district": central,
            "deal_type": "sale",
            "status": "active",
            "price": 18500000,
            "area": 64,
            "rooms": 2,
            "floor": 7,
            "total_floors": 12,
            "address": "ул. Тверская, 7",
            "description": "Светлая квартира в центре Москвы, рядом парк, метро и вся инфраструктура.",
            "latitude": 55.7577,
            "longitude": 37.6156,
            "is_featured": True,
            "image_colors": [(52, 64, 78), (62, 78, 94), (48, 58, 72)],
        },
        {
            "title": "Офисный блок в деловом квартале",
            "property_type": commercial,
            "city": spb,
            "district": petrogradsky,
            "deal_type": "rent",
            "status": "active",
            "price": 780000,
            "area": 88,
            "rooms": 3,
            "floor": 9,
            "total_floors": 18,
            "address": "Большой проспект П.С., 55",
            "description": "Подойдёт под IT-команду, сервис или представительство компании.",
            "latitude": 59.965,
            "longitude": 30.311,
            "is_featured": False,
            "image_colors": [(58, 70, 86), (68, 84, 100), (44, 54, 68)],
        },
        {
            "title": "Дом с участком и террасой",
            "property_type": house,
            "city": kazan,
            "district": sovetsky,
            "deal_type": "sale",
            "status": "active",
            "price": 52000000,
            "area": 140,
            "rooms": 5,
            "floor": None,
            "total_floors": None,
            "address": "коттеджный посёлок у озера",
            "description": "Большой семейный дом с садом, гаражом и тихой улицей.",
            "latitude": 55.865,
            "longitude": 49.08,
            "is_featured": True,
            "image_colors": [(55, 68, 82), (65, 80, 96), (50, 60, 74)],
        },
        {
            "title": "Студия рядом с набережной",
            "property_type": apartment,
            "city": moscow,
            "district": khamovniki,
            "deal_type": "rent",
            "status": "reserved",
            "price": 450000,
            "area": 38,
            "rooms": 1,
            "floor": 15,
            "total_floors": 18,
            "address": "Фрунзенская набережная, 15",
            "description": "Современная студия с новой мебелью, видом на набережную и быстрым интернетом.",
            "latitude": 55.7264,
            "longitude": 37.5786,
            "is_featured": False,
            "image_colors": [(54, 66, 80), (64, 76, 92), (46, 56, 70)],
        },
        {
            "title": "Торговое помещение на первой линии",
            "property_type": commercial,
            "city": spb,
            "district": admiralteysky,
            "deal_type": "sale",
            "status": "active",
            "price": 87500000,
            "area": 210,
            "rooms": None,
            "floor": 1,
            "total_floors": 9,
            "address": "Невский проспект, 48",
            "description": "Готовое помещение под магазин, шоурум или кофейню на первой линии.",
            "latitude": 59.9322,
            "longitude": 30.3466,
            "is_featured": False,
            "image_colors": [(56, 68, 84), (66, 82, 98), (48, 58, 72)],
        },
    ]

    for prop_index, item in enumerate(properties):
        image_colors = item.pop("image_colors")
        prop, _ = Property.objects.update_or_create(title=item["title"], defaults=item)
        if prop.realtor_id != realtor_profile.id:
            prop.realtor = realtor_profile
            prop.save(update_fields=["realtor"])
        PropertyImage.objects.filter(property=prop).delete()
        for idx, rgb in enumerate(image_colors):
            pi = PropertyImage(
                property=prop,
                caption=f"{prop.title} · фото {idx + 1}",
            )
            disk = DEMO_IMAGES / "properties" / f"p{prop_index}_{idx}.jpg"
            if disk.is_file() and disk.stat().st_size > 500:
                raw = disk.read_bytes()
            else:
                raw = jpeg_placeholder(rgb)
            pi.image.save(f"demo_{prop.id}_{idx}.jpg", ContentFile(raw), save=False)
            pi.save()

    CompanyGalleryImage.objects.all().delete()
    gallery_rows = [
        ("Команда и офис", (46, 58, 72)),
        ("Подбор объектов", (58, 72, 88)),
        ("Сделка под ключ", (40, 50, 64)),
    ]
    for order, (caption, rgb) in enumerate(gallery_rows):
        g = CompanyGalleryImage(caption=caption, sort_order=order)
        disk = DEMO_IMAGES / f"gallery_{order}.jpg"
        if disk.is_file() and disk.stat().st_size > 500:
            raw = disk.read_bytes()
        else:
            raw = jpeg_placeholder(rgb, w=1400, h=900)
        g.image.save(f"gallery_{order}.jpg", ContentFile(raw), save=False)
        g.save()

    LeadInquiry.objects.update_or_create(
        full_name="Анна Серова",
        defaults={
            "phone": "+7 901 111 22 33",
            "email": "anna@example.com",
            "city": moscow,
            "property_type": apartment,
            "deal_type": "sale",
            "preferred_rooms": 2,
            "budget_min": 15000000,
            "budget_max": 22000000,
            "message": "Ищем 2-комнатную квартиру в центре Москвы с ремонтом.",
            "status": "new",
        },
    )
    LeadInquiry.objects.update_or_create(
        full_name="Игорь Ковалёв",
        defaults={
            "phone": "+7 921 444 55 66",
            "email": "igor@example.com",
            "city": spb,
            "property_type": commercial,
            "deal_type": "rent",
            "preferred_rooms": 3,
            "budget_min": 500000,
            "budget_max": 900000,
            "message": "Нужен офис под команду 8–10 человек рядом с метро.",
            "status": "in_progress",
        },
    )
    LeadInquiry.objects.update_or_create(
        full_name="Мария Трофимова",
        defaults={
            "phone": "+7 937 222 33 44",
            "email": "maria@example.com",
            "city": kazan,
            "property_type": house,
            "deal_type": "sale",
            "preferred_rooms": 5,
            "budget_min": 40000000,
            "budget_max": 60000000,
            "message": "Ищем семейный дом с участком и террасой недалеко от города.",
            "status": "new",
        },
    )

    print("seed created")


if __name__ == "__main__":
    main()
