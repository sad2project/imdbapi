from enum import Enum


class PosterSize(Enum):
    Original = 'original'
    Wide45 = 'w45'
    Wide92 = 'w92'
    Wide154 = 'w154'
    Wide185 = 'w185'
    Wide200 = 'w200'
    Wide300 = 'w300'
    Wide342 = 'w342'
    Wide400 = 'w400'
    Wide500 = 'w500'
    Wide780 = 'w780'
    Wide1280 = 'w1280'
    Square32 = 's32'
    Square45 = 's45'
    Square50 = 's50'
    Square64 = 's64'
    Square66 = 's66'
    Square90 = 's90'
    Square100 = 's100'
    Square115 = 's115'
    Square128 = 's128'
    Square132 = 's132'
    Square150 = 's150'
    Square180 = 's180'
    Square230 = 's230'
    Square235 = 's235'
    Square264 = 's264'
    Square300 = 's300'
    Square375 = 's375'
    Square470 = 's470'


class PosterUrl:
    POSTER_URL_FORMAT = 'https://imdb-api.com/Posters/{size}/{id}'

    @classmethod
    def with_size(cls, id, size: PosterSize):
        return cls.POSTER_URL_FORMAT.format(size=str(size), id=id)
