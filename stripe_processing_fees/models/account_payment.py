from odoo import models, fields


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    #TODO remove
    fee_move_id = fields.Many2one('account.move', string="Fee Entry")

    def _generate_move_vals(self, write_off_line_vals=None, force_balance=None, line_ids=None):
        res = super()._generate_move_vals(
            write_off_line_vals=write_off_line_vals,
            force_balance=force_balance,
            line_ids=line_ids,
        )
        if self.payment_method_line_id.payment_provider_id.code == "stripe":
            lines = self._processing_fee_lines()
            if lines:
               res['line_ids'] = lines
        return res
        
    def _processing_fee_lines(self):
        balance_transaction = self._get_processing_fee(self._retrieve_balance_transaction_from_charges())

        if not balance_transaction:
            return False

        payment_transaction_id = self.payment_transaction_id

        line_ids = [
            (0, 0, {
                'name': f'{self.payment_transaction_id.reference}',
                'account_id': payment_transaction_id.provider_id.receivable_account_id.id,
                'credit': balance_transaction.get('amount') / 100,
                'debit': 0.0,
            }),
            (0, 0, {
                'name': f"{self.payment_transaction_id.reference}",
                'account_id': payment_transaction_id.provider_id.stripe_receivable_account_id.id,
                'credit': 0.0,
                'debit': balance_transaction.get('net') / 100,
            }),
        ]

        if balance_transaction.get('fee') > 0:
            processing_fee_amount = balance_transaction.get('fee') / 100.0

            line_ids.append(
                (0, 0, {
                    'name': f'{self.payment_transaction_id.reference} - Stripe Processing Fee',
                    'account_id': payment_transaction_id.provider_id.processing_fee_account_id.id,
                    'debit': processing_fee_amount,
                    'credit': 0.0,
                }),
            )
        return line_ids

    def _retrieve_balance_transaction_from_charges(self):
        payment_transaction_id = self.payment_transaction_id
        resp = payment_transaction_id.provider_id._stripe_make_request(
            f'payment_intents/{payment_transaction_id.provider_reference}'
        )
        balance_transaction_id = resp.get("charges", {}).get("data", [{}])[0].get("balance_transaction")
        if balance_transaction_id:
            return balance_transaction_id
        return False


    def _get_processing_fee(self, balance_transaction):        
        if not balance_transaction:
            return False
        resp = self.payment_transaction_id.provider_id._stripe_make_request(f'balance_transactions/{balance_transaction}', method='GET')
        return resp
