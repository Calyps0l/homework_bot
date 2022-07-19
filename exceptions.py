class StatusCodeError(Exception):
    """Код запроса отличается от 200."""

    pass


class ResponseError(Exception):
    """Неккоректный API ответ."""

    pass
