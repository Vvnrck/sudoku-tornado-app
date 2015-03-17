import tornado.ioloop
import tornado.web
import server.views as views
import server.api as api
import settings


def make_app():
    return tornado.web.Application(make_urls(), **make_settings())


def make_urls():
    return [
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": settings.STATIC_URL}),
        (r'/', views.MainHandler),
        (r'/sudoku/(\w+)', api.SudokuHandler),
        (r'/ws', api.SocketHandler),
        (r'/(\w+)', views.SudokuHandler),
    ]


def make_settings():
    return {
        'debug': True,
        'static_path': settings.STATIC_URL
    }


if __name__ == "__main__":
    application = make_app()
    application.listen(settings.SERVER_PORT)
    tornado.ioloop.IOLoop.instance().start()