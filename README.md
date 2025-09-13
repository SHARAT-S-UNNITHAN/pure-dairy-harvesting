# Project Documentation 
# Pure Dairy Harvesting 🐄🥛

A Flask-based e-commerce platform connecting dairy farmers directly with customers.

## 🌟 Features

- **Role-based Authentication** (Farmers, Customers, Admin)
- **Product Management** for farmers
- **Shopping Cart & Order System**
- **Responsive Design** with modern UI
- **Real-time Chat** via WhatsApp integration
- **Secure Payment Processing**

## 🛠️ Tech Stack

### Backend
- **Flask** - Python web framework
- **SQLAlchemy** - ORM for database operations
- **Flask-Login** - User session management
- **Werkzeug** - Password hashing and security
- **WTForms** - Form validation and rendering

### Frontend
- **HTML5** - Page structure
- **CSS3** - Styling with custom animations
- **JavaScript** - Interactive elements
- **Bootstrap** - Responsive design framework
- **FontAwesome** - Icons
- **Jinja2** - Templating engine

### Database
- **SQLite** (Development) - Lightweight database
- **PostgreSQL** (Production-ready) - Recommended for production

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/SHARAT-S-UNNITHAN/pure-dairy-harvesting.git
cd pure-dairy-harvesting
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
export SECRET_KEY=your_secret_key_here
```

5. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

6. Run the application:
```bash
flask run
```

## 🗄️ Database Schema

### Users Table
- id (Integer, Primary Key)
- username (String, Unique)
- email (String, Unique)
- password_hash (String)
- role (String: 'farmer', 'customer', 'admin')
- created_at (DateTime)

### Products Table
- id (Integer, Primary Key)
- name (String)
- description (Text)
- price (Float)
- farmer_id (Integer, Foreign Key)
- category (String)
- image_url (String)
- created_at (DateTime)

### Orders Table
- id (Integer, Primary Key)
- customer_id (Integer, Foreign Key)
- total_amount (Float)
- status (String: 'pending', 'completed', 'cancelled')
- created_at (DateTime)

## 🔧 API Endpoints

| Endpoint | Method | Description | Access |
|----------|--------|-------------|--------|
| `/` | GET | Home page | Public |
| `/login` | GET, POST | User login | Public |
| `/register` | GET, POST | User registration | Public |
| `/dashboard` | GET | User dashboard | Authenticated |
| `/products` | GET | Product listing | Public |
| `/product/<id>` | GET | Product details | Public |
| `/cart` | GET, POST | Shopping cart | Customers |
| `/checkout` | POST | Order processing | Customers |
| `/admin` | GET | Admin dashboard | Admin only |

## 🚀 Deployment

### Heroku Deployment
1. Install Heroku CLI
2. Create Procfile with: `web: gunicorn app:app`
3. Set environment variables on Heroku dashboard
4. Deploy using Git: `git push heroku main`

### Traditional Server
1. Install Python, PostgreSQL, nginx
2. Set up Gunicorn as WSGI server
3. Configure nginx as reverse proxy
4. Set up SSL certificate with Let's Encrypt

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

## 📞 Support

For support, sharatsunnithan3@gmail.com or connect via WhatsApp: +91 9061378596

## 🙏 Acknowledgments

- Flask development team
- Bootstrap team for UI components
- FontAwesome for icons
- Unsplash for stock images
```

## 2. TECHNICAL.md (Technical Documentation)

```markdown
# Technical Documentation

## Architecture Overview

Pure Dairy Harvesting follows the Model-View-Controller (MVC) pattern:

### Models
- `User` - Handles user authentication and profiles
- `Product` - Manages product data and inventory
- `Order` - Processes customer orders
- `Cart` - Manages shopping cart functionality

### Views
- Jinja2 templates for server-side rendering
- Responsive design with Bootstrap grid system
- Dynamic elements with vanilla JavaScript

### Controllers
- Flask route handlers
- Business logic implementation
- Database operations with SQLAlchemy

## Security Implementation

### Password Hashing
```python
from werkzeug.security import generate_password_hash, check_password_hash

# Hashing passwords
password_hash = generate_password_hash('plain_password')

# Verifying passwords
is_valid = check_password_hash(password_hash, 'input_password')
```

### Session Management
- Flask-Login for user session handling
- Session timeout after 60 minutes of inactivity
- Secure cookies with HTTPOnly flag

### CSRF Protection
- WTForms with built-in CSRF protection
- CSRF tokens for all form submissions

## Database Relationships

```python
# One-to-Many: Farmer to Products
class Farmer(User):
    products = db.relationship('Product', backref='farmer', lazy=True)

# Many-to-Many: Orders to Products (through OrderItem)
order_items = db.Table('order_items',
    db.Column('order_id', db.Integer, db.ForeignKey('order.id')),
    db.Column('product_id', db.Integer, db.ForeignKey('product.id')),
    db.Column('quantity', db.Integer)
)
```

## Performance Optimizations

- Database indexing on frequently queried fields
- Static file caching with Flask-Assets
- Pagination for product listings
- Lazy loading of images

## Third-Party Integrations

### WhatsApp API
- Direct chat integration using WhatsApp click-to-chat
- No API key required for basic functionality

### Payment Processing
- Placeholder implementation for payment gateway
- Can be extended with Stripe, PayPal, or Razorpay

## Environment Variables

Required environment variables:
- `SECRET_KEY` - Flask application secret key
- `DATABASE_URL` - Database connection string
- `FLASK_ENV` - Development/production environment

## Testing

Run tests with:
```bash
python -m pytest tests/
```

Test coverage includes:
- Unit tests for models and utilities
- Integration tests for routes
- Selenium tests for user workflows
```

## 3. PROJECT_STRUCTURE.md

```markdown
# Project Structure

```
pure-dairy-harvesting/
│
├── app.py                 # Main application entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables (gitignored)
├── .gitignore            # Git ignore rules
│
├── app/                  # Application package
│   ├── __init__.py       # Package initialization
│   ├── models.py         # Database models
│   ├── routes.py         # Application routes
│   ├── forms.py          # WTForms classes
│   ├── utils.py          # Utility functions
│   └── errors.py         # Error handlers
│
├── migrations/           # Database migration scripts
│   ├── versions/         # Migration versions
│   ├── env.py            # Migration environment
│   └── script.py.mako    # Migration template
│
├── tests/                # Test suite
│   ├── __init__.py       # Test package
│   ├── test_models.py    # Model tests
│   ├── test_routes.py    # Route tests
│   └── test_utils.py     # Utility tests
│
├── static/               # Static assets
│   ├── css/
│   │   ├── styles.css    # Main stylesheet
│   │   └── responsive.css # Responsive styles
│   ├── js/
│   │   ├── main.js       # Main JavaScript
│   │   └── cart.js       # Cart functionality
│   ├── images/           # Image assets
│   └── uploads/          # User uploads (gitignored)
│
└── templates/            # Jinja2 templates
    ├── base.html         # Base template
    ├── index.html        # Home page
    ├── auth/             # Authentication templates
    │   ├── login.html
    │   └── register.html
    ├── dashboard/        # Dashboard templates
    │   ├── farmer.html
    │   ├── customer.html
    │   └── admin.html
    ├── products/         # Product templates
    │   ├── list.html
    │   ├── detail.html
    │   └── add.html
    └── orders/           # Order templates
        ├── cart.html
        ├── checkout.html
        └── history.html
```

## Key Files Description

- `app.py`: Initializes the Flask application, registers blueprints, and starts the development server
- `app/__init__.py`: Application factory function and extension initialization
- `app/models.py`: SQLAlchemy models for database tables
- `app/routes.py`: All application routes and view functions
- `app/forms.py`: WTForms for user input validation
- `static/css/styles.css`: Main stylesheet with custom design system
- `templates/base.html`: Base template with navigation, header, and footer
```

