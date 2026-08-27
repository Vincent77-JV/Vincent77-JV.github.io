# JinOps document parsing automation blueprint

## Workflow sequence
1. **Trigger node**: Custom Webhook receives a POST payload from the JinOps.tech uploader with a temporary PDF download URL.
2. **Processing node**: HTTP multipart/form-data request submits the file URL to Docsumo or Base64.ai using a secure API header key.
3. **Extraction rule**: Parse the text layer and isolate:
   - `total_monthly_bank_credits`
   - `cheque_bounces_last_90_days`
   - `gst_active_status`
4. **Logic filter node**:
   - If `cheque_bounces_last_90_days > 0`, set `account_status = "Manual Underwriting Review Required"` and send a secure admin notification payload.
   - If `cheque_bounces_last_90_days = 0`, write the clean output directly to the active Xano ledger table.

## Webhook contract
**Incoming request**
```json
{
  "application_id": "uuid",
  "temporary_pdf_url": "https://...",
  "document_type": "bank_statement",
  "source": "jinops_uploader"
}
```

**Extraction payload**
```json
{
  "file_url": "https://...",
  "fields": [
    "total_monthly_bank_credits",
    "cheque_bounces_last_90_days",
    "gst_active_status"
  ]
}
```

## Routing logic
- Use strict numeric parsing for bounces.
- Preserve the original extraction payload in the database for auditability.
- Notify administrators only when the manual-review branch is taken.

## Security controls
- Verify webhook signature and origin.
- Keep the extraction key in server-side secrets only.
- Avoid exposing temporary URLs to the browser after ingestion.
- Log every state transition to audit storage.

## Xano writeback
When the clean branch is selected, push:
```json
{
  "application_id": "uuid",
  "total_monthly_bank_credits": 1200000,
  "cheque_bounces_last_90_days": 0,
  "gst_active_status": true,
  "account_status": "Clean for Automated Underwriting"
}
```
