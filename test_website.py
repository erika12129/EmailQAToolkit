from flask import Flask, request, jsonify, render_template_string
import logging
import re

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Simulated localized content
LOCALIZED_CONTENT = {
    'en': {
        'title': 'Welcome to Products Showcase',
        'message': 'This is the English version of our site.',
        'domain': 'partly-products-showcase.lovable.app'
    },
    'es-mx': {
        'title': 'Bienvenido a Products Showcase',
        'message': 'Esta es la versión en español para México.',
        'domain': 'partly-products-showcase.lovable.app/es-mx'
    }
}

# Template for HTML responses
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .domain-info {
            background-color: #f0f0f0;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .utm-info {
            background-color: #e0f7fa;
            padding: 10px;
            border-radius: 5px;
        }
        h1 {
            color: #333;
        }
        .links {
            margin-top: 20px;
        }
        .links a {
            display: inline-block;
            margin-right: 10px;
            color: #0066cc;
        }
        .product-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        .product-table th, .product-table td {
            border: 1px solid #ddd; 
            padding: 8px;
            text-align: left;
        }
        .product-table th {
            background-color: #f2f2f2;
        }
        .productListContainer {
            overflow-x: auto;
            margin-bottom: 20px;
        }
        .product-section {
            margin: 20px 0;
            padding: 10px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="domain-info">
        <h3>Domain Information</h3>
        <p>Detected Domain: <strong>{{ host }}</strong></p>
        <p>Locale: <strong>{{ lang }}</strong></p>
    </div>
    
    <h1>{{ title }}</h1>
    <p>{{ message }}</p>
    
    {% if 'products' in request.path %}
    <div class="product-section">
        <h2>{{ 'Lista de Productos' if lang == 'es-mx' else 'Product List' }}</h2>
        <div class="productListContainer">
            <table class="product-table">
                <thead>
                    <tr>
                        <th>{{ 'Nombre' if lang == 'es-mx' else 'Name' }}</th>
                        <th>{{ 'Precio' if lang == 'es-mx' else 'Price' }}</th>
                        <th>{{ 'Descripción' if lang == 'es-mx' else 'Description' }}</th>
                    </tr>
                </thead>
                <tbody>
                    {% if lang == 'es-mx' %}
                        <tr><td>Producto 1</td><td>199 MXN</td><td>Descripción del producto 1</td></tr>
                        <tr><td>Producto 2</td><td>299 MXN</td><td>Descripción del producto 2</td></tr>
                        <tr><td>Producto 3</td><td>399 MXN</td><td>Descripción del producto 3</td></tr>
                    {% else %}
                        <tr><td>Product 1</td><td>$9.99</td><td>Description for product 1</td></tr>
                        <tr><td>Product 2</td><td>$19.99</td><td>Description for product 2</td></tr>
                        <tr><td>Product 3</td><td>$29.99</td><td>Description for product 3</td></tr>
                    {% endif %}
                </tbody>
            </table>
        </div>
    </div>
    {% endif %}
    
    <div class="utm-info">
        <h3>UTM Parameters</h3>
        <ul>
            {% for key, value in utm_params.items() %}
                {% if value %}
                    <li><strong>{{ key }}</strong>: {{ value }}</li>
                {% endif %}
            {% endfor %}
        </ul>
    </div>
    
    <div class="links">
        <h3>Test Links</h3>
        <a href="/en?utm_source=test&utm_medium=email&utm_campaign=test_campaign">English</a>
        <a href="/es-mx?utm_source=test&utm_medium=email&utm_campaign=test_campaign">Spanish (Mexico)</a>
        <a href="/products?utm_source=test&utm_medium=email&utm_campaign=test_campaign">Products Page</a>
    </div>
</body>
</html>
"""

def extract_domain_info(host):
    """Extract domain and locale information from host."""
    domain_locale = {}
    
    # Handle default test domains
    if not host or host == 'localhost:5001':
        return {'lang': 'en', 'domain': 'partly-products-showcase.lovable.app'}
    
    # Extract domain from host, removing port if present
    domain = host.split(':')[0]
    
    # Check for .mx TLD to determine locale
    if '.mx.' in domain or domain.endswith('.mx'):
        domain_locale['lang'] = 'es-mx'
    else:
        domain_locale['lang'] = 'en'
    
    domain_locale['domain'] = domain
    return domain_locale

def get_utm_params():
    """Extract all UTM parameters from request."""
    utm_params = {}
    for key, value in request.args.items():
        if key.startswith('utm_') or key == 'webtrends':
            utm_params[key] = value
    return utm_params

@app.route('/')
def index():
    """Default route that handles various domain patterns."""
    # Get domain info from host header
    host = request.headers.get('Host', 'localhost:5001')
    domain_info = extract_domain_info(host)
    lang = domain_info.get('lang', 'en')
    
    # Get localized content
    content = LOCALIZED_CONTENT.get(lang, LOCALIZED_CONTENT['en'])
    title = content['title']
    message = content['message']
    
    # Get UTM parameters
    utm_params = get_utm_params()
    
    # Log request for debugging
    logger.info(f"Request for domain: {host}, lang: {lang}, UTMs: {utm_params}")
    
    # Render HTML template
    html = render_template_string(
        HTML_TEMPLATE,
        lang=lang,
        title=title,
        message=message,
        host=host,
        utm_params=utm_params
    )
    
    return html, 200

@app.route('/<path:path>', methods=['GET', 'HEAD'])
def catch_all(path):
    """Catch all route to handle any paths."""
    # Extract lang code from path
    lang = None
    # Log the path for debugging
    print(f"Received request for path: {path}")
    logger.info(f"Received request for path: {path}")
    
    if path.startswith('es/') or path.startswith('es-mx/'):
        lang = 'es-mx'
    elif path.startswith('en/'):
        lang = 'en'
    else:
        # Check if path itself is a language code
        if path in ['es', 'es-mx']:
            lang = 'es-mx'
        elif path == 'en':
            lang = 'en'
    
    # Default to English if no language detected
    if not lang:
        lang = 'en'
    
    # Get domain info from host header
    host = request.headers.get('Host', 'localhost:5001')
    
    # Get localized content
    content = LOCALIZED_CONTENT.get(lang, LOCALIZED_CONTENT['en'])
    title = content['title']
    message = content['message']
    
    # Get UTM parameters
    utm_params = get_utm_params()
    
    # Log request for debugging
    logger.info(f"Request for /{path} on {host} with UTM: {utm_params} (detected lang: {lang})")
    
    # Render HTML template
    html = render_template_string(
        HTML_TEMPLATE,
        lang=lang,
        title=title,
        message=message,
        host=host,
        utm_params=utm_params
    )
    
    return html, 200

@app.route('/product-list-container', methods=['GET', 'HEAD'])
def product_list_container():
    """Test page that only has productListContainer class (no product-table class)."""
    lang = request.args.get('lang', 'en')
    utm_params = get_utm_params()
    host = request.headers.get('Host', 'localhost:5001')
    
    logger.info(f"Request for /product-list-container on {host} with UTM: {utm_params} (detected lang: {lang})")
    
    html = """<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Product List Container Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .productListContainer {
            border: 1px solid #ddd;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .product-item {
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }
        .utm-info {
            background-color: #e0f7fa;
            padding: 10px;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <h1>Product List Container Test Page</h1>
    <p><strong>This page only has productListContainer class (no product-table)</strong></p>
    
    <div class="productListContainer">
        <h3>{{ 'Nuestros Productos' if lang == 'es-mx' else 'Our Products' }}</h3>
        
        {% if lang == 'es-mx' %}
            <div class="product-item">
                <h4>Producto Premium</h4>
                <p>Precio: 499 MXN</p>
                <p>Descripción: Nuestro producto premium con características exclusivas.</p>
            </div>
            <div class="product-item">
                <h4>Producto Estándar</h4>
                <p>Precio: 299 MXN</p>
                <p>Descripción: La opción estándar con excelente relación calidad-precio.</p>
            </div>
        {% else %}
            <div class="product-item">
                <h4>Premium Product</h4>
                <p>Price: $49.99</p>
                <p>Description: Our premium product with exclusive features.</p>
            </div>
            <div class="product-item">
                <h4>Standard Product</h4>
                <p>Price: $29.99</p>
                <p>Description: The standard option with great value for money.</p>
            </div>
        {% endif %}
    </div>
    
    <div class="utm-info">
        <h3>UTM Parameters</h3>
        <ul>
            {% for key, value in utm_params.items() %}
                {% if value %}
                    <li><strong>{{ key }}</strong>: {{ value }}</li>
                {% endif %}
            {% endfor %}
        </ul>
    </div>
    
    <p><a href="/products?{{ request.query_string.decode() }}">View regular products page with both classes</a></p>
</body>
</html>"""
    
    return render_template_string(
        html,
        lang=lang,
        utm_params=utm_params
    ), 200

@app.route('/product-table-only', methods=['GET', 'HEAD'])
def product_table_only():
    """Test page that only has product-table class (no productListContainer)."""
    lang = request.args.get('lang', 'en')
    utm_params = get_utm_params()
    host = request.headers.get('Host', 'localhost:5001')
    
    logger.info(f"Request for /product-table-only on {host} with UTM: {utm_params} (detected lang: {lang})")
    
    html = """<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Product Table Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .product-table {
            width: 100%;
            border-collapse: collapse;
        }
        .product-table th, .product-table td {
            border: 1px solid #ddd;
            padding: 8px;
        }
        .utm-info {
            background-color: #e0f7fa;
            padding: 10px;
            border-radius: 5px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <h1>Product Table Test Page</h1>
    <p><strong>This page only has product-table class (no productListContainer)</strong></p>
    
    <table class="product-table">
        <thead>
            <tr>
                <th>{{ 'Nombre' if lang == 'es-mx' else 'Name' }}</th>
                <th>{{ 'Precio' if lang == 'es-mx' else 'Price' }}</th>
                <th>{{ 'Descripción' if lang == 'es-mx' else 'Description' }}</th>
            </tr>
        </thead>
        <tbody>
            {% if lang == 'es-mx' %}
                <tr><td>Producto 1</td><td>199 MXN</td><td>Descripción del producto 1</td></tr>
                <tr><td>Producto 2</td><td>299 MXN</td><td>Descripción del producto 2</td></tr>
            {% else %}
                <tr><td>Product 1</td><td>$9.99</td><td>Description for product 1</td></tr>
                <tr><td>Product 2</td><td>$19.99</td><td>Description for product 2</td></tr>
            {% endif %}
        </tbody>
    </table>
    
    <div class="utm-info">
        <h3>UTM Parameters</h3>
        <ul>
            {% for key, value in utm_params.items() %}
                {% if value %}
                    <li><strong>{{ key }}</strong>: {{ value }}</li>
                {% endif %}
            {% endfor %}
        </ul>
    </div>
    
    <p><a href="/product-list-container?{{ request.query_string.decode() }}">View productListContainer page</a></p>
    <p><a href="/products?{{ request.query_string.decode() }}">View regular products page with both classes</a></p>
</body>
</html>"""
    
    return render_template_string(
        html,
        lang=lang,
        utm_params=utm_params
    ), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)