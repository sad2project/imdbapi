import pprint
from abc import ABC, abstractmethod

import requests
import logging

from .image import ImageUrl, ImageSize, image_info_from_url, AspectRatio
from .poster import PosterSize, PosterUrl
from .caching.req_cache import RequestsSQLiteBackedMemoryCache

__all__ = ['ImdbApi', 'ApiError', 'ImageUrl', 'image_info_from_url', 'CacheInfo',
           'ImageSize', 'AspectRatio', 'PosterSize', 'PosterUrl', 'TitleUrl',
           'PersonUrl', 'FullCastUrl']


class CacheInfo(ABC):
    @abstractmethod
    def get(self, arg: str, sync_cache=False):
        ...

    @staticmethod
    def of(db_path: str, mem_cache_max_size: int):
        return UseCache(RequestsSQLiteBackedMemoryCache(db_path, mem_cache_max_size))

    @staticmethod
    def no_cache():
        return NoCache()


class UseCache(CacheInfo):
    def __init__(self, cache):
        self.cache = cache

    def get(self, arg: str, sync_cache=False):
        return self.cache(arg, sync_cache=sync_cache)


class NoCache(CacheInfo):
    def get(self, url: str, sync_cache=False):
        return requests.get(url), False


class ImdbApi:
    def __init__(self, api_key: str, cache_info: CacheInfo):
        self.requester = cache_info
        self.api_key = api_key

    def search_title(self, search_term: str, sync_cache=False) -> tuple[dict, bool]:
        url = self._make_url('SearchTitle', search_term)
        logging.info(f'running title search: {url}')
        return self._request_json_results(url, sync_cache)

    def search_series(self, search_term: str, sync_cache=False) -> tuple[dict, bool]:
        url = self._make_url('SearchSeries', search_term)
        logging.info(f'running series search: {url}')
        return self._request_json_results(url, sync_cache)

    def search_movie(self, search_term: str, sync_cache=False) -> tuple[dict, bool]:
        url = self._make_url('SearchMovie', search_term)
        logging.info(f'running movie search: {url}')
        return self._request_json_results(url, sync_cache)

    def search_episode(self, search_term: str, sync_cache=False) -> tuple[dict, bool]:
        url = self._make_url('SearchEpisode', search_term)
        logging.info(f'running episode search: {url}')
        return self._request_json_results(url, sync_cache)

    def search_name(self, search_term: str, sync_cache=False) -> tuple[dict, bool]:
        url = self._make_url('SearchName', search_term)
        logging.info(f'running name search: {url}')
        return self._request_json_results(url, sync_cache)

    def title(self, id: str, *options, sync_cache=False) -> tuple[dict, bool]:
        url_options = ','.join(options)
        url = self._make_url('Title', id, url_options)
        logging.info(f'running title details lookup: {url}')
        return self._request_json(url, sync_cache)

    def season(self, show_id: str, season_num: str, sync_cache=False) -> tuple[dict, bool]:
        url = self._make_url('SeasonEpisodes', show_id, season_num)
        logging.info(f'running season details lookup: {url}')
        return self._request_json(url, sync_cache)

    def download_poster(self, poster_id, size: 'PosterSize', sync_cache=False) -> tuple[bytes,
                                                                                        bool]:
        url = PosterUrl.with_size(poster_id, size)
        logging.info(f'downloading poster from {url}')
        return self._request_content(url, sync_cache)

    def download_image(self, image_id, size: ImageSize, sync_cache=False) -> tuple[bytes, bool]:
        url = ImageUrl.with_size(image_id, size)
        logging.info(f'downloading image from {url}')
        return self._request_content(url, sync_cache)

    def check_usage(self) -> tuple[int, int]:
        url = self._make_url('Usage')
        logging.info(f'checking usage amount')
        json = requests.get(url).json()
        if json['errorMessage']:
            return 0, 100
        else:
            return json['count'], json['maximum']

    def _request_json_results(self, url, sync_cache) -> tuple[dict, bool]:
        response, from_cache = self.requester.get(url, sync_cache)
        json = response.json()
        if json['errorMessage']:
            raise ApiError(json['errorMessage'])
        else:
            return json['results'], from_cache

    def _request_json(self, url, sync_cache) -> tuple[dict, bool]:
        response, from_cache = self.requester.get(url, sync_cache)
        json = response.json()
        if json['errorMessage']:
            raise ApiError(json['errorMessage'])
        else:
            return json, from_cache

    def _request_content(self, url, sync_cache) -> tuple[bytes, bool]:
        response, from_cache = self.requester.get(url, sync_cache)
        return response.content, from_cache

    def _make_url(self, endpoint, *terms):
        url_terms = "/".join((term for term in terms if term != ''))
        return f'https://imdb-api.com/en/API/{endpoint}/{self.api_key}/{url_terms}'


class ApiError(Exception):
    pass


class TitleUrl:
    TITLE_URL_FORMAT = 'https://www.imdb.com/title/{id}'
    SEASON_URL_SUFFIX_FORMAT = '/episodes?season={season}'

    @classmethod
    def for_id(cls, id):
        return cls.TITLE_URL_FORMAT.format(id=id)

    @classmethod
    def for_season(cls, id, season):
        return (cls.TITLE_URL_FORMAT.format(id=id) +
                cls.SEASON_URL_SUFFIX_FORMAT.format(season=season))


class PersonUrl:
    PERSON_URL_FORMAT = 'https://www.imdb.com/name/{id}'

    @classmethod
    def for_person(cls, id):
        return cls.PERSON_URL_FORMAT.format(id=id)


class FullCastUrl:
    FULL_CAST_URL_FORMAT = 'https://www.imdb.com/title/{id}/fullcredits/cast'

    @classmethod
    def for_title(cls, id):
        return cls.FULL_CAST_URL_FORMAT.format(id=id)
