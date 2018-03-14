CREATE TABLE merchant (
  merchant_id serial PRIMARY KEY
, merchant    text NOT NULL
);

CREATE TABLE customer (
  customer_id  serial PRIMARY KEY
, customer     text NOT NULL
);

CREATE TABLE merchant_customer (
  merchant_id    int REFERENCES merchant (merchant_id) ON UPDATE CASCADE ON DELETE CASCADE
, customer_id int REFERENCES customer (customer_id) ON UPDATE CASCADE
, amount     numeric NOT NULL DEFAULT 1
, CONSTRAINT merchant_customer_pkey PRIMARY KEY (merchant_id, customer_id)
);
