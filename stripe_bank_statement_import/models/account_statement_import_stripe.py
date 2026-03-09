# -*- coding: utf-8 -*-
import logging
from odoo import models
import re
_logger = logging.getLogger(__name__)


class AccountStatementImport(models.TransientModel):
    _inherit = "account.statement.import"

    def _parse_file(self, data_file):
        self.ensure_one()
        _logger.info("=== STRIPE WIZARD START ===")
        try:
            Parser = self.env["account.statement.import.stripe.parser"]
            return Parser.parse(data_file)
        except Exception as e:
            _logger.error("STRIPE BANK PARSER FAILED: %s", e)
        return super()._parse_file(data_file)

    def _complete_stmts_vals(self, stmts_vals, journal, account_number):
        stmts_vals = super()._complete_stmts_vals(stmts_vals, journal, account_number)
        
        for st_vals in stmts_vals:
            for line_vals in st_vals["transactions"]:
                if "stripe_partner_id" in line_vals:
                    partner_id_str = line_vals.pop("stripe_partner_id")
                    
                    id_match = re.search(r'id:\s*(\d+)', partner_id_str)
                    if id_match:
                        partner_id = int(id_match.group(1))
                        partner = self.env['res.partner'].sudo().browse(partner_id)
                        if partner.exists():
                            line_vals["partner_name"] = partner.name
                            line_vals["partner_id"] = partner.id
                        else:
                            _logger.warning("PARTNER NOT FOUND: ID %s", partner_id)
                    else:
                        _logger.warning("NO ID in: %s", partner_id_str)
        
        return stmts_vals
