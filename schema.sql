CREATE TABLE users (
  id UUID PRIMARY KEY,
  role TEXT NOT NULL CHECK (role IN ('client', 'admin', 'underwriter')),
  full_name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  phone TEXT NOT NULL,
  mfa_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE client_applications (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  business_name TEXT NOT NULL,
  pincode CHAR(6) NOT NULL CHECK (pincode ~ '^[1-9][0-9]{5}$'),
  status TEXT NOT NULL CHECK (status IN ('draft', 'submitted', 'in_review', 'manual_review', 'approved', 'rejected')),
  total_monthly_bank_credits NUMERIC(14,2),
  cheque_bounces_last_90_days INTEGER NOT NULL DEFAULT 0,
  gst_active_status BOOLEAN,
  foir_percent NUMERIC(5,2),
  net_lending_capacity NUMERIC(14,2),
  success_fee_percent NUMERIC(5,2),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE application_documents (
  id UUID PRIMARY KEY,
  application_id UUID NOT NULL REFERENCES client_applications(id),
  file_name TEXT NOT NULL,
  file_type TEXT NOT NULL,
  storage_url TEXT NOT NULL,
  checksum TEXT NOT NULL,
  extracted_payload JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE payments (
  id UUID PRIMARY KEY,
  application_id UUID NOT NULL REFERENCES client_applications(id),
  razorpay_order_id TEXT UNIQUE,
  razorpay_payment_id TEXT UNIQUE,
  amount_inr NUMERIC(12,2) NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('created', 'authorized', 'captured', 'failed', 'refunded')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE audit_logs (
  id UUID PRIMARY KEY,
  actor_user_id UUID REFERENCES users(id),
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id UUID,
  payload JSONB NOT NULL,
  ip_address INET,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE document_extractions (
  id UUID PRIMARY KEY,
  document_id UUID NOT NULL REFERENCES application_documents(id),
  source_url TEXT NOT NULL,
  total_monthly_bank_credits NUMERIC(14,2),
  cheque_bounces_last_90_days INTEGER NOT NULL DEFAULT 0,
  gst_active_status BOOLEAN,
  account_status TEXT NOT NULL,
  routed_to_manual_review BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
