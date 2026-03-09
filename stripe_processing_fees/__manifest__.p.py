# -*- coding: utf-8 -*-

{
    'name': 'Stripe Payment Processing Fee',
    'category': 'Stripe Payment Processing Fee',
    'sequence': 380,
    'summary': 'Payment Acquirer: Stripe Processing Fee',
    'version': '1.0',
    'description': """Stripe Processing Fee""",
    'depends': ['payment_stripe', 'payment', 'account', 'account_payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_provider_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
