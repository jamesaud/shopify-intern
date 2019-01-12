import copy
from flask import Flask, request
from flask_restplus import Resource, Api, fields, inputs, reqparse
from flask_pymongo import PyMongo

from bson import json_util
from datetime import datetime
import json
import uuid
import math

app = Flask(__name__)
api = Api(app)
app.config["MONGO_URI"] = "mongodb://mongo:27017/my-database"
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
    parser.add_argument('page', type=inputs.natural,  help='Select a new page starting from 0', required=False, default=0)

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
    @api.response(201, 'Product created')
    def post(self):
        json = request.get_json()

        product_id = create_id()
        product = {
             "title": json["title"],
             "price": json["price"],
             "inventory_count": json["inventory_count"],
             "id": str(product_id)
        }
        _product = dict(product)
        mongo.db.products.insert_one(product)
        return {'id': str(product_id)}, 201


class Product(Resource):
    @api.doc(description="Gets details about a particular product")
    @api.marshal_with(product_fields, envelope='resource')
    def get(self, product_id):
        user = mongo.db.products.find_one({"id": product_id}, {'_id': False})
        return json.loads(json_util.dumps(user))
        

api.add_resource(Products, '/products')
api.add_resource(Product, '/products/<string:product_id>')


if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host='0.0.0.0', debug=True, port=80)