# -*- coding: utf-8 -*-
import base64
import csv
import io
import logging
import re
from datetime import datetime

from odoo import models, fields

_logger = logging.getLogger(__name__)


class AccountStatementImportStripeParser(models.TransientModel):
    _name = "account.statement.import.stripe.parser"
    _description = "Stripe CSV Parser"

    def parse(self, data_file):
        _logger.info("=== STRIPE PARSER START ===")
        
        # Decode file
        try:
            content = base64.b64decode(data_file)
        except:
            content = data_file
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1")

        csvfile = io.StringIO(text)
        reader = csv.DictReader(csvfile)

        journal = self.env["account.journal"].browse(self.env.context.get("journal_id"))
        currency_code = (journal.currency_id or journal.company_id.currency_id).name

        transactions = []
        for row in reader:
            charge_id = row.get("id", "").strip()
            date_str = row.get("Created date (UTC)", "").strip()
            amount_str = row.get("Amount", "").strip()
            currency_str = row.get("Currency", "").strip().lower()
            description = row.get("Description", "").strip()
            fee_str = row.get("Fee", "").strip()
            status = row.get("Status", "").strip().lower()
            customer_desc = row.get("Customer Description", "").strip()
            customer_email = row.get("Customer Email", "").strip()

            if status not in ("paid", "succeeded", "captured"):
                continue
            if not date_str or not amount_str:
                continue

            tx_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            amount_str = amount_str.replace(",", ".")
            amount = float(amount_str)

            partner_ref = customer_desc 

            payment_transaction = {
                "date": tx_date.strftime("%Y-%m-%d"),
                "amount": amount * -1,
                "payment_ref": f"{charge_id} {description}"[:100],
                "ref": charge_id,
                "partner_name": customer_email.split("@")[0] if customer_email else False,
                "stripe_partner_id": partner_ref,  # "Odoo Partner: Administrator (id: 3)"
                "unique_import_id": charge_id,
            }
            transactions.append(payment_transaction)
            _logger.info("✓ PAYMENT: +%.2f %s (partner=%s)", amount, charge_id, partner_ref)

          
            if fee_str and fee_str not in ("0,00", "0.00", "0.0", "0"):
                fee_str = fee_str.replace(",", ".")
                try:
                    fee_amount = float(fee_str)
                    if fee_amount > 0:
                        fee_transaction = {
                            "date": tx_date.strftime("%Y-%m-%d"),
                            "amount": fee_amount,
                            "payment_ref": f"{charge_id} - Stripe fee (%.2f SEK)" % fee_amount,
                            "ref": f"{charge_id}-fee",
                            "partner_name": customer_email.split("@")[0] if customer_email else False,
                            "stripe_partner_id": partner_ref, 
                            "unique_import_id": f"{charge_id}-fee",
                        }
                        transactions.append(fee_transaction)
                        _logger.info("✓ FEE: -%.2f %s (SAME partner=%s)", fee_amount, charge_id, partner_ref)
                except:
                    pass

        _logger.info("✓ Created %d transactions", len(transactions))
        if not transactions:
            return currency_code, False, [{"transactions": []}]

        data = {
            "date": transactions[0]["date"],
            "name": f"{journal.code}: Stripe Import" if journal else "Stripe Import",
            "transactions": transactions,
        }
        return currency_code, False, [data]
