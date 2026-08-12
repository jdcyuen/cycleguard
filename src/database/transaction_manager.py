from contextlib import contextmanager


class TransactionManager:

    def __init__(self, connection):
        self.connection = connection

    @contextmanager
    def transaction(self):
        try:
            yield
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise