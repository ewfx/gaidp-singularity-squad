from flask import Flask
from flask_restx import Api
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize Flask-RestX with enhanced configuration
    api = Api(
        app,
        version='1.0',
        title='Regulatory Rulebook API',
        description='''
        Enterprise-grade API for managing regulatory rulebooks and documents.
        
        This API provides endpoints for:
        * Uploading regulatory PDF documents
        * Managing rulebook metadata
        * Retrieving rulebook information
        
        ## Features
        * PDF file validation
        * Automatic UUID generation
        * Metadata management
        * File size limits
        * Secure file storage
        
        ## Security
        * File type validation
        * Size restrictions
        * Secure filename handling
        ''',
        doc='/docs',
        authorizations={
            'apikey': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-API-Key'
            }
        },
        contact='API Support',
        license='Proprietary',
        license_url='https://example.com/license'
    )
    
    # Register namespaces
    from .controllers.rulebook_controller import api as rulebook_ns
    from .controllers.anomaly_controller import api as anomaly
    api.add_namespace(rulebook_ns)
    api.add_namespace(anomaly)   
    return app 