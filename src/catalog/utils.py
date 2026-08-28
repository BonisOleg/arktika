"""Допоміжні функції форматування, без залежності від Django ORM (щоб уникнути циклічних імпортів)."""
from decimal import Decimal


def format_weight(value_kg) -> str:
    """Форматує вагу в кг: до 1 кг — у грамах («300 г»), від 1 кг — у кг («1.5 кг»).

    Правило клієнта: «якщо вага до 1кг, то вказуємо в гр, якщо більше то в кг»."""
    value = Decimal(str(value_kg))
    if value < 1:
        grams = int((value * 1000).to_integral_value())
        return f"{grams} г"
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return f"{text} кг"
