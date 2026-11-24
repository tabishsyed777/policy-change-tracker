import unicodedata

def norm(value):
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def require(condition, message):
    if not condition:
        raise ValueError(message)


