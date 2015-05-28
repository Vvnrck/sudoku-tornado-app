import json

import tornado.ioloop
import tornado.web
import tornado.template
import tornado.websocket
import tornado.gen

import settings
import db
import utils
import sudoku

from string import digits
from random import choice
from collections import defaultdict


socket_heap = []
sockets = defaultdict(list)


def list_active_games() -> 'list of pairs (name, players_online)':
    return [
        (name, len(online)) for name, online in sockets.items()
    ]


class SudokuHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        sudoku_name = args[0]
        sudoku = self._fetch_sudoku(sudoku_name)
        self.write(json.dumps({
            'sudoku_name': sudoku.sudoku_name,
            'field': sudoku.field
        }))

    @staticmethod
    def _fetch_sudoku(sudoku_name):
        session = db.open_db_session(expire_on_commit=False)
        sudoku = session.query(db.Sudoku).filter(db.Sudoku.sudoku_name == sudoku_name)
        sudoku = sudoku.first() or db.Sudoku.new(30, save_to_db=False, session=session)
        sudoku.sudoku_name = sudoku_name
        db.Sudoku.save(sudoku, session)
        session.close()
        return sudoku


class SudokuSocket:
    def __init__(self):
        self.sudoku_name = ''
        self.client_name = ''


class SocketHandler(tornado.websocket.WebSocketHandler, SudokuSocket):
    """
        WebSocket protocol handler for sudoku app.
        Possible messages:
            init <sudoku_name>
            set <sudoku_name> <row> <column> <value> <clientname>
            select <sudoku_name> <row> <column> <old_row> <old_column> <clientname>
            clientname <user_name>
            quit <clientname>
            online <users_online>
            win
    """
    def check_origin(self, origin):
        return True

    def open(self, *args, **kwargs):
        if self not in socket_heap:
            socket_heap.append(self)
        name = ''.join(choice(digits) for _ in range(5))
        self.client_name = name
        self.write_message('clientname {}'.format(name))

    @tornado.gen.coroutine
    def on_message(self, message):
        if message.startswith('init'):
            self._init_socket(message)
            users_online = len(sockets[self.sudoku_name])
            self.send_message_to_others(self.sudoku_name, 'online {}'.format(users_online))
            self.write_message('online {}'.format(users_online))
        elif message.startswith('select'):
            tokens = message.split()
            self.send_message_to_others(self.sudoku_name, message)
        elif message.startswith('set'):
            tokens = message.split()
            sudoku_field, next_name = self._update_sudoku_in_database(tokens)
            self.send_message_to_others(tokens[1], message)
            self.send_win_signal(sudoku_field, next_name)
        elif message.startswith('ping') and settings.DEBUG:
            print('Ping from {}'.format(self.client_name))

    def _init_socket(self, message):
        tokens = message.split()
        sudoku_name = tokens[1]
        self.sudoku_name = sudoku_name
        sockets[sudoku_name].append(self)
        socket_heap.remove(self)

    # @tornado.gen.coroutine
    def _update_sudoku_in_database(self, tokens):
        row = int(tokens[2])
        col = int(tokens[3])
        value = int(tokens[4])
        return db.Sudoku.update(self.sudoku_name, row, col, value)

    def send_message_to_others(self, sudoku_name, message):
        for socket in sockets[sudoku_name]:
            if socket is not self:
                socket.send_message_to_client(message)

    def send_message_to_client(self, message):
        self.write_message(message)

    @tornado.gen.coroutine
    def on_close(self):
        self.send_message_to_others(self.sudoku_name, 'quit {}'.format(self.client_name))
        for sockets_ in sockets.values():
            if self in sockets_:
                sockets_.remove(self)
                break
        self.clean_up_socket_list()

    @staticmethod
    def clean_up_socket_list():
        keys_to_be_deleted = []
        for sudoku, socket_list in sockets.items():
            if len(socket_list) == 0:
                keys_to_be_deleted.append(sudoku)
        for key in keys_to_be_deleted:
            del sockets[key]

    def send_win_signal(self, sudoku_field, next_sudoku_name):
        field = [cell['val'] for cell in sudoku_field]
        field = tuple(utils.chunks(field, 9))
        if sudoku.sudoku_solved(field):
            print(next_sudoku_name)
            self._fetch_next_sudoku(next_sudoku_name)
            self.send_message_to_others(self.sudoku_name, 'win')
            self.write_message('win')

    @staticmethod
    def _fetch_next_sudoku(next_sudoku_name):
        session = db.open_db_session()
        sudoku_ = session.query(db.Sudoku).filter(db.Sudoku.sudoku_name == next_sudoku_name).first()
        sudoku_ = sudoku_ or db.Sudoku.new(settings.SUDOKU_GRID_NUMBERS, save_to_db=False, session=session)
        sudoku_.sudoku_name = next_sudoku_name
        db.Sudoku.save(sudoku_, session)
        session.close()


