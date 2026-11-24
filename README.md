# Project_-DummyPay

## CI

GitHub Actions runs the pytest suite on pushes, pull requests, and manual dispatches. Create a GitHub environment named `test` and add `DUMMYPAY_EMAIL`, `DUMMYPAY_PASSWORD`, and `DUMMYPAY_RECIPIENT_EMAIL` as secrets for that environment before enabling the workflow.

## API transfer test

The API transfer test uses the same sender and recipient credentials, plus
`DUMMYPAY_ANON_KEY` containing the Supabase publishable key. It is skipped by
default because successful transfers are permanent ledger entries. To run it
locally, set those variables and explicitly opt in:

```powershell
$env:DUMMYPAY_RUN_API_TESTS = "true"
python -m pytest tests/test_sendmoney_api.py
```

The test sends 100 minor units (1.00 in the sending currency). Use dedicated
test accounts; do not use a service-role key.