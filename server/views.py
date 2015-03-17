import json

import tornado.ioloop
import tornado.web
import tornado.template

import server.api
import settings
import db
import utils


class ViewSettingsMixin:
    def get_context_data(self, *args, **kwargs):
        context = {
            'STATIC_URL': settings.STATIC_URL
        }
        return context


class Handler(tornado.web.RequestHandler):
    template = 'base.html'

    def get_context_data(self, *args, **kwargs) -> dict:
        return {}

    def view(self, *args, **kwargs):
        loader = tornado.template.Loader(settings.TEMPLATE_DIR)
        context = self.get_context_data(*args, **kwargs)
        return loader.load(self.template).generate(**context)

    def get(self, *args, **kwargs):
        self.write(self.view(*args, **kwargs))


class MainHandler(Handler):
    template = 'menu.html'

    def get_context_data(self, *args, **kwargs):
        return {
            'url': settings.URL,
            'games': server.api.list_active_games(),
            'random_string': utils.get_random_string(settings.SUDOKU_NAME_LEN)
        }


class SudokuHandler(Handler):
    template = 'sudoku.html'

    @staticmethod
    def fetch_sudoku(sudoku_id) -> db.Sudoku:
        session = db.open_db_session()
        sudoku = session.query(db.Sudoku).filter(db.Sudoku.sudoku_name == sudoku_id)
        sudoku = sudoku.first() or db.Sudoku.new(
            settings.SUDOKU_GRID_NUMBERS, save_to_db=False, session=session)
        sudoku.sudoku_name = sudoku_id
        db.Sudoku.save(sudoku, session)
        return sudoku

    def get_context_data(self, *args, **kwargs):
        sudoku_name = args[0]
        sudoku = self.fetch_sudoku(sudoku_name)
        sudoku_field = [[None] * 9 for _ in range(9)]
        for i, cell in enumerate(json.loads(sudoku.field)):
            sudoku_field[i // 9][i % 9] = cell['val']
        context = {
            'sudoku': self.fetch_sudoku(sudoku_name),
            'sudoku_field': sudoku_field,
            'url': settings.URL
        }
        return context