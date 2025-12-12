# data_sources/parliament/client.py
from ._vendor.pypd import ParliamentApiClient

_client = None

def get_client():
    global _client
    if _client is None:
        _client = ParliamentApiClient()
    return _client