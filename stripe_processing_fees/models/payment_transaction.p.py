from odoo import models, fields

class PaymentTransactionStripe(models.Model):
    _inherit = 'payment.transaction'


    # #if VERSION <=  "17.0"
    def _create_payment(self, add_payment_vals={}):
        payment = super()._create_payment(add_payment_vals=add_payment_vals)
    # # else
    def _create_payment(self, **extra_create_values):
        payment = super()._create_payment(**extra_create_values)
    # # endif
        return payment
