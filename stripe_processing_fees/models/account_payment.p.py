from odoo import models, fields


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    fee_move_id = fields.Many2one('account.move', string="Fee Entry")

    def _process_processing_fee(self):
        processing_fee = self._get_processing_fee(self._retrieve_balance_transaction_from_charges())
        if not processing_fee:
            return

        processing_fee_amount = processing_fee / 100.0

        processing_fee_move_id = self.move_id.copy({'ref': self.move_id.name})
        for move_line in processing_fee_move_id.line_ids:
            if move_line.debit > 0:
                # Was debit, now becomes credit with processing fee amount
                move_line.with_context(check_move_validity=False).write({
                    'debit': 0.0,
                    'credit': processing_fee_amount,
                    'name': f'{move_line.name} - Stripe Processing Fee'
                })
            elif move_line.credit > 0:
                # Was credit, now becomes debit with processing fee amount
                move_line.with_context(check_move_validity=False).write({
                    'debit': processing_fee_amount,
                    'credit': 0.0,
                    'name': f'{move_line.name} - Stripe Processing Fee'
                })
        self.write({'fee_move_id': processing_fee_move_id.id})
        processing_fee_move_id.action_post()

    def _retrieve_balance_transaction_from_charges(self):
        payment_transaction_id = self.payment_transaction_id
        # #if VERSION <=  "14.0"
        resp = payment_transaction_id.acquirer_id._stripe_request(
            f'charges/{payment_transaction_id.acquirer_reference}'
        )
        # # elif VERSION <=  "17.0"
        resp = payment_transaction_id.acquirer_id._stripe_make_request(
            f'charges/{payment_transaction_id.acquirer_reference}'
        )
        # # elif VERSION >=  "18.0"
        resp = payment_transaction_id.provider_id._stripe_make_request(
            f'payment_intents/{payment_transaction_id.provider_reference}'
        )
        balance_transaction_id = resp.get("charges", {}).get("data", [{}])[0].get("balance_transaction")
        # # endif
        # # if VERSION <=  "17.0"
        if resp.get('balance_transaction'):
            return resp.get('balance_transaction')
        # # elif VERSION <=  "18.0"
        if balance_transaction_id:
            return balance_transaction_id
        # # endif
        return False


    def _get_processing_fee(self, balance_transaction):        
        if not balance_transaction:
            return False
        # #if VERSION <=  "14.0"
        resp = self.payment_transaction_id.acquirer_id._stripe_request(f'balance_transactions/{balance_transaction}', method='GET')
        # #  elif VERSION <=  "17.0"
        resp = self.payment_transaction_id.acquirer_id._stripe_make_request(f'balance_transactions/{balance_transaction}', method='GET')
        # #  elif VERSION >=  "18.0"
        resp = self.payment_transaction_id.provider_id._stripe_make_request(f'balance_transactions/{balance_transaction}', method='GET')
        # # endif
        if resp.get('fee'):
            return resp.get('fee')
        return False
