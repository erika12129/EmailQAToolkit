from flask import Flask, request, jsonify
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Simulated localized content
LOCALIZED_CONTENT = {
    'en': {
        'title': 'Welcome to SomeDomain',
        'message': 'This is the English version of our site.'
    },
    'es-mx': {
        'title': 'Bienvenido a SomeDomain',
        'message': 'Esta es la versión en español para México.'
    }
}

@app.route('/<lang>/', methods=['GET'])
@app.route('/<lang>', methods=['GET'])
def localized_page(lang):
    """Serve localized page based on language code."""
    if lang not in LOCALIZED_CONTENT:
        return jsonify({'error': 'Language not supported'}), 404
    
    # Extract UTM parameters
    utm_params = {
        'utm_source': request.args.get('utm_source', ''),
        'utm_medium': request.args.get('utm_medium', ''),
        'utm_campaign': request.args.get('utm_campaign', '')
    }
    
    # Log request for debugging
    logger.info(f"Request for /{lang} with UTM: {utm_params}")
    
    # Simple HTML response
    content = LOCALIZED_CONTENT[lang]
    html = f"""
    <!DOCTYPE html>
    <html lang="{lang}">
    <head>
        <title>{content['title']}</title>
    </head>
    <body>
        <h1>{content['title']}</h1>
        <p>{content['message']}</p>
        <p>UTM Parameters: {', '.join([f'{k}={v}' for k, v in utm_params.items() if v])}</p>
    </body>
    </html>
    """
    return html, 200

@app.route('/')
def index():
    """Default route for testing."""
    return jsonify({'message': 'Test website is running. Try /en or /es-mx'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)