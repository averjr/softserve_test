from tornado.options import define, options


import tornado.ioloop
import tornado.web

import momoko
import os

from controller.base import BaseHandler
from controller.customers import CustomersHandler
from controller.customers import AccountsHandler
from controller.merchants import MerchantsHandler


dsn_bdname = os.getenv('POSTGRES_DB')
dsn_user = os.getenv('POSTGRES_USER')
dsn_password = os.getenv('POSTGRES_PASSWORD')
dsn_host = os.getenv('DB_HOST')

dsn = 'dbname={} user={} password={} host={}'
dsn = dsn.format(dsn_bdname, dsn_bdname, dsn_password, dsn_host)
define("postgres_dsn", default=dsn)


def main(ioloop, dsn, debug=False):
    app = tornado.web.Application([
            (r'/customers/?', CustomersHandler),
            (r'/customers/(?P<customer_id>[0-9]+)/?', CustomersHandler),
            (r'/customers/(?P<customer_id>[0-9]+)/replenish/?', AccountsHandler),
            (r'/customers/(?P<customer_id>[0-9]+)/withdrow/?', AccountsHandler),
            (r'/merchant/?', MerchantsHandler),
            (r'/merchant/(?P<merchant_id>[0-9]+)/?', MerchantsHandler),
        ],
        default_handler_class=BaseHandler,
        debug=debug)

    app.db = momoko.Pool(dsn=dsn, size=1, ioloop=ioloop)
    app.db.connect()
    return app


if __name__ == "__main__":
    tornado.options.parse_command_line()

    ioloop = tornado.ioloop.IOLoop.instance()
    application = main(ioloop, options.postgres_dsn, debug=True)

    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)

    ioloop.start()
