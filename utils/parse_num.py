def parse_formatted_number(formatted_str: str) -> float:
    """
    Преобразует отформатированную строку обратно в число
    Поддерживает русские обозначения: тыс, млн, млрд, трлн
    """
    if not formatted_str or formatted_str == "0":
        return 0.0

    # Убираем '/сек' если есть
    clean_str = formatted_str.replace('/сек', '').strip()

    # Парсим русские обозначения
    if ' трлн' in clean_str:
        return float(clean_str.replace(' трлн', '')) * 1_000_000_000_000
    elif ' млрд' in clean_str:
        return float(clean_str.replace(' млрд', '')) * 1_000_000_000
    elif ' млн' in clean_str:
        return float(clean_str.replace(' млн', '')) * 1_000_000
    elif ' тыс' in clean_str:
        return float(clean_str.replace(' тыс', '')) * 1_000
    else:
        # Просто число
        return float(clean_str)