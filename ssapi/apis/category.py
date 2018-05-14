from flask_praetorian import auth_required
from flask_restplus import Namespace, Resource, fields
from ssapi.db import Category

api = Namespace('categories', description='Category related operations')

category_marshal_model = api.model('Category', {
    'id': fields.String(required=True, description='The category id'),
    'name': fields.String(required=True, description='The category name'),
})


@api.route('/')
class CategoryListResource(Resource):
    @api.doc('list_categories')
    @api.marshal_list_with(category_marshal_model)
    @auth_required
    def get(self):
        return Category.query.all()
