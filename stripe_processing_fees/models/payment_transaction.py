from odoo import models, fields

class PaymentTransactionStripe(models.Model):
    _inherit = 'payment.transaction'


    def _create_payment(self, **extra_create_values):
        payment = super()._create_payment(**extra_create_values)
        return payment
