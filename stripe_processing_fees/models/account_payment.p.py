from odoo import models, fields


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    fee_move_id = fields.Many2one('account.move', string="Fee Entry")

    def _process_processing_fee(self):
        processing_fee_move_id = self.env['account.move'].sudo().with_context(check_move_validity=False).create({
            'move_type': 'entry',
            'journal_id': self.journal_id.id,
            'date': fields.Date.today(),
            'ref': self.move_id.name,
            'line_ids': self._processing_fee_lines(),
        })

        self.write({'fee_move_id': processing_fee_move_id.id})
        processing_fee_move_id.action_post()

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
                'account_id': payment_transaction_id.provider_id.stripe_account_id.id,
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
        return resp
