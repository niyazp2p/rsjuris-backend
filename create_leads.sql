-- =============================================================================
-- 1. ENUMS CREATION (Guarded against duplication)
-- =============================================================================
DO $$ BEGIN
    CREATE TYPE audiencesegment AS ENUM ('INDIVIDUAL', 'BUSINESS');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE leadstatus AS ENUM (
        'INTAKE', 
        'PRE_LITIGATION_REVIEW', 
        'RETAINED', 
        'IN_LITIGATION', 
        'SETTLED', 
        'CLOSED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE leadpriority AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'URGENT');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- =============================================================================
-- 2. CRM SCHEMA SETUP
-- =============================================================================
CREATE TABLE IF NOT EXISTS leads (
    id VARCHAR PRIMARY KEY,
    lead_number VARCHAR(100) UNIQUE NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    client_email VARCHAR(255) NOT NULL,
    client_phone VARCHAR(50) NOT NULL,
    alternate_phone VARCHAR(50),
    audience audiencesegment NOT NULL DEFAULT 'INDIVIDUAL',
    practice_area VARCHAR(150) NOT NULL,
    case_title VARCHAR(255) NOT NULL,
    case_description TEXT NOT NULL,
    court_forum VARCHAR(150),
    opposing_party VARCHAR(255),
    case_filing_number VARCHAR(100),
    claim_value NUMERIC(14, 2),
    status leadstatus NOT NULL DEFAULT 'INTAKE',
    priority leadpriority NOT NULL DEFAULT 'MEDIUM',
    enquiry_id VARCHAR UNIQUE REFERENCES enquiries(id) ON DELETE SET NULL,
    assigned_to_id VARCHAR REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_leads_number ON leads(lead_number);
CREATE INDEX IF NOT EXISTS ix_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS ix_leads_priority ON leads(priority);
CREATE INDEX IF NOT EXISTS ix_leads_practice_area ON leads(practice_area);

CREATE TABLE IF NOT EXISTS lead_remarks (
    id VARCHAR PRIMARY KEY,
    lead_id VARCHAR NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    author_id VARCHAR REFERENCES users(id) ON DELETE SET NULL,
    author_name VARCHAR(255) NOT NULL,
    remark TEXT NOT NULL,
    prev_status VARCHAR(50),
    next_status VARCHAR(50),
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_lead_remarks_lead_id ON lead_remarks(lead_id);

-- =============================================================================
-- 3. SEED LEADS DATA
-- =============================================================================
INSERT INTO leads (
    id,
    lead_number,
    client_name,
    client_email,
    client_phone,
    alternate_phone,
    audience,
    practice_area,
    case_title,
    case_description,
    court_forum,
    opposing_party,
    case_filing_number,
    claim_value,
    status,
    priority,
    created_at,
    updated_at
) VALUES 
(
    'e9876543-210f-edcb-a098-76543210fedc',
    'RSJ-CAS-2026-7241',
    'Apex Realties Private Limited',
    'counsel@apexrealties.com',
    '+91 98111 22334',
    '+91 11 4321 0000',
    'BUSINESS',
    'Property & Real Estate Law',
    'Apex Realties vs State Infrastructure Corp',
    'Commercial contract breach and recovery of earnest money deposit across commercial metro corridor development.',
    'High Court of Delhi - Commercial Division',
    'State Infrastructure Corporation',
    'CS(COMM)/412/2026',
    25000000.00,
    'IN_LITIGATION',
    'HIGH',
    NOW() - INTERVAL '3 days',
    NOW()
),
(
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    'RSJ-CAS-2026-8092',
    'InnovateTech Solutions Pvt Ltd',
    'aditi@innovatetech.io',
    '+91 98100 12345',
    NULL,
    'BUSINESS',
    'Corporate & Commercial Law',
    'InnovateTech Shareholder Dispute & IP Covenant Breach',
    'Shareholder deadlock and petition under Section 241/242 regarding illegal dilution and proprietary algorithm theft.',
    'NCLT New Delhi Principal Bench',
    'Promoter Group Shareholders',
    'CP/182(ND)/2026',
    48000000.00,
    'RETAINED',
    'URGENT',
    NOW() - INTERVAL '2 days',
    NOW()
),
(
    'b2c3d4e5-f6a7-8901-bcde-f12345678901',
    'RSJ-CAS-2026-3104',
    'Vikramaditya Singhania',
    'v.singhania@apexholding.com',
    '+91 98200 99881',
    NULL,
    'INDIVIDUAL',
    'Criminal Law',
    'State vs Singhania (Section 41A Defense)',
    'Notice issued under Section 41A CrPC concerning scheduled financial transaction audits; urgent anticipatory bail sought.',
    'Sessions Court, Patiala House',
    'State Economic Offences Wing',
    'BA/912/2026',
    NULL,
    'PRE_LITIGATION_REVIEW',
    'URGENT',
    NOW() - INTERVAL '1 day',
    NOW()
),
(
    'c3d4e5f6-a7b8-9012-cdef-123456789012',
    'RSJ-CAS-2026-1189',
    'Meera Nair',
    'meera.nair@outlook.com',
    '+91 97112 44321',
    NULL,
    'INDIVIDUAL',
    'Civil Litigation & Dispute Resolution',
    'Meera Nair vs K.R. Enterprises',
    'Commercial dispute concerning recovery of advance security deposits and injunctive relief on retail leases.',
    'District Commercial Court, Saket',
    'K.R. Enterprises',
    'ARB/55/2026',
    3500000.00,
    'INTAKE',
    'MEDIUM',
    NOW() - INTERVAL '5 hours',
    NOW()
)
ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- 4. SEED LEAD REMARKS (Includes author_name)
-- =============================================================================
INSERT INTO lead_remarks (
    id,
    lead_id,
    author_id,
    author_name,
    remark,
    prev_status,
    next_status,
    created_at
)
SELECT 
    'rem-lead-001',
    'e9876543-210f-edcb-a098-76543210fedc',
    u.id,
    u.full_name,
    'Initial chamber consultation completed. Retainer executed for Commercial Division suit.',
    'INTAKE',
    'RETAINED',
    NOW() - INTERVAL '3 days'
FROM users u WHERE u.email = 'admin@rsjuris.com'
LIMIT 1
ON CONFLICT (id) DO NOTHING;

INSERT INTO lead_remarks (
    id,
    lead_id,
    author_id,
    author_name,
    remark,
    prev_status,
    next_status,
    created_at
)
SELECT 
    'rem-lead-002',
    'e9876543-210f-edcb-a098-76543210fedc',
    u.id,
    u.full_name,
    'Plaint filed before Commercial Division. Ex-parte ad-interim injunction granted against encashment of earnest deposits.',
    'RETAINED',
    'IN_LITIGATION',
    NOW() - INTERVAL '1 day'
FROM users u WHERE u.email = 'admin@rsjuris.com'
LIMIT 1
ON CONFLICT (id) DO NOTHING;

INSERT INTO lead_remarks (
    id,
    lead_id,
    author_id,
    author_name,
    remark,
    prev_status,
    next_status,
    created_at
)
SELECT 
    'rem-lead-003',
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    u.id,
    u.full_name,
    'Draft company petition finalized. Interim stay application drafted under Section 242(2) for hearing before Principal Bench.',
    'INTAKE',
    'RETAINED',
    NOW() - INTERVAL '18 hours'
FROM users u WHERE u.email = 'admin@rsjuris.com'
LIMIT 1
ON CONFLICT (id) DO NOTHING;