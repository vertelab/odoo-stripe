from odoo import models, fields
from odoo.exceptions import UserError


class PaymentAcquirerStripe(models.Model):
    _inherit = 'payment.provider'

    bank_journal_id = fields.Many2one('account.journal', string='Bank Journal', domain=[('type', '=', 'bank')])
    processing_fee_account_id = fields.Many2one('account.account', string='Processing Fee Account')
    receivable_account_id = fields.Many2one('account.account', string='Receivable Account')
    stripe_receivable_account_id = fields.Many2one('account.account', string='Stripe Account')

    def _handle_payout_webhook(self, checkout_object, wh_type):
        if not checkout_object:
            return False

        if wh_type == 'payout.paid':
            return self._process_paid_payout(checkout_object)
        return None

    def _process_paid_payout(self, checkout_object):
        payout_amount = checkout_object.get('amount') / 100.0

        currency_id = self.env['res.currency'].sudo().search([
            ('name', '=', checkout_object.get('currency').upper())
        ], limit=1)
        if not currency_id:
            raise UserError(f"Currency is probably not active or does not exist")

        bank_transfer_fee = 0.0
        if checkout_object.get('application_fee_amount'):
            bank_transfer_fee = checkout_object.get('application_fee_amount') / 100.0

        provider_id = self.env.ref('payment.payment_provider_stripe')

        account_move = self.env['account.move'].sudo().sudo().with_context(check_move_validity=False).create({
            'move_type': 'entry',
            'journal_id': provider_id.bank_journal_id.id,
            'date': fields.Date.today(),
            'ref': checkout_object.get('id'),
            'narration': f"{checkout_object.get('description')} - {checkout_object.get('balance_transaction')}",
            'line_ids': self._payout_move_lines(
                description=checkout_object.get('description'),
                payout_amount=payout_amount,
                transfer_fee=bank_transfer_fee,
                currency_id=currency_id,
                provider_id=provider_id
            ),
        })
        account_move.action_post()
        return True

    def _payout_move_lines(self, description, payout_amount, transfer_fee, currency_id, provider_id):
        line_ids = [
            # Credit: Stripe suspense account (total payout + fee)
            (0, 0, {
                'name': f"Stripe Payout - {description}",
                'account_id': provider_id.bank_journal_id.default_account_id.id,
                'credit': 0.0,
                'debit': payout_amount + transfer_fee,
                'currency_id': currency_id.id,
            }),

            # Debit: Bank account (net amount received)
            (0, 0, {
                'name': f"Stripe Payout - {description}",
                'account_id': provider_id.stripe_receivable_account_id.id,
                'debit': 0.0,
                'credit': payout_amount,
                'currency_id': currency_id.id,
            }),
        ]

        # Add transfer fee line if exists
        if transfer_fee:
            line_ids.append((0, 0, {
                'name': f"Stripe Transfer Fee - {description}",
                'account_id': provider_id.processing_fee_account_id.id,
                'credit': transfer_fee,
                'debit': 0.0,
                'currency_id': currency_id.id,
            }))
        return line_ids

