import logging
import pprint

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.tools import file_open, mute_logger

from odoo.addons.payment_stripe.controllers.main import StripeController

_logger = logging.getLogger(__name__)


class StripeControllerExtended(StripeController):
    _webhook_url = '/payment/stripe/webhook'

    @http.route('/payment/stripe/webhook', type='http', methods=['POST'], auth='public', csrf=False)
    def stripe_webhook(self):
        """ Extended webhook handler to include payout events """
        event = request.get_json_data()
        _logger.info("Notification received from Stripe with data:\n%s", pprint.pformat(event))

        # Handle payout events separately (they don't have transaction references)
        if event['type'] in ('payout.paid', 'payout.failed', 'payout.updated'):
            try:
                stripe_object = event['data']['object']

                provider = request.env.ref('payment.payment_provider_stripe').sudo()

                if provider:
                    # Verify signature without requiring a transaction
                    tx_like = type('obj', (object,), {'provider_id': provider})()
                    self._verify_notification_signature(tx_like)

                    # Handle the payout
                    provider._handle_payout_webhook(stripe_object, event['type'])
                    _logger.info("Successfully processed payout webhook: %s", event['type'])
                else:
                    _logger.warning("No active Stripe provider found to process payout webhook")

            except Exception as e:
                _logger.exception("Error processing payout webhook: %s", str(e))

            return request.make_json_response('')

        # Let parent handle transaction-based events
        return super().stripe_webhook()
