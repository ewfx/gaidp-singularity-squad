from flask import Flask
from flask_restx import Api
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Create API with custom configuration
    api = Api(
        title='Regulatory Compliance API',
        version='1.0',
        description='API for regulatory compliance and rulebook management',
        doc='/docs',  # Swagger UI endpoint
        default='rulebooks',  # Default namespace
        default_label='Rulebook Operations',
        # Swagger UI configuration
        authorizations={
            'apikey': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'Authorization'
            }
        },
        # Make UI look better
        ui=True,
        validate=True,
        # Keep endpoints expanded
        ordered=True,
        # Custom UI configuration
        swagger_ui_config={
            'docExpansion': 'list',  # Keep endpoints expanded
            'defaultModelsExpandDepth': -1,  # Expand all models
            'defaultModelExpandDepth': -1,  # Expand all model properties
            'deepLinking': True,  # Enable deep linking
            'displayOperationId': True,  # Show operation IDs
            'displayRequestDuration': True,  # Show request duration
            'filter': True,  # Enable filtering
            'operationsSorter': 'alpha',  # Sort operations alphabetically
            'showExtensions': True,  # Show extensions
            'showCommonExtensions': True,  # Show common extensions
            'supportedSubmitMethods': ['get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace'],  # Show all HTTP methods
            'tryItOutEnabled': True,  # Enable try it out by default
            'persistAuthorization': True,  # Persist authorization
            'syntaxHighlight': True,  # Enable syntax highlighting
            'jsonEditor': True,  # Enable JSON editor
            'defaultModelRendering': 'model',  # Show models by default
        }
    )
    
    # Register namespaces and blueprints
    from .controllers.rulebook_controller import api as rulebook_ns
    from .controllers.dashboard_controller import dashboard_bp
    from .controllers.anomaly_controller import api as anomaly_ns, anomaly_bp
    from .controllers.validation_controller import validation_bp, api as validation_api
    from .controllers.home_controller import home_bp

    # Register REST API namespaces
    api.add_namespace(rulebook_ns)
    api.add_namespace(anomaly_ns)
    api.add_namespace(validation_api)

    # Register template rendering blueprints
    app.register_blueprint(home_bp)  # Register home blueprint first (root route)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(anomaly_bp)
    app.register_blueprint(validation_bp)
    
    # Initialize API with app
    api.init_app(app)
    return app 