import secrets

def generate_uuid(length: int = 32) -> str:
    return secrets.token_hex(length)