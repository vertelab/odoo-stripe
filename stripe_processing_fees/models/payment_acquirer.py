from odoo import models, fields



class PaymentAcquirerStripe(models.Model):
    _inherit = 'payment.provider'

    def _handle_stripe_webhook(self, data):
        wh_type = data.get('type')
        stripe_object = data.get('data', {}).get('object')
        if wh_type == 'payout.paid':
            return self._handle_payout_webhook(stripe_object)
        return super()._handle_stripe_webhook(data)

    def _handle_payout_webhook(self, checkout_object):
        tx_reference = checkout_object.get('id')
        amount = checkout_object.get('amount') / 100.0
        currency_id = self.env['res.currency'].sudo().search([
            ('name', '=', checkout_object.get('currency').upper())
        ], limit=1)
        description = checkout_object.get('description')
        balance_transaction = checkout_object.get('balance_transaction')
        account_number_id = checkout_object.get('destination')

        stripe_payment_acquirer = self.env.ref('payment.payment_acquirer_stripe')
        bank_journal_id = stripe_payment_acquirer.journal_id

        bank_stmt = self.env['account.bank.statement'].sudo().create({
            'journal_id': bank_journal_id.id,
            'date': fields.Date.today(),
            'line_ids': [(0, 0, {
                'payment_ref': tx_reference,
                'ref': tx_reference,
                'transaction_type': description,
                'narration': f"{description} - {balance_transaction}",
                'account_number': account_number_id,
                'amount': amount,
                'currency_id': currency_id.id,
            })],
        })
        bank_stmt.button_post()
        return True
