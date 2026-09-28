-- 1. Create Enums for Enquiries & Leads if they don't exist
DO $$ BEGIN
    CREATE TYPE enquirystatus AS ENUM ('NEW', 'UNDER_REVIEW', 'CONTACTED', 'CONVERTED_TO_LEAD', 'ARCHIVED', 'SPAM');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE leadstatus AS ENUM ('INTAKE', 'PRE_LITIGATION_REVIEW', 'RETAINED', 'IN_LITIGATION', 'SETTLED', 'CLOSED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE leadpriority AS ENUM ('URGENT', 'HIGH', 'MEDIUM', 'LOW');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE mattertype AS ENUM (
        'CORPORATE_COMMERCIAL',
        'CIVIL_LITIGATION',
        'CRIMINAL_DEFENSE',
        'PROPERTY_REAL_ESTATE',
        'FAMILY_MATRIMONIAL',
        'EMPLOYMENT_LABOUR',
        'BANKING_FINANCE',
        'IPR_COPYRIGHT',
        'ARBITRATION_ADR',
        'OTHER'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Create Enquiries Table
CREATE TABLE IF NOT EXISTS enquiries (
    id VARCHAR PRIMARY KEY,
    reference_number VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    matter_type VARCHAR(100) NOT NULL,
    summary TEXT NOT NULL,
    status enquirystatus NOT NULL DEFAULT 'NEW',
    ip_address VARCHAR(100),
    user_agent VARCHAR(500),
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_enquiries_ref ON enquiries(reference_number);
CREATE INDEX IF NOT EXISTS ix_enquiries_status ON enquiries(status);
CREATE INDEX IF NOT EXISTS ix_enquiries_created_at ON enquiries(created_at);

-- 3. Create Leads Table
CREATE TABLE IF NOT EXISTS leads (
    id VARCHAR PRIMARY KEY,
    lead_number VARCHAR(100) UNIQUE NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    client_email VARCHAR(255) NOT NULL,
    client_phone VARCHAR(50) NOT NULL,
    alternate_phone VARCHAR(50),
    audience VARCHAR(50) NOT NULL DEFAULT 'BUSINESS',
    practice_area VARCHAR(150) NOT NULL,
    case_title VARCHAR(255) NOT NULL,
    case_description TEXT NOT NULL,
    court_forum VARCHAR(150),
    opposing_party VARCHAR(255),
    case_filing_number VARCHAR(100),
    claim_value VARCHAR(100),
    priority leadpriority NOT NULL DEFAULT 'MEDIUM',
    status leadstatus NOT NULL DEFAULT 'INTAKE',
    enquiry_id VARCHAR REFERENCES enquiries(id) ON DELETE SET NULL,
    assigned_to_id VARCHAR REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_leads_number ON leads(lead_number);
CREATE INDEX IF NOT EXISTS ix_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS ix_leads_priority ON leads(priority);
CREATE INDEX IF NOT EXISTS ix_leads_practice_area ON leads(practice_area);

-- 4. Create Lead Remarks Table
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