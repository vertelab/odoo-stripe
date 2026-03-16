from odoo import fields, models
import logging

class OnlineBankStatementProvider(models.Model):
    _inherit = 'online.bank.statement.provider'

    invert_amounts_stripe = fields.Boolean(string="Invert Amounts")

    def _obtain_statement_data(self, date_since, date_until):
        self.ensure_one()
        lines, extra = super()._obtain_statement_data(
                date_since,
                date_until,
        )
        # ~ logging.warning(f"1 {lines=}")
        if self.service == "stripe" and self.invert_amounts_stripe:
           for line in lines:
               # ~ logging.warning(f"1 {line['amount']}")
               line['amount'] = line['amount']*-1
               # ~ logging.warning(f"2 {line['amount']}")
               
        # ~ logging.warning(f"2 {lines=}")
        # ~ raise Exception("TEst")
        return lines, extra 
          
