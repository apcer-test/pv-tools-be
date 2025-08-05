# User table seeding

sql_for_tenant = '''
INSERT INTO tenant (id, secret_key, is_active, created_at, updated_at, deleted_at, created_by, updated_by, deleted_by)
VALUES
('03K1D6VT352M83632KFQA55DF1', 'secret_key', TRUE, NOW(), NOW(), NULL, NULL, NULL, NULL);
'''

sql_for_tenant_users = '''
INSERT INTO tenant_users (tenant_id, user_id, role, created_at, updated_at, deleted_at, created_by, updated_by, deleted_by)
VALUES
('03K1D6VT352M83632KFQA55DF1', '01K1D6VT352M83632KFQA55DF1', 'ADMIN', NOW(), NOW(), NULL, NULL, NULL, NULL);
'''

sql_for_create_admin = '''
INSERT INTO users (first_name, last_name, email, password, phone, role, id, created_at, updated_at, deleted_at, created_by, updated_by, deleted_by)
VALUES
('admin',
 'admin', 
 'admin@admin.com', 
 '$2b$12$m08HRslO4jwlf04qRolf9eLsd.FLDHhjP5Dlen2WTQi6aJZkyeixa', 
 '+910000000000', 
 'ADMIN',
 '01K1D6VT352M83632KFQA55DF1',
 NOW(),
 NOW(),
 NULL,
 NULL,
 NULL,
 NULL
 );
'''
#the default password is "Admin@123" we need to change it based on hashing algorithm


# AI-related tables seeding (doc_type and fallback_chain)

# 1. Doc Type
sql_for_doc_type = '''
INSERT INTO doc_type (id, code, description, created_at, updated_at, deleted_at)
VALUES 
    ('01K1AGGAEZAC16072DAMTBSXF2', 'CIOMS', 'CIOMS', NOW(), NOW(), NULL),
    ('01K1AGGAEZS0GMM34AFPYRDX91', 'IRMS', 'IRMS', NOW(), NOW(), NULL),
    ('01K1AGGAEZY15XAP04GFP43ZTC', 'AER', 'AER', NOW(), NOW(), NULL),
    ('01K1AGGAEZRYPYTF3SRAR8NB55', 'MEDWATCH', 'MEDWATCH', NOW(), NOW(), NULL),
    ('01K1AGGAEZ5EKR9J8NSFMQGWAQ', 'LFTA', 'LFTA', NOW(), NOW(), NULL),
    ('01K1AGGAEZQNCFTQXK3QV4R2NG', 'YELLOW_CARD', 'YELLOW_CARD', NOW(), NOW(), NULL);
'''

# 2. Fallback Chain
sql_for_fallback_chain = '''
INSERT INTO fallback_chain (id, name, max_total_retries, is_active, created_at, updated_at, deleted_at)
VALUES (
    '01K1AGGAEZAGKMS9YMZYM1YYWT',
    'Default AI Extraction Chain',
    3,
    TRUE,
    NOW(),
    NOW(),
    NULL
);
'''