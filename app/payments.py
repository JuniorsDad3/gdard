# app/payments.py
import stripe
from flask import current_app, url_for

stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

def create_stripe_checkout(product, quantity, farmer):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'zar',
                    'product_data': {
                        'name': product.name,
                    },
                    'unit_amount': int(product.price * 100),
                },
                'quantity': quantity,
            }],
            mode='payment',
            success_url=url_for('payment_success', _external=True),
            cancel_url=url_for('marketplace', _external=True),
            metadata={
                'product_id': product.id,
                'buyer_id': current_user.id,
                'farmer_id': farmer.id
            }
        )
        return session.id
    except Exception as e:
        current_app.logger.error(f"Stripe Error: {str(e)}")
        return None