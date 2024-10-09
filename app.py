from flask import Flask, request, render_template, redirect, url_for, session
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")  # Use your MongoDB URI if hosted elsewhere
db = client['farmer_market_db']  # Database name
users_collection = db['users']  # Collection for users
products_collection = db['products']  # Collection for products

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    user_type = request.form['user_type']
    contact = request.form['contact']  # Contact details

    if users_collection.find_one({'username': username}):
        return 'Username already exists', 400

    # Insert new user into the database
    users_collection.insert_one({
        'username': username,
        'password': password,
        'type': user_type,
        'contact': contact  # Save contact details
    })
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user = users_collection.find_one({'username': username})
    if user and user['password'] == password:
        session['username'] = username
        session['user_type'] = user['type']
        return redirect(url_for('dashboard'))
    return 'Invalid credentials', 401

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        user_type = session['user_type']
        if user_type == 'seller':
            products = list(products_collection.find({'seller': session['username']}))
            return render_template('seller_dashboard.html', products=products, contact=session.get('contact'))
        elif user_type == 'customer':
            products = list(products_collection.find())
            return render_template('buyer_dashboard.html', products=products, contact=session.get('contact'))
    return redirect(url_for('index'))

@app.route('/add_product', methods=['POST'])
def add_product():
    if 'username' in session and session['user_type'] == 'seller':
        product = {
            'name': request.form['name'],
            'description': request.form['description'],
            'price': request.form['price'],
            'quantity': request.form['quantity'],
            'seller': session['username']
        }
        products_collection.insert_one(product)  # Save product to database
    return redirect(url_for('dashboard'))

@app.route('/edit_product/<product_name>', methods=['GET', 'POST'])
def edit_product(product_name):
    if 'username' not in session or session['user_type'] != 'seller':
        return redirect(url_for('index'))

    if request.method == 'POST':
        products_collection.update_one(
            {'name': product_name, 'seller': session['username']},
            {'$set': {
                'description': request.form['description'],
                'price': request.form['price'],
                'quantity': request.form['quantity']
            }}
        )
        return redirect(url_for('dashboard'))

    product = products_collection.find_one({'name': product_name, 'seller': session['username']})
    return render_template('edit_product.html', product=product)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_type', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
