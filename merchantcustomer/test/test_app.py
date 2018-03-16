from tornado.testing import AsyncHTTPTestCase, gen_test
from tornado.httputil import HTTPHeaders
import urllib.parse
import unittest
import momoko
import json
import os

import app

dsn_bdname = os.getenv('POSTGRES_DB')
dsn_user = os.getenv('POSTGRES_USER')
dsn_password = os.getenv('POSTGRES_PASSWORD')
dsn_host = os.getenv('DB_HOST')

dsn = 'dbname={} user={} password={} host={}'
dsn = dsn.format(dsn_bdname, dsn_bdname, dsn_password, dsn_host)

class BaseTest(AsyncHTTPTestCase):
    dsn = dsn

    @gen_test
    def set_up_10(self):
        self.conn = yield momoko.connect(self.dsn, ioloop=self.io_loop)

    def setUp(self):
        super(BaseTest, self).setUp()
        self.set_up_10()

    @gen_test
    def tear_down_10(self):
        # FIXME:
        yield self.conn.execute("TRUNCATE customer CASCADE;")
        yield self.conn.execute("TRUNCATE merchant CASCADE;")

    def tearDown(self):
        self.tear_down_10()
        super(BaseTest, self).tearDown()

    def get_app(self):
        return app.main(self.io_loop, self.dsn)

    @gen_test
    def create_customer(self, name):
        customer = name
        cursor = yield self.conn.execute(
            "INSERT INTO customer (customer)\n"
            "VALUES (%s) RETURNING customer_id;",
            (customer,))
        row = cursor.fetchone()
        return row[0]

    @gen_test
    def create_merchant(self, name):
        merchant = name
        cursor = yield self.conn.execute(
            "INSERT INTO merchant (merchant)\n"
            "VALUES (%s) RETURNING merchant_id;",
            (merchant,))
        row = cursor.fetchone()
        return row[0]

    @gen_test
    def create_account(self, merchant_id, customer_id, amount):
        cursor = yield self.conn.execute(
            "INSERT INTO merchant_customer (merchant_id, customer_id, amount)\n"
            "VALUES (%s, %s, %s) RETURNING *;", (merchant_id, customer_id, amount))

        row = cursor.fetchone()
        return row[2]

    def create_customer_with_merchant_account(self, amount):
        customer_name = 'test customer'
        customer_id = self.create_customer(customer_name)
        merchant_name = 'test merchant'
        merchant_id = self.create_merchant(merchant_name)

        amount = self.create_account(merchant_id, customer_id, amount)
        return customer_id, merchant_id, amount


class CustomerTest(BaseTest):
    def test_create_customers(self):
        """Test create customer"""
        data = {
            'customer': 'test name',
        }
        body = urllib.parse.urlencode(data)
        response = self.fetch('/customers/', method="POST", body=body)

        response_data = json.loads(response.body)
        self.assertEqual(response.code, 201)
        self.assertEqual(response_data['customer'], data['customer'])
        self.assertIn('customer_id', response_data)

    def test_read_customer(self):
        """Test read customer"""
        customer_name = 'test name'
        customer_id = self.create_customer(customer_name)

        response = self.fetch('/customers/{}'.format(customer_id), method="GET")
        response_data = json.loads(response.body)
        self.assertEqual(response.code, 200)
        self.assertEqual(response_data['customer'], customer_name)

    # TODO: implement this
    # def test_read_customer_with_merchants_amout(self):
    #     """Test customer returns with merchants and amout"""
    #     # self.assertEqual(
    #       response_data['customer']['accounts'][merchant_id],
    #       data['amount']
    #     )

    def test_update_customer(self):
        """Test update customer"""
        customer_name = 'test name'
        customer_id = self.create_customer(customer_name)
        data = {
            'customer': 'new name',
        }

        body = json.dumps(data)
        response = self.fetch(
             "/customers/{}".format(customer_id),
             method="PUT",
             body=body,
             allow_nonstandard_methods=True
        )

        response_data = json.loads(response.body)
        self.assertEqual(response.code, 201)
        self.assertEqual(response_data['customer'], data['customer'])
        self.assertIn('customer_id', response_data)

    def test_fail_update_customer(self):
        """Test fail update customer"""
        data = {
            'customer': 'new name',
        }
        body = json.dumps(data)

        # using 42 as fake customer id
        response = self.fetch(
             "/customers/{}".format(42),
             method="PUT",
             body=body,
             allow_nonstandard_methods=True
        )

        response_data = json.loads(response.body)
        self.assertEqual(response.code, 400)

    # TODO: Create test for delating customer with accounts
    def test_delete_customer(self):
        """Test delete customer"""
        customer_name = 'test name'
        customer_id = self.create_customer(customer_name)

        response = self.fetch(
             "/customers/{}".format(customer_id),
             method="DELETE",
             allow_nonstandard_methods=True
        )
        self.assertEqual(response.code, 204)


class AccountTest(BaseTest):
    # TODO: Add test for replenish with wrong data (e.g. not existing customer)
    def test_customer_account_replenish(self):
        """Test customer replenish account"""
        customer_name = 'test customer'
        customer_id = self.create_customer(customer_name)

        merchant_name = 'test merchant'
        merchant_id = self.create_merchant(merchant_name)

        data = {
            'merchant_id': merchant_id,
            'amount': 42
        }
        body = urllib.parse.urlencode(data)
        response = self.fetch(
            '/customers/{}/replenish'.format(customer_id),
            method="POST",
            body=body
        )

        response_data = json.loads(response.body)
        self.assertEqual(response.code, 200)
        self.assertEqual(response_data['merchant_id'], merchant_id)
        self.assertEqual(response_data['customer_id'], customer_id)
        self.assertEqual(response_data['amount'], data['amount'])
        # TODO: Change this to check response with user merchants and amouts

    def test_customer_account_replenish_existed(self):
        """Test existing customer replenish account"""
        customer_id, merchant_id, amount = self.create_customer_with_merchant_account(43.12)
        amount = float(amount)

        new_amount = amount + 42
        data = {
            'merchant_id': merchant_id,
            'amount': new_amount
        }
        body = urllib.parse.urlencode(data)
        response = self.fetch(
            '/customers/{}/replenish'.format(customer_id),
            method="POST",
            body=body
        )

        response_data = json.loads(response.body)
        self.assertEqual(response.code, 200)
        self.assertEqual(response_data['merchant_id'], merchant_id)
        self.assertEqual(response_data['customer_id'], customer_id)
        self.assertEqual(response_data['amount'], new_amount)
        # TODO: Change this to check response with user merchants and amouts

    def test_customer_account_withdrow(self):
        """Test customer withdrow"""
        customer_id, merchant_id, amount = self.create_customer_with_merchant_account(43.12)
        amount = float(amount)
        withdrow = 3.14
        new_amount = amount - withdrow

        data = {
            'merchant_id': merchant_id,
            'withdrow': withdrow
        }
        body = json.dumps(data)
        response = self.fetch(
            '/customers/{}/withdrow'.format(customer_id),
            method="PUT",
            body=body
        )

        response_data = json.loads(response.body)
        self.assertEqual(response.code, 200)
        self.assertEqual(response_data['amount'], new_amount)

    def test_fail_customer_account_withdrow(self):
        """Test fail customer withdrow"""
        # TODO: if no amount for this merchant
        customer_id, merchant_id, amount = self.create_customer_with_merchant_account(43.12)
        amount = float(amount)
        withdrow = 43.13
        new_amount = amount - withdrow

        data = {
            'merchant_id': merchant_id,
            'withdrow': withdrow
        }
        body = json.dumps(data)
        response = self.fetch(
            '/customers/{}/withdrow'.format(customer_id),
            method="PUT",
            body=body
        )

        response_data = json.loads(response.body)
        self.assertIsNot(response.code, 200)


class MerchantTest(BaseTest):
    def test_create_merchant(self):
        """Test create merchant"""
        data = {
            'merchant': 'test name',
        }
        body = urllib.parse.urlencode(data)
        response = self.fetch('/merchant/', method="POST", body=body)

        response_data = json.loads(response.body)
        self.assertEqual(response.code, 201)
        self.assertEqual(response_data['merchant'], data['merchant'])
        self.assertIn('merchant_id', response_data)

    def test_read_merchant(self):
        """Test read merchant"""
        merchant_name = 'test name'
        merchant_id = self.create_merchant(merchant_name)

        response = self.fetch('/merchant/{}'.format(merchant_id), method="GET")
        response_data = json.loads(response.body)
        self.assertEqual(response.code, 200)
        self.assertEqual(response_data['merchant'], merchant_name)

    def test_update_merchant(self):
        """Test update merchant"""
        merchant_name = 'test name'
        merchant_id = self.create_merchant(merchant_name)
        data = {
            'merchant': 'new name',
        }

        body = json.dumps(data)
        response = self.fetch(
             "/merchant/{}".format(merchant_id),
             method="PUT",
             body=body,
             allow_nonstandard_methods=True
        )

        response_data = json.loads(response.body)
        self.assertEqual(response.code, 201)
        self.assertEqual(response_data['merchant'], data['merchant'])
        self.assertIn('merchant_id', response_data)

    def test_delete_merchant(self):
        """Test delete merchant"""
        merchant_name = 'test name'
        merchant_id = self.create_customer(merchant_name)

        response = self.fetch(
             "/merchant/{}".format(merchant_id),
             method="DELETE",
             allow_nonstandard_methods=True
        )
        self.assertEqual(response.code, 204)

if __name__ == "__main__":
    unittest.main(verbosity=2)
