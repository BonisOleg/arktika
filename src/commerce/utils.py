from decimal import Decimal, InvalidOperation

VAT_RATE = Decimal("0.20")  # інформаційний розріз «в т.ч. ПДВ» — ціни вже включають ПДВ


def vat_from_gross(gross: Decimal) -> Decimal:
    """Частка ПДВ у сумі з ПДВ: gross × rate / (1 + rate)."""
    if not gross:
        return Decimal("0.00")
    return (Decimal(gross) * VAT_RATE / (1 + VAT_RATE)).quantize(Decimal("0.01"))


def get_or_create_session_key(request) -> str:
    """SEC-01: гість-кошик прив'язаний до Django session_key, не до IP/cookie власного винаходу."""
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def parse_quantity(raw, default: str = "1") -> Decimal:
    """Дробова кількість (вагові товари — крок 0.1 кг). Некоректний ввід → default,
    без падіння 500 на кривому POST (напр. крок мишкою під час зміни варіанта)."""
    text = str(raw).strip().replace(",", ".") if raw not in (None, "") else default
    try:
        value = Decimal(text)
    except InvalidOperation:
        value = Decimal(default)
    return value
