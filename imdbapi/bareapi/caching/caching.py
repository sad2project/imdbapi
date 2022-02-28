import contextlib
import sqlite3
from collections import deque


@contextlib.contextmanager
def open_db(db: str):
    connection = sqlite3.connect(db)
    cursor = connection.cursor()
    yield cursor
    connection.commit()
    connection.close()


class SQLiteKeyValueStore:
    def __init__(self, dbpath):
        self.db = dbpath
        with open_db(self.db) as db:
            db.execute('CREATE TABLE IF NOT EXISTS cache'
                       '(key TEXT PRIMARY KEY ON CONFLICT REPLACE,'
                       'value BLOB)')

    def __setitem__(self, key: str, value):
        with open_db(self.db) as db:
            db.execute('INSERT INTO cache VALUES (?, ?)', (key, value))
        return value

    def __delitem__(self, key: str):
        with open_db(self.db) as db:
            db.execute('DELETE FROM cache WHERE key = ?', (key,))

    def __getitem__(self, key: str):
        with open_db(self.db) as db:
            result = db.execute('SELECT value FROM cache WHERE key = ?', (key,)).fetchone()
            if result is None:
                return result
            return result[0]

    def __contains__(self, item):
        return self[item] is not None

    def __iter__(self):
        with open_db(self.db) as db:
            db.execute('SELECT * FROM cache')
            yield from db


class LruStore:
    def __init__(self, max_size: int):
        self.storage = {}
        self.usage_order = deque((), maxlen=max_size)
        self.max_size = max_size

    def __getitem__(self, key):
        if key in self.storage:
            self.usage_order.remove(key)
            self.usage_order.append(key)
        return self.storage[key]

    def __setitem__(self, key, value):
        if len(self.usage_order) == self.max_size:
            olditem = self.usage_order[0]
            self.usage_order.popleft()
            del self.storage[olditem]
        self.storage[key] = value
        self.usage_order.append(key)

    def __delitem__(self, key):
        self.usage_order.remove(key)
        del self.storage[key]

    def __contains__(self, key):
        return key in self.storage
