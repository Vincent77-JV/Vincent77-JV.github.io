# Express API surface

## Endpoints
- `POST /api/webhooks/document-upload`
- `POST /api/extractions/route`
- `POST /api/auth/mfa/start`
- `POST /api/auth/mfa/verify`
- `POST /api/payments/razorpay/order`
- `POST /api/payments/razorpay/webhook`
- `GET /api/applications/:id`
- `GET /api/admin/queue`

## Webhook handler behavior
- Accept a temporary PDF URL from the uploader.
- Forward the file to the extraction provider with multipart/form-data and secure header auth.
- Parse the response into the three required fields.
- Apply the bounce-based filter.
- Persist the result and audit the transition.

## Manual-review branch
- Update account status to `Manual Underwriting Review Required`.
- Notify admin with application id, reason, and extracted metrics.

## Clean branch
- Insert the cleaned extraction into the ledger table.
- Continue the underwriting flow without escalation.

## Notes
- Keep all secrets in environment variables.
- Return deterministic JSON for every endpoint.
