from fastapi import Response

def no_cache_headers(response: Response):
    """
    Добавляет заголовки, запрещающие кеширование на клиенте.
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response