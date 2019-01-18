import copy
from flask import Flask, request
from flask_restplus import Resource, Api, fields, inputs, reqparse
from flask_pymongo import PyMongo
from bson import json_util
from datetime import datetime
import json
import uuid
import os


app = Flask(__name__)
api = Api(app, 
          title='Shopify Internship Application',
          version='1.0',
          description='flask rest api concerning an online marketplace')



PRODUCTION = bool(os.environ.get("PRODUCTION"))   # Production should be set to "true" if the env variable is set

# Production should be passed in the env var
# Otherwise configured for Docker in development
app.config["MONGO_URI"] = os.environ.get('MONGODB_URI') + '/my-database'     
mongo = PyMongo(app)
app.config['RESTPLUS_MASK_SWAGGER'] = False


def create_id():
    return str(uuid.uuid4())


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
    @api.response(201, 'Product created', product_fields)
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
        product = mongo.db.products.find_one({"id": product_id}, {'_id': False})
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
    def patch(self, product_id):
        product = mongo.db.products.find_one({"id": product_id})
        if product['inventory_count'] == 0:
            api.abort(403, 'Inventory count already at 0')

        product = mongo.db.products.find_one_and_update({"id": product_id}, {'$inc': {'inventory_count': -1}})
        product = mongo.db.products.find_one({"id": product_id})
        return json.loads(json_util.dumps(product))


class Cart(Resource):
    pass


api.add_resource(Products, '/products')
api.add_resource(Product, '/products/<string:product_id>')
api.add_resource(PurchaseProduct, '/products/<string:product_id>/purchase')


if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host='0.0.0.0', debug=not PRODUCTION, port=80)