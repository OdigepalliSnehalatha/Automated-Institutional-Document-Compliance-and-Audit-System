-- ============================================================
-- MIGRATION: 001_structural_system.sql
-- Automated Institutional Document Compliance and Audit System
-- ============================================================

-- 1. Ensure document_types table contains active types
CREATE TABLE IF NOT EXISTS document_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

INSERT INTO document_types (name, description, is_active)
VALUES 
    ('Course Structure', 'Institution-defined structural format for course syllabi and units', TRUE),
    ('Question Bank', 'Structural format for question banks (Units 1-5, Part A and Part B distribution)', TRUE),
    ('Question Paper', 'Structural format for Mid and Semester Examination Question Papers', TRUE)
ON CONFLICT (name) DO UPDATE 
SET is_active = TRUE, description = EXCLUDED.description;

-- 2. Ensure document_formats table
CREATE TABLE IF NOT EXISTS document_formats (
    id SERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    document_type_id INTEGER NOT NULL REFERENCES document_types(id) ON DELETE CASCADE,
    format_name VARCHAR(255) NOT NULL,
    instructions TEXT,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ensure department_id is nullable if it was NOT NULL
ALTER TABLE document_formats ALTER COLUMN department_id DROP NOT NULL;

-- 3. Ensure format_requirements table
CREATE TABLE IF NOT EXISTS format_requirements (
    id SERIAL PRIMARY KEY,
    format_id INTEGER NOT NULL REFERENCES document_formats(id) ON DELETE CASCADE,
    requirement_name VARCHAR(255) NOT NULL,
    requirement_type VARCHAR(100) NOT NULL,
    requirement_value TEXT,
    is_required BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 1
);

-- 4. Ensure documents table has all required columns
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    document_type_id INTEGER REFERENCES document_types(id) ON DELETE SET NULL,
    uploaded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analysis_status VARCHAR(50) DEFAULT 'PENDING',
    analysis_result JSONB,
    analyzed_at TIMESTAMP
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'documents' AND column_name = 'uploaded_by'
    ) THEN
        ALTER TABLE documents ADD COLUMN uploaded_by INTEGER REFERENCES users(id) ON DELETE SET NULL;
    END IF;
END $$;

-- 5. Ensure login_otps table
CREATE TABLE IF NOT EXISTS login_otps (
    id SERIAL PRIMARY KEY,
    institution_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    otp_hash TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    attempts INTEGER DEFAULT 0,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_dept ON documents(department_id);
CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(analysis_status);
CREATE INDEX IF NOT EXISTS idx_formats_dept ON document_formats(department_id);
CREATE INDEX IF NOT EXISTS idx_formats_type ON document_formats(document_type_id);
CREATE INDEX IF NOT EXISTS idx_login_otps_lookup ON login_otps(email, role, is_used);
