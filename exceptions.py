class StatusCodeError(Exception):
    """Код запроса отличается от 200."""

    pass


class TokenError(Exception):
    """Ошибка в проверке токенов."""

    pass


class ResponseError(Exception):
    """Неккоректный API ответ."""

    pass
