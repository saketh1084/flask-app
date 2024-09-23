from flask import Flask, render_template, request, redirect, jsonify, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId
from bson.json_util import dumps  # For converting MongoDB cursor to JSON

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['Users']  # Connect to the 'Users' database
data_collection = db['user']  # Use the 'user' collection

# Home route
@app.route('/')
def home():
    return render_template('home.html')

# About route
@app.route('/about')
def about():
    return render_template('about.html')

# API status route
@app.route('/api/status')
def status():
    return jsonify({"status": "active"})

# Greet route
@app.route('/greet')
def greet():
    name = request.args.get('name', 'Guest')
    return f"Hello, {name}!"

# Contact route (GET and POST handling)
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        return redirect(url_for('thanks', name=name))
    return render_template('contact.html')

# Thank you route after form submission
@app.route('/thanks')
def thanks():
    name = request.args.get('name', 'Guest')
    return f"Thank you for your message, {name}!"

# POST /add - Add a new user to the database
@app.route('/add', methods=['POST'])
def add_user():
    _json = request.json
    _name = _json.get('name')
    _email = _json.get('email')

    if _name and _email:
        # Insert the new user into the 'user' collection
        data_collection.insert_one({'name': _name, 'email': _email})

        return jsonify("User added successfully"), 200
    else:
        return not_found()  # Handle missing name or email

# GET /users - Retrieve all users
@app.route('/users', methods=['GET'])
def get_users():
    users = data_collection.find()
    resp = dumps(users)
    return resp

# GET /user/<id> - Retrieve user by ID
@app.route('/user/<id>', methods=['GET'])
def get_user_by_id(id):
    try:
        user = data_collection.find_one({'_id': ObjectId(id)})

        if user:
            resp = dumps(user)
            return resp, 200  # Return user data if found
        else:
            return jsonify({"status": 404, "message": "User not found"}), 404

    except InvalidId:
        return jsonify({"status": 404, "message": "Invalid ObjectId format"}), 404

# DELETE /delete/<id> - Delete user by ID
@app.route('/delete/<id>', methods=['DELETE'])
def delete_user(id):
    try:
        result = data_collection.delete_one({'_id': ObjectId(id)})

        if result.deleted_count > 0:
            return jsonify("User deleted successfully"), 200
        else:
            return jsonify({"status": 404, "message": "User not found"}), 404

    except InvalidId:
        return jsonify({"status": 404, "message": "Invalid ObjectId format"}), 404

# PUT /update/<id> - Update user by ID
@app.route('/update/<id>', methods=['PUT'])
def update_user(id):
    try:
        _json = request.json
        _name = _json.get('name')
        _email = _json.get('email')

        # Create a dictionary for the update
        update_data = {}
        if _name:
            update_data['name'] = _name
        if _email:
            update_data['email'] = _email

        # Update the user in the database
        result = data_collection.update_one({'_id': ObjectId(id)}, {'$set': update_data})

        if result.modified_count > 0:
            return jsonify("User updated successfully"), 200
        else:
            return jsonify({"status": 404, "message": "User not found or no change made"}), 404

    except InvalidId:
        return jsonify({"status": 404, "message": "Invalid ObjectId format"}), 404


# Error handler for 404
@app.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Not Found: ' + request.url
    }
    resp = jsonify(message)
    resp.status_code = 404
    return resp

if __name__ == "__main__":
    app.secret_key = 'your_secret_key'  
    app.run(debug=True)
