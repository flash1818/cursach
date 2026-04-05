"""Нормализация российского номера для регистрации и профиля."""

import re


def digits_only(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def normalize_ru_phone(value: str) -> str:
    """
    Принимает ввод вида +7..., 8..., 9XXXXXXXXX.
    Возвращает строку вида +79001234567 или пустую строку, если поле пустое.
    """
    raw = (value or "").strip()
    if not raw:
        return ""
    d = digits_only(raw)
    if len(d) == 11 and d.startswith("8"):
        d = "7" + d[1:]
    elif len(d) == 10 and d.startswith("9"):
        d = "7" + d
    elif len(d) == 11 and d.startswith("7"):
        pass
    else:
        raise ValueError("Введите мобильный номер РФ: 10 цифр или +7 / 8 в начале.")
    if len(d) != 11 or not d.startswith("7"):
        raise ValueError("Номер должен содержать 11 цифр и код страны 7.")
    if d[1] != "9":
        raise ValueError("Ожидается мобильный номер (после +7 — 9…).")
    return f"+{d}"


def format_phone_display(e164: str) -> str:
    """+79001234567 → +7 (900) 123-45-67 для отображения."""
    d = digits_only(e164)
    if len(d) == 11 and d.startswith("7"):
        return f"+7 ({d[1:4]}) {d[4:7]}-{d[7:9]}-{d[9:11]}"
    return e164 or ""
