import requests

from .caching import SQLiteKeyValueStore, LruStore


def do_request(url):
    response = requests.get(url)
    return response.content, response


def recreate_request(content):
    response = requests.Response()
    response._content = content
    return response, True


class RequestsSQLiteBackedMemoryCache:
    def __init__(self, db_path: str, mem_cache_max_size: int=20):
        self.file_cache = SQLiteKeyValueStore(db_path)
        self.mem_cache = LruStore(mem_cache_max_size)

    def __call__(self, url: str, sync_cache=False) -> tuple[requests.Response, bool]:
        if sync_cache:
            return self.sync_cache(url)
        else:
            return self.normal_call(url)

    def normal_call(self, url: str):
        if url in self.mem_cache:
            return recreate_request(self.mem_cache[url])
        if url in self.file_cache:
            content = self.file_cache[url]
            self.mem_cache[url] = content
            return recreate_request(content)
        else:
            return self.sync_cache(url)

    def sync_cache(self, url: str):
        content, result = do_request(url)
        self.mem_cache[url] = content
        self.file_cache[url] = content
        return result, False
