async def check_credentials(username: str, password: str) -> bool:
    return username == "admin" and password == "admin123"
