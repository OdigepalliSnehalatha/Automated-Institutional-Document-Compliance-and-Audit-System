-- ==============================================================================
-- MIGRATION: 002_professional_compliance_system.sql
-- Automated Institutional Compliance & Document Audit System
-- Professional Academic Governance, Question Paper Management & Validation Schema
-- ==============================================================================

-- 1. Academic Years
CREATE TABLE IF NOT EXISTS academic_years (
    id SERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    year_name VARCHAR(50) NOT NULL,
    is_current BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(institution_id, year_name)
);

-- 2. Semesters
CREATE TABLE IF NOT EXISTS semesters (
    id SERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    semester_name VARCHAR(50) NOT NULL,
    semester_code VARCHAR(20) NOT NULL,
    semester_number INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(institution_id, semester_code)
);

-- 3. Courses / Subjects
CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    semester_id INTEGER REFERENCES semesters(id) ON DELETE SET NULL,
    academic_year_id INTEGER REFERENCES academic_years(id) ON DELETE SET NULL,
    course_code VARCHAR(50) NOT NULL,
    course_name VARCHAR(255) NOT NULL,
    credits INTEGER DEFAULT 3,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(institution_id, department_id, course_code)
);

-- 4. Faculty Course Assignments
CREATE TABLE IF NOT EXISTS faculty_course_assignments (
    id SERIAL PRIMARY KEY,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    faculty_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    academic_year_id INTEGER REFERENCES academic_years(id) ON DELETE SET NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(course_id, faculty_id, academic_year_id)
);

-- 5. Examination Categories
CREATE TABLE IF NOT EXISTS exam_categories (
    id SERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institution(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL,
    max_marks INTEGER DEFAULT 30,
    is_mandatory BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 1,
    UNIQUE(institution_id, code)
);

-- 6. Add new columns to documents table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'documents' AND column_name = 'course_id') THEN
        ALTER TABLE documents ADD COLUMN course_id INTEGER REFERENCES courses(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'documents' AND column_name = 'academic_year_id') THEN
        ALTER TABLE documents ADD COLUMN academic_year_id INTEGER REFERENCES academic_years(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'documents' AND column_name = 'semester_id') THEN
        ALTER TABLE documents ADD COLUMN semester_id INTEGER REFERENCES semesters(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'documents' AND column_name = 'exam_category') THEN
        ALTER TABLE documents ADD COLUMN exam_category VARCHAR(50);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'documents' AND column_name = 'file_hash') THEN
        ALTER TABLE documents ADD COLUMN file_hash VARCHAR(64);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'documents' AND column_name = 'file_size') THEN
        ALTER TABLE documents ADD COLUMN file_size BIGINT DEFAULT 0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'documents' AND column_name = 'validation_status') THEN
        ALTER TABLE documents ADD COLUMN validation_status VARCHAR(50) DEFAULT 'PENDING';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'documents' AND column_name = 'approval_status') THEN
        ALTER TABLE documents ADD COLUMN approval_status VARCHAR(50) DEFAULT 'PENDING';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'documents' AND column_name = 'approved_by') THEN
        ALTER TABLE documents ADD COLUMN approved_by INTEGER REFERENCES users(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'documents' AND column_name = 'approval_comments') THEN
        ALTER TABLE documents ADD COLUMN approval_comments TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'documents' AND column_name = 'approved_at') THEN
        ALTER TABLE documents ADD COLUMN approved_at TIMESTAMP;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'documents' AND column_name = 'version') THEN
        ALTER TABLE documents ADD COLUMN version INTEGER DEFAULT 1;
    END IF;
END $$;

-- 7. Document Versions (Audit History & Version Control)
CREATE TABLE IF NOT EXISTS document_versions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_hash VARCHAR(64),
    file_size BIGINT,
    uploaded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validation_status VARCHAR(50),
    validation_result JSONB,
    approval_status VARCHAR(50),
    approval_comments TEXT,
    change_summary TEXT
);

-- 8. Audit Findings & Decisions
CREATE TABLE IF NOT EXISTS audit_findings (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    finding_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) DEFAULT 'MEDIUM',
    description TEXT NOT NULL,
    recommendation TEXT,
    status VARCHAR(50) DEFAULT 'OPEN',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. Activity Logs
CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    institution_id INTEGER REFERENCES institution(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    details JSONB,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_docs_course ON documents(course_id);
CREATE INDEX IF NOT EXISTS idx_docs_exam_cat ON documents(exam_category);
CREATE INDEX IF NOT EXISTS idx_docs_val_status ON documents(validation_status);
CREATE INDEX IF NOT EXISTS idx_docs_app_status ON documents(approval_status);
CREATE INDEX IF NOT EXISTS idx_courses_dept ON courses(department_id);
CREATE INDEX IF NOT EXISTS idx_faculty_assign ON faculty_course_assignments(faculty_id);
