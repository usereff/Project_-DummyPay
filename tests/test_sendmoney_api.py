import os
import uuid
from contextlib import closing

import pytest

from utilities.backend.backend_base import BackendBase
from utilities.config import (
    DUMMYPAY_ANON_KEY,
    EMAIL,
    PASSWORD,
    RECIPIENT_EMAIL,
)


@pytest.mark.api
def test_sendmoney_via_api_debits_wallet_and_records_transaction():
    """Complete an API transfer and verify its balance and ledger effects."""
    # if os.getenv("DUMMYPAY_RUN_API_TESTS", "").lower() != "true":
    #     pytest.skip(
    #         "Set DUMMYPAY_RUN_API_TESTS=true to run a permanent API transfer."
    #     )

    missing = [
        name
        for name, value in (
            ("DUMMYPAY_ANON_KEY", DUMMYPAY_ANON_KEY),
            ("DUMMYPAY_EMAIL", EMAIL),
            ("DUMMYPAY_PASSWORD", PASSWORD),
            ("DUMMYPAY_RECIPIENT_EMAIL", RECIPIENT_EMAIL),
        )
        if not value
    ]
    if missing:
        pytest.fail(
            f"Set the required API test variables: {', '.join(missing)}."
        )

    amount_minor = 100
    with closing(BackendBase()) as api:
        session = api.sign_in(EMAIL, PASSWORD)
        sender_id = session["user"]["id"]
        sender_profile = api.select(
            "profiles",
            select="id,email,preferred_currency",
            id=f"eq.{sender_id}",
        )[0]
        recipient = api.rpc(
            "lookup_recipient", p_email=RECIPIENT_EMAIL
        )[0]
        assert recipient["status"] == "found", (
            f"Recipient lookup returned {recipient['status']!r}."
        )
        assert recipient["user_id"] != sender_id, (
            "The recipient account must differ from the sender."
        )

        wallets = api.select(
            "wallets",
            select="id,currency,balance_minor",
        )
        funded_wallets = [
            wallet
            for wallet in wallets
            if wallet["balance_minor"] >= amount_minor
        ]
        assert funded_wallets, (
            f"No wallet has the {amount_minor}-minor-unit minimum balance."
        )
        wallet = next(
            (
                item
                for item in funded_wallets
                if item["currency"] == sender_profile["preferred_currency"]
            ),
            max(funded_wallets, key=lambda item: item["balance_minor"]),
        )
        balance_before = wallet["balance_minor"]

        quote = api.rpc(
            "create_transfer_quote",
            p_recipient_id=recipient["user_id"],
            p_sending_currency=wallet["currency"],
            p_amount_minor=amount_minor,
            p_input_side="send",
        )
        assert quote["sending_amount_minor"] == amount_minor

        transaction = api.rpc(
            "execute_transfer",
            p_quote_id=quote["quote_id"],
            p_idempotency_key=str(uuid.uuid4()),
        )
        assert transaction["status"] == "completed"
        assert transaction["sender_user_id"] == sender_id
        assert transaction["recipient_user_id"] == recipient["user_id"]
        assert transaction["sending_amount_minor"] == amount_minor

        wallet_after = api.select(
            "wallets",
            select="id,currency,balance_minor",
            id=f"eq.{wallet['id']}",
        )
        assert len(wallet_after) == 1
        assert wallet_after[0]["balance_minor"] == (
            balance_before - amount_minor
        ), "The sender's wallet balance did not decrease by the sent amount."

        ledger_rows = api.select(
            "transactions",
            select=(
                "id,type,status,sender_user_id,recipient_user_id,"
                "sender_wallet_id,sending_amount_minor,sending_currency,"
                "receiving_amount_minor,receiving_currency"
            ),
            id=f"eq.{transaction['id']}",
        )
        assert len(ledger_rows) == 1, (
            "The transfer was not recorded exactly once in the transactions table."
        )
        ledger_transaction = ledger_rows[0]
        assert ledger_transaction["type"] == "transfer"
        assert ledger_transaction["status"] == "completed"
        assert ledger_transaction["sender_user_id"] == sender_id
        assert ledger_transaction["recipient_user_id"] == recipient["user_id"]
        assert ledger_transaction["sender_wallet_id"] == wallet["id"]
        assert ledger_transaction["sending_amount_minor"] == amount_minor
        assert ledger_transaction["sending_currency"] == wallet["currency"]
        assert ledger_transaction["receiving_amount_minor"] == (
            quote["receiving_amount_minor"]
        )
        assert ledger_transaction["receiving_currency"] == (
            recipient["preferred_currency"]
        )

        history = api.rpc(
            "list_my_transactions",
            p_direction="sent",
            p_limit=100,
        )
        history_rows = [
            row for row in history if row["id"] == transaction["id"]
        ]
        assert len(history_rows) == 1, (
            "The transfer is missing from the sender's transaction history."
        )
        assert history_rows[0]["status"] == "completed"
