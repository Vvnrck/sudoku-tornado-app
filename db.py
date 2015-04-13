import json
from string import ascii_letters, digits
from random import choice

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

import settings
import sudoku
import utils


Base = declarative_base()
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_size=20)


def open_db_session(expire_on_commit=True):
    return sessionmaker(bind=engine, expire_on_commit=expire_on_commit)()


class Sudoku(Base):
    """
    Sudoku database table.
    Columns:
        1. id.
        2. sudoku_name. Each sudoku can be accessed by it's name.
        3. field. JSON array of 81 elements that reflects current
                  sudoku game state. This array should be initialized
                  as an array of zeros.
                  [{val: 0, cand: []}, ...]
    """
    __tablename__ = 'sudoku'

    id = Column(Integer, primary_key=True)
    sudoku_name = Column(String(settings.SUDOKU_NAME_LEN), nullable=False, unique=True)
    field = Column(String(4000), nullable=False)
    next_sudoku = Column(String(settings.SUDOKU_NAME_LEN), nullable=False, unique=True)

    def __repr__(self):
        return 'Sudoku: id = {0}, name = {1}'.format(self.id, self.sudoku_name)

    @staticmethod
    def new(number_on_fields, save_to_db=True, session=None):
        sudoku_puzzle = sum(sudoku.construct_sudoku(number_on_fields), [])
        name = utils.get_random_string(settings.SUDOKU_NAME_LEN)
        next_sudoku = utils.get_random_string(settings.SUDOKU_NAME_LEN)
        field = [{'val': n, 'cand': [], 'readonly': 1 if n else 0} for n in sudoku_puzzle]
        field = json.dumps(field)
        sudoku_puzzle = Sudoku(sudoku_name=name, field=field, next_sudoku=next_sudoku)
        if save_to_db:
            Sudoku.save(sudoku_puzzle, session)
        return sudoku_puzzle

    @staticmethod
    def save(sudoku_puzzle, session=None):
        _session = session or open_db_session()
        _session.add(sudoku_puzzle)
        _session.commit()
        if session is None:
            _session.close()

    @staticmethod
    def update(sudoku_name, row, column, value):
        session = open_db_session()
        sudoku_ = session.query(Sudoku).filter(Sudoku.sudoku_name == sudoku_name)
        sudoku_ = sudoku_.first()
        field = None
        next_name = None
        if sudoku_:
            next_name = sudoku_.next_sudoku
            field = json.loads(sudoku_.field)
            cell = (row - 1) * 9 + column - 1
            readonly = int(field[cell]['readonly']) == 1
            if not readonly:
                field[cell]['val'] = value
                sudoku_.field = json.dumps(field)
                Sudoku.save(sudoku_, session)
        session.close()
        return field, next_name

    def sudoku_completed(self):
        field = json.loads(self.field)

        return True


if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)

