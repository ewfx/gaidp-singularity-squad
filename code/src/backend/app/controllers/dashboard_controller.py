from flask import Blueprint, render_template
from ..services.rulebook_service import RulebookService

dashboard_bp = Blueprint('dashboard', __name__)
rulebook_service = RulebookService()

@dashboard_bp.route('/dashboard')
def dashboard():
    """Render the main dashboard page"""
    try:
        # Get all rulebooks
        rulebooks = rulebook_service.get_all_rulebooks()
        return render_template('dashboard.html', rulebooks=rulebooks)
    except Exception as e:
        return render_template('dashboard.html', rulebooks=[], error=str(e)) 