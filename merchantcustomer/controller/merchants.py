from .base import BaseHandler, MyAppException
from tornado.escape import json_decode
from tornado import gen


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
        data = json_decode(self.request.body)
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
