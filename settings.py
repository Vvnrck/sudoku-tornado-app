import os
import sys

DEBUG = True
ENVIRONMENT = 'heroku' if os.environ.get('DATABASE_URL') is not None else 'local'

BASE_DIR = os.path.dirname(__file__)
TEMPLATE_DIR = os.path.join(BASE_DIR, 'server/templates')
STATIC_URL = os.path.join(BASE_DIR, 'static')

SUDOKU_NAME_LEN = 5
SUDOKU_GRID_NUMBERS = int(os.environ.get('SUDOKU_GRID_NUMBERS', 35))

if ENVIRONMENT == 'heroku':
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    SERVER_PORT = os.environ['PORT']
    URL = 'trviad-sudoku.herokuapp.com'
elif ENVIRONMENT == 'local':
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:123456@localhost:5432/sudoku_tornado'
    SERVER_PORT = 8888
    URL = 'localhost:{}'.format(SERVER_PORT)
