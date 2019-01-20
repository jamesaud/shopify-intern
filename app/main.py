import copy
from flask import Flask, request
from flask_restplus import Resource, Api, fields, inputs, reqparse, marshal
from flask_pymongo import PyMongo
from bson import json_util
from datetime import datetime
import json
import uuid
import os
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


api = Api(app, 
          title='Shopify Internship Application',
          version='1.0',
          description='flask rest api concerning an online marketplace')


# Environment Variables
PRODUCTION = os.environ.get("PRODUCTION") == 'True'   # Production should be set to "true" if the env variable is set
PORT = int(os.environ.get('PORT', 80))                # 80 by default for local development

# Configuratiton
app.config["MONGO_URI"] = os.environ['MONGODB_URI']
mongo = PyMongo(app)
app.config['RESTPLUS_MASK_SWAGGER'] = False


def create_id():   
    return str(uuid.uuid4())


# Models and validation for input/output fields
product_input_fields = api.model('ProductInput', {
    'title': fields.String(required=True),
    'price': fields.Float(required=True, min=0),
    'inventory_count': fields.Integer(required=True, min=0)
})

product_fields = api.inherit('Product', product_input_fields, {
    'id': fields.String(required=True),
})

pagination = api.model('A page of results', {
    'page': fields.Integer(description='Number of this page of results'),
    'pages': fields.Integer(description='Total number of pages of results'),
})

page_of_products = api.inherit('Page of products', pagination, {
    'items': fields.List(fields.Nested(product_fields))
})

cart_fields = api.model('Cart', {
    'id': fields.String(required=True),
    'products': fields.List(fields.Nested(product_fields)),
    'total_price': fields.Float(required=True, default=0)
})

# General return field for an id
id_field = api.model('ID', {
    'id': fields.String(required=True),
})

product_id_field = api.model('ProductID', {
    'product_id': fields.String(required=True), 
})  


# Define Resources

class Products(Resource):
    PER_PAGE = 10

    parser = reqparse.RequestParser()
    parser.add_argument('min_quantity', type=int, help='Require products with at least this quantity', default=0, required=False)
    parser.add_argument('page', type=inputs.natural,  help='Select a new page (starting from 0)', required=False, default=0)

    @api.doc(description="Returns details of all products")
    @api.expect(parser, validate=True)
    @api.marshal_with(page_of_products)
    def get(self):
        args = self.parser.parse_args()
        min_quantity = args.min_quantity - 1
        page = args.page

        # Require min quantity
        products_db = mongo.db.products.find({"inventory_count": {"$gt": min_quantity}}, {'_id': False})

        # Select correct page
        products_db = products_db.skip(page * self.PER_PAGE).limit(self.PER_PAGE)

        products = list(products_db)
        products = json.loads(json_util.dumps(products))
        pages = products_db.count() // self.PER_PAGE
        response = {
            'page': min(page, pages),
            'pages': pages,
            'items': products
        }
        return response


    @api.doc(description="Creates a new product")
    @api.expect(product_input_fields, validate=True)
    @api.response(201, 'Product created', id_field)
    def post(self):
        data = request.get_json()

        product_id = create_id()
        product = {
             "title": data["title"],
             "price": data["price"],
             "inventory_count": data["inventory_count"],
             "id": product_id
        }
        mongo.db.products.insert_one(product)
        product = mongo.db.products.find_one({"id": product_id}, {'_id': False, 'id': True})
    
        return json.loads(json_util.dumps(product)), 201

class Product(Resource):
    @api.doc(description="Gets details about a particular product")
    @api.marshal_with(product_fields)
    def get(self, product_id):
        product = mongo.db.products.find_one({"id": product_id}, {'_id': False})
        return json.loads(json_util.dumps(product))

class PurchaseProduct(Resource):
    @api.doc(description="Subtracts 1 from the current item count of a particular product")
    @api.marshal_with(product_fields)
    @api.response(200, 'Success', product_fields)
    @api.response(403, 'Product inventory count is at 0')
    @api.response(422, 'Product does not exist')
    def patch(self, product_id):
        product = mongo.db.products.find_one({"id": product_id})
        if product is None:
            api.abort(422, 'Product does not exist')

        success = self.decrement_inventory_count(product_id)
        if not success:
            api.abort(403, 'Inventory count already at 0')

        product = mongo.db.products.find_one({"id": product_id})
        return json.loads(json_util.dumps(product))

    @staticmethod
    def decrement_inventory_count(product_id):
        """ Decreases inventory count by 1 for a given product """
        product = mongo.db.products.find_one({"id": product_id})

        if product['inventory_count'] == 0:
            return False

        return mongo.db.products.find_one_and_update({"id": product_id}, {'$inc': {'inventory_count': -1}})

class Carts(Resource):
    @api.doc(description="Creates a new cart")
    @api.response(201, 'Cart created', id_field)
    def post(self):
        cart_id = create_id()
        cart = {
             "id": cart_id,
             "products": []
        }
        mongo.db.carts.insert_one(cart)
        cart = mongo.db.carts.find_one({"id": cart_id}, {'_id': False, 'id': True})
        return json.loads(json_util.dumps(cart)), 201

class Cart(Resource):
    @staticmethod
    def products_info(product_ids):
        """ Given a list of product_ids, pull the info from the DB"""
        # Pull item information to display to user 
        products = mongo.db.products.find({"id" : {"$in" : product_ids}}, {'_id': False})
        return list(products)

    @staticmethod
    def display_cart(cart):
        """ Returns cart as dictionary to display to the user """
        cart['products'] = Cart.products_info(cart['products'])
        cart['total_price'] = sum(product['price'] for product in cart['products'])
        return cart 

    @api.doc(description="Gets details about a particular product")
    @api.marshal_with(cart_fields)
    def get(self, cart_id):
        cart = mongo.db.carts.find_one({"id": cart_id}, {'_id': False})
        cart = self.display_cart(cart)
        return json.loads(json_util.dumps(cart))

    @api.doc(description="Adds item to cart")
    @api.expect(product_id_field)
    @api.response(201, 'Successfully added product to cart', cart_fields)
    @api.response(422, 'Product does not exist')
    def post(self, cart_id):
        data = request.get_json()
        product_id = data['product_id']

        if mongo.db.products.find_one({"id": product_id}) is None:
            api.abort(422, 'Product does not exist') 

        cart = mongo.db.carts.find_one({"id": cart_id}, {'_id': False})

        new_products = cart['products']
        if product_id not in new_products:
            new_products.append(product_id)
        
        mongo.db.carts.find_one_and_update({"id": cart_id}, 
                                 {"$set": {"products": new_products}})

        cart = mongo.db.carts.find_one({"id": cart_id}, {'_id': False})

        # Pull item information to display to user 
        cart = self.display_cart(cart)
        output = json.loads(json_util.dumps(cart))
        return marshal(output, cart_fields), 201

class CartCheckout(Resource):
    @api.doc(description='"Completes" the cart. Any products that are not able to be purchased will remain in the cart (this could happen if a product has 0 inventory count). ')
    @api.marshal_with(cart_fields)
    @api.response(200, 'Successfully completed cart', cart_fields)
    @api.response(422, 'Cart does not exist')
    def patch(self, cart_id):
        cart = mongo.db.carts.find_one({"id": cart_id})
        if cart is None:
            api.abort(422, 'Cart does not exist') 

        products = cart['products']
        for product_id in products:
            success = PurchaseProduct.decrement_inventory_count(product_id)
            if success:
                products.remove(product_id)

        # Set to empty cart after checking out, unless an item failed to checkout
        mongo.db.carts.find_one_and_update({"id": cart_id}, 
                                 {"$set": {"products": products}})

        cart = mongo.db.carts.find_one({"id": cart_id}, {"_id": False})
        cart = Cart.display_cart(cart)
        return json.loads(json_util.dumps(cart))
        
# Add to API        
api.add_resource(Products, '/products')
api.add_resource(Product, '/products/<string:product_id>')
api.add_resource(PurchaseProduct, '/products/<string:product_id>/purchase')
api.add_resource(Cart, '/carts/<string:cart_id>')
api.add_resource(CartCheckout, '/carts/<string:cart_id>/complete')
api.add_resource(Carts, '/carts')


if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host='0.0.0.0', debug=not PRODUCTION, port=PORT)