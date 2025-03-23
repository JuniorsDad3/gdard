# auth/biometric_auth.py
from authlib.integrations.flask_client import OAuth
from flask import current_app

oauth = OAuth(current_app)
gov_id = oauth.register(
    name='gov_id',
    client_id=current_app.config['GOV_ID_CLIENT'],
    client_secret=current_app.config['GOV_ID_SECRET'],
    authorize_url='https://auth.gov.za/oauth/authorize',
    token_url='https://auth.gov.za/oauth/token'
)

@routes_bp.route('/login/gov-id')
def gov_id_login():
    redirect_uri = url_for('routes.gov_id_callback', _external=True)
    return gov_id.authorize_redirect(redirect_uri)