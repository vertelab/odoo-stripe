import json
import re
import urllib.request
from datetime import datetime
from urllib.error import HTTPError
from urllib.parse import urlencode

import pytz

from odoo import api, fields, models
from odoo.exceptions import UserError

class OnlineBankStatementProvider(models.Model):
    _inherit = 'online.bank.statement.provider'

    def _obtain_statement_data(self, date_since, date_until):
        self.ensure_one()
        if self.service != "stripe":
            return super()._obtain_statement_data(
                date_since,
                date_until,
            )  # pragma: no cover
        currency = self.currency_id or self.company_id.currency_id
        if date_since.tzinfo:
            date_since = date_since.astimezone(pytz.utc).replace(tzinfo=None)
        if date_until.tzinfo:
            date_until = date_until.astimezone(pytz.utc).replace(tzinfo=None)
        date_since = int(date_since.timestamp())
        date_until = int(date_until.timestamp())
        params = [
            ("created[gte]", date_since),
            ("created[lt]", date_until),
        ]
        for s in self.stripe_expand.split(","):
            s = s.strip()
            if not s:
                continue
            params.append(("expand[]", s))
        lines = []
        for tx in self._stripe_api_get_all("/balance_transactions", params):
            line1 = False
            line2 = False
            if tx["currency"].lower() != currency.name.lower():
                continue
            
            line1 = {
                    "ref": safe_format(self.stripe_reference, tx),
                    "payment_ref": safe_format(self.stripe_label, tx),
                    "narration": safe_format(self.stripe_note, tx),
                    "amount": float(tx["amount"]) / (10**currency.decimal_places),
                    "date": datetime.fromtimestamp(tx["created"]),
                    "unique_import_id": tx["id"],
                    "raw_data": json.dumps(tx),
                }
            
            if tx.get("fee"):
               line2 = {
                        "ref": safe_format(self.stripe_fee_reference, tx),
                        "payment_ref": safe_format(self.stripe_fee_label, tx),
                        "narration": safe_format(self.stripe_fee_note, tx),
                        "amount": float(tx["fee"]) / (10**currency.decimal_places),
                        "date": datetime.fromtimestamp(tx["created"]),
                        "unique_import_id": tx["id"] + "_fee",
                        "raw_data": json.dumps(tx),
                    }
               line1['amount'] = line1['amount'] - line2['amount']
            if line1:
                lines.append(line1)
            if line2:
                lines.append(line2) 
        return lines, {}
        
def safe_format(template, kwargs):
    template = template or ""

    def sub(m: re.Match):
        val = kwargs
        for k in m.group(1).split("."):
            try:
                val = val[k]
            except (KeyError, TypeError):
                val = None
        if val is None:
            return ""
        return str(val)

    return re.sub(r"\{([^}]+)\}", sub, template)
