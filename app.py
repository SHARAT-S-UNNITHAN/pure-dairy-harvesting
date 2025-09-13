from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_migrate import Migrate
from flask import send_from_directory, abort
import os

# Import extensions
from extensions import db, login_manager, bcrypt
from models import Role, User, Product, Order, OrderItem, Category

app = Flask(__name__)
app.config.from_object('config.Config')

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
bcrypt.init_app(app)
migrate = Migrate(app, db) 

# Setup login manager
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create upload directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'products'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'profiles'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'licenses'), exist_ok=True) # For farmer licenses

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Routes
@app.route('/')
def index():
    products = Product.query.filter_by(approved=True).all()
    categories = Category.query.all()
    return render_template('products.html', products=products, categories=categories)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            # --- NEW: CHECK IF FARMER IS APPROVED ---
            if user.role.name == 'farmer' and not user.is_approved:
                flash('Your farmer account is pending admin approval. You will be notified once approved.', 'warning')
                return redirect(url_for('login'))
            # --- END OF NEW CHECK ---
            
            session['user_id'] = user.id
            session['role'] = user.role.name
            session['user_name'] = user.name
            flash('Login successful!', 'success')
            if user.role.name == 'farmer':
                return redirect(url_for('farmer_dashboard'))
            elif user.role.name == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('customer_dashboard'))
        flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        role_name = request.form['role']
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            flash('Invalid role', 'error')
            return redirect(url_for('register'))
        
        # Auto-approve customers, but not farmers
        is_approved = True if role_name == 'customer' else False

        user = User(
            name=name, 
            email=email, 
            phone=phone, 
            role=role,
            is_approved=is_approved  # Set approval status
        )
        user.set_password(password)
        
        # Add farm details and handle license if farmer
        if role_name == 'farmer':
            user.farm_name = request.form.get('farm_name')
            user.location = request.form.get('location')

            # Handle License Upload (MANDATORY for farmers)
            if 'license_doc' in request.files:
                file = request.files['license_doc']
                if file and file.filename != '' and allowed_file(file.filename):
                    # Create a secure filename
                    filename = secure_filename(f"license_{user.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'licenses', filename)
                    file.save(file_path)
                    user.license_filename = filename # Save filename to the user
                else:
                    flash('A valid license document is required for farmer registration.', 'error')
                    return redirect(url_for('register'))
            else:
                flash('License document is required for farmer registration.', 'error')
                return redirect(url_for('register'))
            
            # Handle Profile Picture Upload for farmers
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file and file.filename != '' and allowed_file(file.filename):
                    # Create a secure filename
                    filename = secure_filename(f"profile_{user.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles', filename)
                    file.save(file_path)
                    user.profile_picture = filename # Save filename to the user
                else:
                    flash('A valid profile picture is required for farmer registration.', 'error')
                    return redirect(url_for('register'))
        
        db.session.add(user)
        db.session.commit()

        # Different success messages based on role
        if role_name == 'farmer':
            flash('Registration successful! Your farmer account is pending admin approval. You will be able to log in once approved.', 'success')
        else:
            flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    roles = Role.query.all()
    return render_template('register.html', roles=roles)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        user.phone = request.form['phone']
        user.bio = request.form['bio']
        user.address = request.form['address']
        
        # Add farm details if farmer
        if session['role'] == 'farmer':
            user.farm_name = request.form.get('farm_name')
            user.location = request.form.get('location')
        
        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"user_{user.id}_{file.filename}")
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles', filename)
                file.save(file_path)
                user.profile_picture = filename
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('edit_profile.html', user=user)

@app.route('/farmer_dashboard')
def farmer_dashboard():
    if 'user_id' not in session or session['role'] != 'farmer':
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    products = Product.query.filter_by(farmer_id=user.id).all()
    return render_template('farmer_dashboard.html', user=user, products=products)

@app.route('/customer_dashboard')
def customer_dashboard():
    if 'user_id' not in session or session['role'] != 'customer':
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('customer_dashboard.html', user=user)
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    users = User.query.all()
    products = Product.query.all()  # This should be all products
    orders = Order.query.all()
    categories = Category.query.all()
    return render_template('admin_dashboard.html',
                           users=users,
                           products=products,  # Pass all products
                           orders=orders,
                           categories=categories)
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session or session['role'] != 'farmer':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        category_id = request.form.get('category_id')
        
        product = Product(
            name=name, 
            description=description, 
            price=price, 
            quantity=quantity, 
            farmer_id=session['user_id'],
            category_id=category_id if category_id else None
        )
        
        # Handle product image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"product_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'products', filename)
                file.save(file_path)
                product.image = filename
        
        db.session.add(product)
        db.session.commit()
        flash('Product added, awaiting admin approval', 'success')
        return redirect(url_for('farmer_dashboard'))
    
    categories = Category.query.all()
    return render_template('product_form.html', action='Add', categories=categories)

@app.route('/update_product/<int:id>', methods=['GET', 'POST'])
def update_product(id):
    if 'user_id' not in session or session['role'] != 'farmer':
        return redirect(url_for('login'))
    
    product = Product.query.get_or_404(id)
    if product.farmer_id != session['user_id']:
        flash('Unauthorized', 'error')
        return redirect(url_for('farmer_dashboard'))
    
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.quantity = int(request.form['quantity'])
        product.category_id = request.form.get('category_id')
        product.approved = False  # Reset approval status when updated
        
        # Handle product image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"product_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'products', filename)
                file.save(file_path)
                product.image = filename
        
        db.session.commit()
        flash('Product updated, awaiting admin approval', 'success')
        return redirect(url_for('farmer_dashboard'))
    
    categories = Category.query.all()
    return render_template('product_form.html', product=product, action='Update', categories=categories)

@app.route('/delete_product/<int:id>')
def delete_product(id):
    if 'user_id' not in session or session['role'] != 'farmer':
        return redirect(url_for('login'))
    
    product = Product.query.get_or_404(id)
    if product.farmer_id != session['user_id']:
        flash('Unauthorized', 'error')
        return redirect(url_for('farmer_dashboard'))
    
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted', 'success')
    return redirect(url_for('farmer_dashboard'))

@app.route('/approve_product/<int:id>')
def approve_product(id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    product = Product.query.get_or_404(id)
    product.approved = True
    db.session.commit()
    flash('Product approved', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/reject_product/<int:id>')
def reject_product(id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Product rejected and deleted', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/cart', methods=['GET', 'POST']) # Add POST method
def cart():
    if 'user_id' not in session or session['role'] != 'customer':
        return redirect(url_for('login'))

    cart = session.get('cart', {})

    # Handle POST request to update quantity
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        new_quantity = int(request.form.get('quantity', 1))

        if new_quantity < 1:
            # If quantity is 0 or less, remove the item
            cart.pop(str(product_id), None)
        else:
            cart[str(product_id)] = new_quantity

        session['cart'] = cart
        flash('Cart updated!', 'success')
        return redirect(url_for('cart'))

    # Original GET request logic
    products = Product.query.filter(Product.id.in_(cart.keys())).all()
    cart_items = [{'product': p, 'quantity': cart[str(p.id)]} for p in products]
    total = sum(item['product'].price * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/add_to_cart/<int:id>')
def add_to_cart(id):
    if 'user_id' not in session or session['role'] != 'customer':
        return redirect(url_for('login'))
    
    product = Product.query.get_or_404(id)
    if not product.approved:
        flash('Product not available', 'error')
        return redirect(url_for('index'))
    
    cart = session.get('cart', {})
    cart[str(id)] = cart.get(str(id), 0) + 1
    session['cart'] = cart
    flash('Product added to cart', 'success')
    return redirect(url_for('index'))

@app.route('/remove_from_cart/<int:id>')
def remove_from_cart(id):
    if 'user_id' not in session or session['role'] != 'customer':
        return redirect(url_for('login'))
    
    cart = session.get('cart', {})
    if str(id) in cart:
        if cart[str(id)] > 1:
            cart[str(id)] -= 1
        else:
            del cart[str(id)]
        session['cart'] = cart
        flash('Product removed from cart', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session or session['role'] != 'customer':
        return redirect(url_for('login'))
    
    # Get the current user's cart from the session
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty!', 'error')
        return redirect(url_for('cart'))
    
    # Get the product objects and calculate total for the order summary
    products = Product.query.filter(Product.id.in_(cart.keys())).all()
    cart_items = [{'product': p, 'quantity': cart[str(p.id)]} for p in products]
    total = sum(item['product'].price * item['quantity'] for item in cart_items)
    
    # Get the current user object to pre-fill the address
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        shipping_address = request.form['shipping_address']
        
        # Create new order
        order = Order(
            customer_id=session['user_id'], 
            date=datetime.utcnow(), 
            shipping_address=shipping_address
        )
        db.session.add(order)
        
        # Add items to order and update product quantities
        for product_id, quantity in cart.items():
            product = Product.query.get(int(product_id))
            if product and product.quantity >= quantity and product.approved:
                order_item = OrderItem(
                    order=order, 
                    product_id=product.id, 
                    quantity=quantity,
                    price_at_purchase=product.price
                )
                product.quantity -= quantity  # Reduce product stock
                db.session.add(order_item)
            else:
                db.session.rollback()
                if not product or not product.approved:
                    flash(f'Product "{product.name if product else "Unknown"}" is no longer available.', 'error')
                else:
                    flash(f'Not enough stock for {product.name}. Only {product.quantity} available.', 'error')
                return redirect(url_for('cart'))
        
        db.session.commit()
        session.pop('cart', None)  # Clear the cart
        flash('Order placed successfully!', 'success')
        return redirect(url_for('order_history'))
    
    # Handle GET request - show checkout form
    return render_template('checkout.html', 
                           user=user, 
                           cart_items=cart_items, 
                           total=total)

@app.route('/order_history')
def order_history():
    if 'user_id' not in session or session['role'] != 'customer':
        return redirect(url_for('login'))
    
    orders = Order.query.filter_by(customer_id=session['user_id']).order_by(Order.date.desc()).all()
    return render_template('order_history.html', orders=orders)

@app.route('/admin/add_category', methods=['POST'])
def add_category():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    name = request.form['name']
    if Category.query.filter_by(name=name).first():
        flash('Category already exists', 'error')
        return redirect(url_for('admin_dashboard'))
    
    category = Category(name=name)
    db.session.add(category)
    db.session.commit()
    flash('Category added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_category/<int:id>')
def delete_category(id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/farmer/<int:farmer_id>')
def view_farmer(farmer_id):
    # Get the farmer from database
    farmer = User.query.get_or_404(farmer_id)
    
    # Check if user is actually a farmer
    if farmer.role.name != 'farmer':
        flash('User is not a farmer.', 'error')
        return redirect(url_for('index'))
    
    # Check if farmer is approved (only show approved farmers to customers)
    if not farmer.is_approved:
        flash('Farmer profile is not available.', 'error')
        return redirect(url_for('index'))
    
    # Get all approved products from this farmer
    products = Product.query.filter_by(farmer_id=farmer_id, approved=True).all()
    
    return render_template('farmer_profile.html', farmer=farmer, products=products)

@app.route('/admin/approve_farmer/<int:user_id>')
def approve_farmer(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    farmer = User.query.get_or_404(user_id)
    if farmer.role.name != 'farmer':
        flash('User is not a farmer.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    farmer.is_approved = True
    db.session.commit()
    flash(f'Farmer "{farmer.name}" has been approved! They can now log in.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    # Prevent admin from deleting themselves
    if user_id == session['user_id']:
        flash('You cannot delete your own account!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Additional safety checks
    if user.role.name == 'admin':
        flash('Cannot delete other admin accounts!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Delete user's products if they are a farmer
    if user.role.name == 'farmer':
        # First delete all products associated with this farmer
        Product.query.filter_by(farmer_id=user_id).delete()
    
    # Delete the user
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User "{user.name}" has been deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))
# Route to serve license files
@app.route('/uploads/licenses/<filename>')
def serve_license(filename):
    # Security check to prevent directory traversal attacks
    if '..' in filename or filename.startswith('/'):
        abort(404)
    
    try:
        return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'licenses'), filename)
    except FileNotFoundError:
        abort(404)

# Route to serve product images
@app.route('/uploads/products/<filename>')
def serve_product_image(filename):
    # Security check to prevent directory traversal attacks
    if '..' in filename or filename.startswith('/'):
        abort(404)
    
    try:
        return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'products'), filename)
    except FileNotFoundError:
        abort(404)

# Route to serve profile pictures
@app.route('/uploads/profiles/<filename>')
def serve_profile_image(filename):
    # Security check to prevent directory traversal attacks
    if '..' in filename or filename.startswith('/'):
        abort(404)
    
    try:
        return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'profiles'), filename)
    except FileNotFoundError:
        abort(404)
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Create instance directory if it doesn't exist
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    print(f"Instance directory created/verified: {instance_dir}")
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    with app.app_context():
        db.create_all()
        if not Role.query.first():
            roles = ['admin', 'farmer', 'customer']
            for role in roles:
                db.session.add(Role(name=role))
            db.session.commit()
            print("Default roles created.")
        
        # Add some default categories if none exist
        if not Category.query.first():
            categories = ['Milk', 'Curd', 'Ghee', 'Butter', 'Cheese', 'Paneer']
            for category in categories:
                db.session.add(Category(name=category))
            db.session.commit()
            print("Default categories created.")
    
    app.run(debug=True)