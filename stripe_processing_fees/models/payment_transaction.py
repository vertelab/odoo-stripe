from odoo import models, fields



class PaymentTransactionStripe(models.Model):
    _inherit = 'payment.transaction'

    def _create_payment(self, add_payment_vals={}):
        payment = super()._create_payment(add_payment_vals=add_payment_vals)
        payment._process_processing_fee()
        return payment


