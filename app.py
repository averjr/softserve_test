from tornado.options import define, options
from tornado import gen

import tornado.ioloop
import tornado.web

import momoko
import json
import traceback

from decimal import Decimal as D


dsn = 'dbname={} user={} password={} host={}'
dsn = dsn.format('docker', 'docker', 'docker', 'db')
define("postgres_dsn", default=dsn)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, D):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


class MyAppException(tornado.web.HTTPError):
    pass


class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):

        return self.application.db

    def write_error(self, status_code, **kwargs):

        self.set_header('Content-Type', 'application/json')
        if self.settings.get("serve_traceback") and "exc_info" in kwargs:
            # in debug mode, try to send a traceback
            lines = []
            for line in traceback.format_exception(*kwargs["exc_info"]):
                lines.append(line)
            self.set_status(status_code)
            self.finish(json.dumps({
                "status": "error",
                'message': self._reason,
            }))
        else:
            self.set_status(status_code)
            self.finish(json.dumps({
                "status": "error",
                'message': self._reason,
            }))


class MainHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        cursor = yield self.db.execute("SELECT * FROM customer;")
        self.write("Results: %s" % cursor.fetchall())
        self.finish()


class CustomersHandler(BaseHandler):
    @gen.coroutine
    def post(self):
        customer = self.get_argument("customer")
        cursor = yield self.db.execute(
            "INSERT INTO customer (customer)\n"
            "VALUES (%s) RETURNING *;", (customer,))
        row = cursor.fetchone()
        obj_customer_description = ['customer_id', 'customer']
        obj = dict(zip(obj_customer_description, row))
        self.set_status(201)
        self.write(obj)
        self.finish()

    @gen.coroutine
    def get(self, customer_id):
        cursor = yield self.db.execute(
            "SELECT * FROM customer WHERE customer_id = %s;", (customer_id,))
        row = cursor.fetchone()
        obj_customer_description = ['customer_id', 'customer']
        obj = dict(zip(obj_customer_description, row))

        self.set_status(200)
        self.write(obj)
        self.finish()

    @gen.coroutine
    def put(self, customer_id):
        data = tornado.escape.json_decode(self.request.body)
        customer = data['customer']
        cursor = yield self.db.execute(
            "UPDATE customer\n"
            "SET customer = %s\n"
            "WHERE customer_id = %s RETURNING *;", (customer, customer_id))
        row = cursor.fetchone()
        if not row:
            raise MyAppException(
                reason='No customer with such id.',
                status_code=400
            )

        obj_customer_description = ['customer_id', 'customer']
        obj = dict(zip(obj_customer_description, row))

        self.set_status(201)
        self.write(obj)
        self.finish()

    def delete(self, customer_id):
        self.db.execute(
            "DELETE FROM customer WHERE customer_id = %s;", (customer_id,))
        self.set_status(204)
        # TODO: add handling if no customer with such id


class MerchantsHandler(BaseHandler):
    @gen.coroutine
    def post(self):
        merchant = self.get_argument("merchant")
        cursor = yield self.db.execute(
            "INSERT INTO merchant (merchant)\n"
            "VALUES (%s) RETURNING *;", (merchant,))
        row = cursor.fetchone()
        obj_customer_description = ['merchant_id', 'merchant']
        obj = dict(zip(obj_customer_description, row))
        self.set_status(201)
        self.write(obj)
        self.finish()

    @gen.coroutine
    def get(self, merchant_id):
        cursor = yield self.db.execute(
            "SELECT * FROM merchant WHERE merchant_id = %s;", (merchant_id,))
        row = cursor.fetchone()
        obj_merchant_description = ['merchant_id', 'merchant']
        obj = dict(zip(obj_merchant_description, row))

        self.set_status(200)
        self.write(obj)
        self.finish()

    @gen.coroutine
    def put(self, merchant_id):
        data = tornado.escape.json_decode(self.request.body)
        merchant = data['merchant']
        cursor = yield self.db.execute(
            "UPDATE merchant\n"
            "SET merchant = %s\n"
            "WHERE merchant_id = %s RETURNING *;", (merchant, merchant_id))
        row = cursor.fetchone()
        if not row:
            raise MyAppException(
                reason='No merchant with such id.',
                status_code=400
            )

        obj_merchant_description = ['merchant_id', 'merchant']
        obj = dict(zip(obj_merchant_description, row))

        self.set_status(201)
        self.write(obj)
        self.finish()

    def delete(self, merchant_id):
        self.db.execute(
            "DELETE FROM merchant WHERE merchant_id = %s;", (merchant_id,))
        self.set_status(204)
        # TODO: add handling if no customer with such id


class AccountsHandler(BaseHandler):
    @gen.coroutine
    def post(self, customer_id):
        merchant_id = self.get_argument("merchant_id")
        amount = self.get_argument("amount")

        cursor = yield self.db.execute(
            "SELECT * FROM merchant_customer\n"
            "WHERE merchant_id = %s and customer_id = %s;",
            (merchant_id, customer_id))
        row = cursor.fetchone()
        if not row:
            # TODO: Handle if wrong merchant_id and/or customer_id
            cursor = yield self.db.execute(
                "INSERT INTO merchant_customer\n"
                "(merchant_id, customer_id, amount)\n"
                "VALUES (%s, %s, %s) RETURNING *;",
                (merchant_id, customer_id, amount))
            row = cursor.fetchone()
        else:
            cursor = yield self.db.execute(
                "UPDATE merchant_customer\n"
                "SET amount = %s\n"
                "WHERE merchant_id = %s and customer_id = %s RETURNING *;",
                (amount, merchant_id, customer_id, ))
            row = cursor.fetchone()

        # TODO: Return customer object with merchants accounts
        obj_obj_merchant_customer_description = [
            'merchant_id',
            'customer_id',
            'amount'
        ]
        obj = dict(zip(obj_obj_merchant_customer_description, row))
        self.set_status(200)
        self.write(json.dumps(obj, cls=DecimalEncoder))
        self.finish()

    @gen.coroutine
    def put(self, customer_id):
        data = tornado.escape.json_decode(self.request.body)
        merchant_id = data['merchant_id']
        withdrow = D(data['withdrow'])

        cursor = yield self.db.execute(
            "SELECT amount FROM merchant_customer\n"
            "WHERE merchant_id = %s and customer_id = %s;",
            (merchant_id, customer_id))

        curent_amount = cursor.fetchone()[0]
        if not curent_amount:
            raise MyAppException(
                reason='Wrong merchant_id or customer_id.',
                status_code=400)

        new_amount = curent_amount - withdrow
        if new_amount < 0:
            raise MyAppException(reason='Not enough money.', status_code=400)

        cursor = yield self.db.execute(
            "UPDATE merchant_customer\n"
            "SET amount = %s\n"
            "WHERE merchant_id = %s and customer_id = %s RETURNING *;",
            (new_amount, merchant_id, customer_id, ))
        row = cursor.fetchone()

        obj_obj_merchant_customer_description = [
            'merchant_id',
            'customer_id',
            'amount'
        ]
        obj = dict(zip(obj_obj_merchant_customer_description, row))

        self.set_status(200)
        self.write(json.dumps(obj, cls=DecimalEncoder))
        self.finish()


def main(ioloop, dsn, debug=True):
    app = tornado.web.Application([
            (r'/', MainHandler),
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
