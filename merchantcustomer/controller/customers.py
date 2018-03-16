from tornado.escape import json_decode
from tornado import gen

from .base import BaseHandler, MyAppException
from helpers import DecimalEncoder

from decimal import Decimal as D
import json


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
        data = json_decode(self.request.body)
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
        data = json_decode(self.request.body)
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
