"""Billing and subscription handlers for the interactive CLI.

Nous Portal billing / subscription was removed from this build. The mixin
keeps the method names so ``HermesCLI`` MRO call sites do not crash; every
handler reports that Portal billing is unavailable.
"""

from __future__ import annotations


class CLIBillingMixin:
    """Mixin holding interactive-CLI billing and subscription handlers."""

    def _print_nous_credits_block(self) -> bool:
        """Nous Portal credits display was removed — print nothing."""
        return False

    def _print_usage_cta(self) -> None:
        """No Portal billing CTA after removal."""
        return None

    def _show_subscription(self):
        from cli import _cprint, _d

        _cprint(f"  {_d('Nous Portal subscription was removed from this build.')}")

    def _show_billing(self, command: str = "/topup"):
        from cli import _cprint, _d

        del command
        _cprint(f"  {_d('Nous Portal billing was removed from this build.')}")

    # --- private helpers kept as no-ops so legacy call sites do not AttributeError ---

    def _subscription_overview(self, state, manage_url):
        del state, manage_url
        self._show_subscription()

    def _open_url_in_browser(self, url: str) -> bool:
        del url
        return False

    def _subscription_free_catalog(self, state, manage_url):
        del state, manage_url
        self._show_subscription()

    def _subscription_open_portal(self, state, manage_url, *, verb="Manage your subscription"):
        del state, manage_url, verb
        self._show_subscription()

    def _subscription_change_menu(self, state, manage_url):
        del state, manage_url
        self._show_subscription()

    def _subscription_pick_tier(self, state):
        del state
        return None

    def _subscription_preview_and_confirm(self, state, tier_id, *, allow_stepup=True):
        del state, tier_id, allow_stepup
        self._show_subscription()

    def _subscription_confirm_cancel(self, state):
        del state
        self._show_subscription()

    def _subscription_apply(self, state, action, idempotency_key=None, *, allow_stepup=True):
        del state, action, idempotency_key, allow_stepup
        self._show_subscription()

    def _subscription_handle_scope_required(self, state, *, retry, idempotency_key=None):
        del state, retry, idempotency_key
        self._show_subscription()

    def _subscription_render_error(self, state, exc):
        del state, exc
        self._show_subscription()

    def _subscription_render_upgrade_ambiguous(self, exc):
        del exc
        self._show_subscription()

    def _billing_portal_hint(self, state, *, reason: str = "") -> None:
        del state, reason
        self._show_billing()

    def _billing_overview(self, state):
        del state
        self._show_billing()

    def _usage_bar_lines(self, usage, plan_name) -> list:
        del usage, plan_name
        return []

    def _billing_open_portal(self, state):
        del state
        self._show_billing()

    def _billing_require_admin(self, state) -> bool:
        del state
        return False

    def _billing_add_card_flow(self, state):
        del state
        self._show_billing()

    def _billing_buy_flow(self, state):
        del state
        self._show_billing()

    def _billing_confirm_and_charge(self, state, amount):
        del state, amount
        self._show_billing()

    def _billing_poll_charge(self, state, charge_id, amount):
        del state, charge_id, amount
        self._show_billing()

    def _billing_render_charge_failed(self, state, reason):
        del state, reason
        self._show_billing()

    def _billing_render_charge_error(self, state, exc):
        del state, exc
        self._show_billing()

    def _billing_handle_scope_required(self, state, *, amount=None, idempotency_key=None):
        del state, amount, idempotency_key
        self._show_billing()

    def _billing_auto_reload_flow(self, state):
        del state
        self._show_billing()

    def _billing_auto_reload_disable(self, state):
        del state
        self._show_billing()

    def _billing_limit_screen(self, state):
        del state
        self._show_billing()
