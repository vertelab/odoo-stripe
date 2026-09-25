# -*- coding: utf-8 -*-

{
    'website': 'https://vertel.se/apps/odoo-stripe/stripe_processing_fees',
    'name': 'Stripe Payment Processing Fee',
    'category': 'Stripe Payment Processing Fee',
    'sequence': 380,
    'summary': 'Payment Acquirer: Stripe Processing Fee.',
    'version': '18.0.1.0.0',
    'description': '''
Stripe Payment Processing Fee
=============================

    Payment Acquirer: Stripe Processing Fee.

    Features:

        - Web integration: Exposes HTTP endpoints for external systems.
        - UI Integration: Extends 4 view(s) in the Odoo interface.
        - Extends Odoo: Builds on account.payment, payment.acquirer, payment.provider, payment.transaction.
    ''',
    'depends': ['payment_stripe', 'payment', 'account', 'account_payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_provider_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
