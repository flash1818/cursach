import os

import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "realestate_site.settings")
django.setup()

from django.contrib.auth import get_user_model
from listings.models import City, District, LeadInquiry, Property, PropertyImage, PropertyType, Realtor


User = get_user_model()


def main():
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
        defaults={"phone": "+7 999 000 00 00"},
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
            "image_urls": [
                "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=900&q=80",
                "https://images.unsplash.com/photo-1493809842364-78817add7ffb?auto=format&fit=crop&w=900&q=80",
                "https://images.unsplash.com/photo-1493809842364-78817add7ffb?auto=format&fit=crop&w=900&q=80",
            ],
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
            "image_urls": [
                "https://images.unsplash.com/photo-1529424301806-4be0bb154e3b?auto=format&fit=crop&w=900&q=80",
                "https://images.unsplash.com/photo-1483478550801-ceba5fe50e8e?auto=format&fit=crop&w=900&q=80",
                "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=900&q=80",
            ],
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
            "image_urls": [
                "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=900&q=80",
                "https://images.unsplash.com/photo-1600607687920-4e2a5345c9a5?auto=format&fit=crop&w=900&q=80",
                "https://images.unsplash.com/photo-1600585154340-0ef3c08c0632?auto=format&fit=crop&w=900&q=80",
            ],
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
            "image_urls": [
                "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=900&q=80",
                "https://images.unsplash.com/photo-1523755231516-e43fd2e8dca5?auto=format&fit=crop&w=900&q=80",
                "https://images.unsplash.com/photo-1505691723518-36a5ac3be353?auto=format&fit=crop&w=900&q=80",
            ],
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
            "image_urls": [
                "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=900&q=80",
                "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=900&q=80",
                "https://images.unsplash.com/photo-1529429617124-aee63a28bd55?auto=format&fit=crop&w=900&q=80",
            ],
        },
    ]

    for item in properties:
        image_urls = item.pop("image_urls")
        prop, _ = Property.objects.update_or_create(title=item["title"], defaults=item)
        # Все демо-объекты привязаны к единственному риэлтору
        if prop.realtor_id != realtor_profile.id:
            prop.realtor = realtor_profile
            prop.save(update_fields=["realtor"])
        for idx, url in enumerate(image_urls):
            PropertyImage.objects.update_or_create(
                property=prop,
                image_url=url,
                defaults={"caption": f"{prop.title} · фото {idx + 1}"},
            )

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
