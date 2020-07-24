import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


db_drop_and_create_all()

## ROUTES
# get drinks from the database
@app.route('/drinks', methods=['GET'])
def get_drinks():
    try:

        #get the required drink information that we want to display
        drinks_list = Drink.query.all()
        
        # abort 404 if we cannot get any results from the database
        if len(drinks_list) == 0:
            abort(404)

        drinks = [drink.short() for drink in drinks_list]
        return jsonify({
            'success': True,
            'drinks': drinks
        }), 200
    except:
        abort(404)


# get drinks detail from the database
# it require "get:drinks-detail" permission for the user to access these information
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(jwt):
    try:

        #get the required drink information that we want to display 
        drinks_list = Drink.query.all()

        # abort 404 if we cannot get any results from the database
        if len(drinks_list) == 0:
            abort(404)

        drinks = [drink.long() for drink in drinks_list]

        return jsonify({
            'success': True,
            'drinks': drinks
        }), 200
        
    except:
        abort(404)



# add a new drink to the database
# it require "post:drinks" permission for the user to add a drink
@app.route("/drinks", methods=['POST'])
@requires_auth("post:drinks")
def new_drink(jwt):
    try:
        requested_body = request.get_json()
        title = requested_body['title']
        recipe = requested_body['recipe']

        #create a new drink object and insert it to the database 
        drink = Drink(title=title, recipe=json.dumps(recipe))
        drink.insert()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        }), 200

    except:
        abort(422)
        


# edit a specific drink information
# it require "patch:drinks" permission for the user to update these information
@app.route("/drinks/<drink_id>", methods=['PATCH'])
@requires_auth("patch:drinks")
def edit_drink(jwt, drink_id):
    
    #return the required drink object that we want to update using drink_id
    drink = Drink.query.get(drink_id)
    #abort 404 if we cannot find the drink object we want to modify 
    if not drink:
        abort(404)

    try:
        requested_body = request.get_json()
        
        # replace the new value of "title" and "recipe" with the old one
        if 'title' in requested_body:
            drink.title = requested_body['title']

        if 'recipe' in requested_body:
            drink.recipe = json.dumps(requested_body['recipe'])
        
        # after that we commit the changes in the database
        drink.update()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        }), 200

    except:
        abort(422)



# delete a specific drink from the database
# it require "delete:drinks" permission for the user to delete a drink
@app.route('/drinks/<drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, drink_id):

    #return the required drink object that we want to delete it using drink_id
    drink = Drink.query.get(drink_id)
    #abort 404 if we cannot find the drink object we want to delete 
    if not drink:
        abort(404)

    try:
        # delete it form the database and commit
        drink.delete()

        return jsonify({
            'success': True, 'delete': drink_id
            }), 200

    except:
        abort(422)
    


## Error Handling
'''
Example error handling for unprocessable entity
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 422,
                    "message": "unprocessable"
                    }), 422


@app.errorhandler(404)
def not_found(error):
    return jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404


@app.errorhandler(AuthError)
def AuthError_handler(error):
    return jsonify(error.error), error.status_code
