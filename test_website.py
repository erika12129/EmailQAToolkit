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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)