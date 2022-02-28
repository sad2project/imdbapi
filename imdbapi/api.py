import pprint
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union, TypeVar, Generic

from .bareapi.api import (ImdbApi as BareApi, ApiError, ImageSize, ImageUrl,
                         image_info_from_url, AspectRatio, PosterSize, PosterUrl, CacheInfo,
                         PersonUrl, TitleUrl, FullCastUrl)


T = TypeVar('T')

class ApiResult(Generic[T]):
    def __init__(self, result: T, cached: bool):
        self.result = result
        self.cached = cached


class ImdbApi:
    def __init__(self, api_back_end):
        self.api = api_back_end

    @classmethod
    def with_default_back_end(cls, api_key: str, caching: CacheInfo):
        return cls(BareApi(api_key, caching))

    def search_title(self, search_term: str, *, sync_cache=False) -> ApiResult[list['Title']]:
        result, cached = self.api.search_title(search_term, sync_cache=sync_cache)
        return ApiResult(Title.from_result_list(result), cached)

    def search_series(self, search_term: str, *, sync_cache=False) -> ApiResult[list['Title']]:
        result, cached = self.api.search_series(search_term, sync_cache=sync_cache)
        return ApiResult(Title.from_result_list(result), cached)

    def search_movie(self, search_term: str, *, sync_cache=False) -> ApiResult[list['Title']]:
        result, cached = self.api.search_movie(search_term, sync_cache=sync_cache)
        return ApiResult(Title.from_result_list(result), cached)

    def search_episode(self, search_term: str, *, sync_cache=False) -> ApiResult[list['Title']]:
        result, cached = self.api.search_episode(search_term, sync_cache=sync_cache)
        return ApiResult(Title.from_result_list(result), cached)

    def search_name(self, search_term: str, *, sync_cache=False) -> ApiResult[list[dict]]:
        result, cached = self.api.search_name(search_term, sync_cache=sync_cache)
        return ApiResult(Name.from_result_list(result), cached)

    def title(self, id, *options, sync_cache=False) -> ApiResult[Union[dict, 'TVSeries', 'Movie']]:
        result, cached = self.api.title(id, *options, sync_cache=sync_cache)
        if result['type'] == 'TVSeries':
            return ApiResult(TVSeries.from_result(result), cached)
        if result['type'] == 'Movie':
            return ApiResult(Movie.from_result(result), cached)
        else:
            return ApiResult(result, cached)

    def tv_series(self, id, *options, sync_cache=False) -> ApiResult['TVSeries']:
        result, cached = self.api.title(id, *options, sync_cache=sync_cache)
        return ApiResult(TVSeries.from_result(result), cached)

    def movie(self, id, *options, sync_cache=False) -> ApiResult['Movie']:
        result, cached = self.api.title(id, *options, sync_cache=sync_cache)
        return ApiResult(Movie.from_result(result), cached)

    def season(self, series: 'TVSeries', season_num, *, sync_cache=False) -> ApiResult['Season']:
        if season_num not in series:
            raise ValueError(f'{season_num} is not a valid season for {series.title}. ' 
                             f'Choose from {series.seasons}')
        result, cached = self.api.season(series.id, str(season_num), sync_cache=sync_cache)
        return ApiResult(Season.from_result(result, int(season_num)), cached)

    def all_seasons(self, series: 'TVSeries', *, sync_cache=False) -> ApiResult[list['Season']]:
        any_cached = False
        init_results = [self.season(series, season, sync_cache=sync_cache)
                        for season in series]
        seasons: list[Season] = []
        for api_result in init_results:
            seasons.append(api_result.result)
            any_cached = any_cached or api_result.cached
        return ApiResult(seasons, any_cached)

    def look_up_full_title_data(self, title: 'Title', *, sync_cache=False) -> ApiResult[Union[dict,
                                                                                           'TVSeries', 'Movie']]:
        return self.title(title.id, 'Posters', sync_cache=sync_cache)

    def check_usage(self):
        return self.api.check_usage()


class Mappable(ABC):
    @classmethod
    @abstractmethod
    def from_result(cls, result):
        ...

    @classmethod
    def from_result_list(cls, results):
        if results is None:
            return []
        return [cls.from_result(result) for result in results]

    @property
    @abstractmethod
    def imdb_link(self):
        ...

    def __format__(self, format_spec):
        if format_spec == '':
            return str(self)
        if format_spec == 'r':
            return repr(self)
        if format_spec == 's':
            return self._short_format()
        else:
            raise ValueError(f"'{format_spec}' is not a valid format for {type(self).__name__}")

    @abstractmethod
    def _short_format(self):
        ...


@dataclass
class Title(Mappable):
    id: str
    title: str
    image: str
    description: str

    @classmethod
    def from_result(cls, result):
        return cls(
                result['id'],
                result['title'],
                result['image'],
                result['description'])

    @property
    def imdb_link(self):
        return TitleUrl.for_id(self.id)

    def full_cast_link(self):
        return FullCastUrl.for_title(self.id)

    def _short_format(self):
        return f'{self.id} - {self.title}'


@dataclass
class TVSeries(Mappable):
    id: str
    title: str
    full_title: str
    image: 'Image'
    cast: list['CastMember']
    plot: str
    genres: list
    imdb_rating: str
    posters: list['Poster']
    seasons: list

    @classmethod
    def from_result(cls, result):
        posters = result['posters']
        return cls(
            result['id'],
            result['title'],
            result['fullTitle'],
            Image.from_result(result['image']),
            CastMember.from_result_list(result['actorList']),
            result['plot'],
            result['genres'].split(', '),
            result['imDbRating'],
            Poster.from_result_list(
                posters['posters'] if posters is not None else []),
            result['tvSeriesInfo']['seasons'])

    @property
    def imdb_link(self):
        return TitleUrl.for_id(self.id)

    def full_cast_link(self):
        return FullCastUrl.for_title(self.id)

    def __contains__(self, season_number: Union[int, str]):
        return str(season_number) in self.seasons

    def __iter__(self):
        return iter(self.seasons)

    def __getitem__(self, item: Union[int, str]):
        return self.seasons[int(item) - 1]

    def _short_format(self):
        return f'{self.id} - {self.full_title}'


@dataclass
class Season(Mappable):
    show_id: str
    show_title: str
    season_number: int
    episodes: list['Episode']

    @classmethod
    def from_result(cls, result, season_number=None):
        if season_number is None:
            if 'season_number' in result:
                season_number = result['season_number']
            else:
                raise KeyError('season number was not passed in via result or direct argument')
        return cls(
            result['imDbId'],
            result['title'],
            int(season_number),
            Episode.from_result_list(
                result['episodes'], result['imDbId'], result['title']))

    def __iter__(self):
        return iter(self.episodes)

    def episode(self, item: int):
        return self.episodes[item - 1]

    @property
    def imdb_link(self):
        return TitleUrl.for_season(self.show_id, self.season_number)

    def _short_format(self):
        return f'Season {self.season_number} of {self.show_title} ({self.show_id})'


@dataclass
class Episode(Mappable):
    id: str
    title: str
    show_id: str
    show_title: str
    season: int
    episode: int
    image: 'Image'
    release_date: str
    plot: str
    imdb_rating: str

    @classmethod
    def from_result(cls, result, show_id=None, show_title=None):
        if show_id is None:
            if 'show_id' in result:
                show_id = result['show_id']
            else:
                raise KeyError('series id was not passed in via result or direct argument')
        if show_title is None:
            if 'show_id' in result:
                show_title = result['show_title']
            else:
                raise KeyError('series title was not passed in via result or direct argument')

        return cls(
            result['id'],
            result['title'],
            show_id,
            show_title,
            int(result['seasonNumber']),
            int(result['episodeNumber']),
            Image.from_result(result['image']),
            result['released'],
            result['plot'],
            result['imDbRating'])

    @classmethod
    def from_result_list(cls, results, show_id=None, show_title=None):
        if results is None:
            return None

        for result in results:
            result['show_id'] = show_id
            result['show_title'] = show_title
        return super().from_result_list(results)

    @property
    def imdb_link(self):
        return TitleUrl.for_id(self.id)

    def full_cast_link(self):
        return FullCastUrl.for_title(self.id)

    def _short_format(self):
        return f'{self.id} - {self.title} (S{self.season}E{self.episode} of {self.show_title})'


@dataclass
class Movie(Mappable):
    id: str
    title: str
    full_title: str
    image: str
    cast: list['CastMember']
    plot: str
    genres: list
    imdb_rating: str
    posters: list

    @classmethod
    def from_result(cls, result):
        posters = result['posters']
        return cls(
            result['id'],
            result['title'],
            result['fullTitle'],
            result['image'],
            CastMember.from_result_list(result['actorList']),
            result['plot'],
            result['genres'].split(', '),
            result['imDbRating'],
            Poster.from_result_list(posters['posters']) if posters is not None else [])

    @property
    def imdb_link(self):
        return TitleUrl.for_id(self.id)

    def full_cast_link(self):
        return FullCastUrl.for_title(self.id)

    def _short_format(self):
        return f'{self.id}: {self.full_title}'


@dataclass
class CastMember(Mappable):
    id: str
    name: str
    as_character: str
    image: 'Image'

    @classmethod
    def from_result(cls, result):
        # asCharacter is coming in weird, saying stuff like 'Tophas Toph'
        as_ = result['asCharacter']
        as_end = ((len(as_) - 3) // 2)
        return cls(
            result['id'],
            result['name'],
            as_[:as_end],
            Image.from_result(result['image']))

    @property
    def imdb_link(self):
        return PersonUrl.for_person(self.id)

    def _short_format(self):
        return f'{self.id}: {self.name} as {self.as_character}'


@dataclass
class Name(Mappable):
    id: str
    name: str
    image: 'Image'

    @classmethod
    def from_result(cls, result):
        return cls(
            result['id'],
            result['title'],
            Image.from_result(result['image']))

    @property
    def imdb_link(self):
        return PersonUrl.for_person(self.id)

    def _short_format(self):
        return f'{self.id}: {self.name}'


@dataclass
class Poster(Mappable):
    id: str
    size: PosterSize
    link: str

    @classmethod
    def from_result(cls, result):
        return cls(
            result['id'],
            Poster.read_size_from_url(result['link']),
            result['link'])

    @staticmethod
    def read_size_from_url(url: str):
        end_of_size = url.find('/', 28)
        return PosterSize(url[28:end_of_size])

    def with_size(self, size: PosterSize):
        return Poster(
            self.id,
            size,
            PosterUrl.with_size(self.id, size))

    @property
    def imdb_link(self):
        return self.link

    def _short_format(self):
        return f'{self.id}: {self.size.name}'


@dataclass
class Image(Mappable):
    id: str
    size: ImageSize
    aspect_ratio: AspectRatio
    link: str

    @classmethod
    def from_result(cls, url):
        size, aspect_ratio, id = image_info_from_url(url)
        return cls(
            id,
            size,
            aspect_ratio,
            url)

    def with_size(self, size: ImageSize):
        aspect_ratio = size.aspect_ratio(AspectRatio.from_url_or_id(self.id))
        return Image(
            self.id,
            size,
            aspect_ratio,
            ImageUrl.with_size(self.id, size))

    @property
    def imdb_link(self):
        return self.link

    def _short_format(self):
        return f'{self.id}: {str(self.size)}'
