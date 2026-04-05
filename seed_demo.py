import os

import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "realestate_site.settings")
django.setup()

from django.contrib.auth import get_user_model
from listings.models import (
    City,
    Deal,
    District,
    LeadInquiry,
    MetroStation,
    Notification,
    Property,
    PropertyMetro,
    PropertyChatMessage,
    PropertyType,
    Realtor,
)


User = get_user_model()


def reset_demo_state():
    """Удалить уведомления и сделки; вернуть объекты sold/archived в каталог (active)."""
    PropertyChatMessage.objects.all().delete()
    Notification.objects.all().delete()
    Deal.objects.all().delete()
    Property.objects.filter(status__in=["sold", "archived"]).update(status="active")


def main():
    reset_demo_state()

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
        },
        {
            "title": "1-комнатная у метро «Тверская»",
            "property_type": apartment,
            "city": moscow,
            "district": central,
            "deal_type": "sale",
            "status": "active",
            "price": 14200000,
            "area": 38,
            "rooms": 1,
            "floor": 4,
            "total_floors": 8,
            "address": "Тверская ул., 18",
            "description": "Компактная квартира для жизни или инвестиций, пешком до метро.",
            "latitude": 55.757,
            "longitude": 37.61,
            "is_featured": False,
        },
        {
            "title": "3-комнатная с двумя санузлами, Хамовники",
            "property_type": apartment,
            "city": moscow,
            "district": khamovniki,
            "deal_type": "sale",
            "status": "active",
            "price": 28900000,
            "area": 92,
            "rooms": 3,
            "floor": 6,
            "total_floors": 14,
            "address": "Усачёва ул., 11",
            "description": "Светлые комнаты, вид во двор, развитая инфраструктура района.",
            "latitude": 55.732,
            "longitude": 37.575,
            "is_featured": True,
        },
        {
            "title": "Аренда 2-комнатной у Патриарших",
            "property_type": apartment,
            "city": moscow,
            "district": central,
            "deal_type": "rent",
            "status": "active",
            "price": 195000,
            "area": 58,
            "rooms": 2,
            "floor": 3,
            "total_floors": 5,
            "address": "Патриарший пер., 8",
            "description": "Тихий переулок, мебель по запросу, долгосрочная аренда.",
            "latitude": 55.761,
            "longitude": 37.599,
            "is_featured": False,
        },
        {
            "title": "Квартира-евродвушка, Петроградка",
            "property_type": apartment,
            "city": spb,
            "district": petrogradsky,
            "deal_type": "sale",
            "status": "active",
            "price": 12900000,
            "area": 45,
            "rooms": 2,
            "floor": 8,
            "total_floors": 12,
            "address": "Большой проспект П.С., 32",
            "description": "Современная планировка, ремонт, рядом парки и набережная.",
            "latitude": 59.96,
            "longitude": 30.315,
            "is_featured": False,
        },
        {
            "title": "Офис 120 м², класс B, Адмиралтейский",
            "property_type": commercial,
            "city": spb,
            "district": admiralteysky,
            "deal_type": "rent",
            "status": "active",
            "price": 1100000,
            "area": 120,
            "rooms": 4,
            "floor": 5,
            "total_floors": 11,
            "address": "Лермонтовский проспект, 3",
            "description": "Open space, переговорные, охрана и парковка по согласованию.",
            "latitude": 59.925,
            "longitude": 30.29,
            "is_featured": False,
        },
        {
            "title": "Таунхаус с гаражом, Казань",
            "property_type": house,
            "city": kazan,
            "district": sovetsky,
            "deal_type": "sale",
            "status": "active",
            "price": 18500000,
            "area": 165,
            "rooms": 4,
            "floor": None,
            "total_floors": None,
            "address": "пос. Зелёный бор",
            "description": "Два этажа, участок 4 сотки, детская площадка во дворе.",
            "latitude": 55.88,
            "longitude": 49.12,
            "is_featured": False,
        },
        {
            "title": "Студия в аренду, Казань центр",
            "property_type": apartment,
            "city": kazan,
            "district": sovetsky,
            "deal_type": "rent",
            "status": "active",
            "price": 28000,
            "area": 28,
            "rooms": 1,
            "floor": 12,
            "total_floors": 16,
            "address": "ул. Пушкина, 52",
            "description": "Новый дом, техника и мебель, для одного жильца.",
            "latitude": 55.79,
            "longitude": 49.12,
            "is_featured": False,
        },
        {
            "title": "4-комнатная пентхаус-стиль, Москва",
            "property_type": apartment,
            "city": moscow,
            "district": khamovniki,
            "deal_type": "sale",
            "status": "active",
            "price": 62000000,
            "area": 145,
            "rooms": 4,
            "floor": 18,
            "total_floors": 22,
            "address": "Комсомольский проспект, 41",
            "description": "Панорамные окна, терраса, премиальная отделка.",
            "latitude": 55.73,
            "longitude": 37.585,
            "is_featured": True,
        },
        {
            "title": "Помещение под кафе, первая линия СПб",
            "property_type": commercial,
            "city": spb,
            "district": admiralteysky,
            "deal_type": "sale",
            "status": "active",
            "price": 32000000,
            "area": 95,
            "rooms": None,
            "floor": 1,
            "total_floors": 4,
            "address": "наб. реки Фонтанки, 120",
            "description": "Витрины, высокий пешеходный трафик, отдельный вход.",
            "latitude": 59.928,
            "longitude": 30.335,
            "is_featured": False,
        },
        {
            "title": "2-комнатная с ремонтом, новостройка Москва",
            "property_type": apartment,
            "city": moscow,
            "district": central,
            "deal_type": "sale",
            "status": "active",
            "price": 19800000,
            "area": 56,
            "rooms": 2,
            "floor": 11,
            "total_floors": 25,
            "address": "ул. Новый Арбат, 15",
            "description": "Закрытый двор, консьерж, паркинг в доме.",
            "latitude": 55.752,
            "longitude": 37.588,
            "is_featured": False,
        },
    ]

    for _, item in enumerate(properties):
        prop, _ = Property.objects.update_or_create(title=item["title"], defaults=item)
        if prop.realtor_id != realtor_profile.id:
            prop.realtor = realtor_profile
            prop.save(update_fields=["realtor"])

    # Общие станции метро для кластера «центр Москвы» — больше пересечений в /api/similar/
    st_tver, _ = MetroStation.objects.get_or_create(
        city=moscow,
        name="Тверская",
        defaults={"line": "Замоскворецкая"},
    )
    st_push, _ = MetroStation.objects.get_or_create(
        city=moscow,
        name="Пушкинская",
        defaults={"line": "Таганско-Краснопресненская"},
    )
    st_nevsky, _ = MetroStation.objects.get_or_create(
        city=spb,
        name="Невский проспект",
        defaults={"line": "Зелёная"},
    )

    metro_links = [
        ("2-комнатная квартира в центре Москвы", st_tver, 420, 6),
        ("2-комнатная с ремонтом, новостройка Москва", st_tver, 580, 8),
        ("Аренда 2-комнатной у Патриарших", st_push, 640, 7),
        ("1-комнатная у метро «Тверская»", st_tver, 280, 4),
        ("3-комнатная с двумя санузлами, Хамовники", st_push, 720, 9),
        ("Квартира-евродвушка, Петроградка", st_nevsky, 510, 7),
        ("Офисный блок в деловом квартале", st_nevsky, 890, 11),
    ]
    for title, station, dist_m, walk_m in metro_links:
        prop = Property.objects.filter(title=title).first()
        if prop:
            PropertyMetro.objects.update_or_create(
                property=prop,
                station=station,
                defaults={
                    "distance_meters": dist_m,
                    "walking_time_minutes": walk_m,
                },
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
