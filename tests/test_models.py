# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
import random
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # ADD YOUR TEST CASES HERE
    #
    def test_read_product(self):
        """It should read a product from the database with a given product id"""
        # create a mock product and add to db
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        print(f'product created: {str(product)}')

        # get the product we just added
        fetched_product = Product.find(product.id)
        self.assertEqual(fetched_product.id, product.id)
        self.assertEqual(fetched_product.name, product.name)
        self.assertEqual(fetched_product.description, product.description)
        self.assertEqual(fetched_product.price, product.price)

    def test_update_product(self):
        """It should update changes to a product in the database"""
        # create a mock product and add to db
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        print(f'product created: {product}; description: {product.description}')

        # update the product data
        new_description = "test description"
        original_id = product.id
        product.description = new_description
        print(f'new product: {product}; description: {product.description}')
        product.update()
        self.assertEqual(original_id, product.id)
        self.assertEqual(new_description, product.description)

        # fetch all items (there should only be one)
        products = Product.all()
        self.assertEqual(len(products), 1)

        # assert the first item matches the updated product
        self.assertEqual(products[0].id, original_id)
        self.assertEqual(products[0].description, new_description)

    def test_update_product_empty_id(self):
        """it should raise an exception if attempting to update a product without providing an id"""
        # create a mock product, remove its id
        product = ProductFactory()
        product.id = None

        # try to update the product, it should raise a DataValidationError
        self.assertRaises(DataValidationError, product.update)

    def test_delete_product(self):
        """It should remove an existing product by referenced id"""
        # create a mock product and add to db
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        print(f'product created: {product}')

        # get all products, there should only be 1
        products = Product.all()
        self.assertEqual(len(products), 1)

        # remove the product
        product.delete()
        products = Product.all()
        self.assertEqual(len(products), 0)

    def test_list_all_products(self):
        """it should get all products in the database"""
        # initial condition: no products in database
        products = Product.all()
        self.assertEqual(len(products), 0)

        # create 5 products
        for _ in range(5):
            new_product = ProductFactory()
            new_product.id = None
            new_product.create()

        # we should now have 5 products in the database
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_get_product_by_name(self):
        """it should get a product by the product's name"""
        # create 5 products
        for _ in range(5):
            new_product = ProductFactory()
            new_product.id = None
            new_product.create()

        # get all products (so we can reference them to get their names)
        products = Product.all()
        index = random.randint(0, 4)  # picking a random product to reference
        product_name = products[index].name

        # count how many products have name=product_name
        count = len([product for product in products if product.name == product_name])

        # get products by name
        found_products = Product.find_by_name(product_name)
        self.assertEqual(found_products.count(), count)
        for prod in found_products:
            self.assertEqual(prod.name, product_name)

    def test_get_product_by_availability(self):
        """it should filter products by availability"""
        # create 10 products
        for _ in range(10):
            new_product = ProductFactory()
            new_product.id = None
            new_product.create()

        # get all products
        products = Product.all()
        index = random.randint(0, 9)  # picking a random product to reference
        availability = products[index].available

        # count how many products have matching availability
        count = len([product for product in products if product.available == availability])

        # filter and assert
        found_products = Product.find_by_availability(availability)
        self.assertEqual(found_products.count(), count)
        for prod in found_products:
            self.assertEqual(prod.available, availability)

    def test_get_by_product_category(self):
        """it should filter products by category"""
        # create 10 products
        for _ in range(10):
            new_product = ProductFactory()
            new_product.id = None
            new_product.create()

        # get all products
        products = Product.all()
        index = random.randint(0, 9)  # picking a random product to reference
        category = products[index].category

        # count how many products have matching availability
        count = len([product for product in products if product.category == category])

        # filter and assert
        found_products = Product.find_by_category(category)
        self.assertEqual(found_products.count(), count)
        for prod in found_products:
            self.assertEqual(prod.category, category)

    def test_get_by_price(self):
        """it should filter products by price"""
        # create 10 products
        for _ in range(10):
            new_product = ProductFactory()
            new_product.id = None
            new_product.create()

        # get all products
        products = Product.all()
        index = random.randint(0, 9)  # picking a random product to reference
        price = products[index].price

        # count how many products have matching availability
        count = len([product for product in products if product.price == price])

        # filter and assert
        found_products = Product.find_by_price(str(price))  # casting to string for additional code coverage
        self.assertEqual(found_products.count(), count)
        for prod in found_products:
            self.assertEqual(prod.price, price)
