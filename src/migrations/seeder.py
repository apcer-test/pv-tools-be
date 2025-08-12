from ulid import ULID

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


# User Management Tables Seeding

# 1. Client
client_id = str(ULID())
user_management_sql = f"""
INSERT INTO clients (id, name, code, slug, description, meta_data, is_active, created_at, updated_at, deleted_at)
VALUES ('{client_id}', 'Azurity Pharmaceuticals, Inc.', 'AZ', 'azurity', NULL, NULL, TRUE, NOW(), NOW(), NULL);
"""

# 2. Permissions
permissions = [
    {"name": "View", "slug": "view"},
    {"name": "Edit", "slug": "edit"},
    {"name": "Lock", "slug": "lock"},
    {"name": "Delete", "slug": "delete"},
    {"name": "Audit", "slug": "audit"},
]
permission_ids = {}
for p in permissions:
    pid = str(ULID())
    permission_ids[p["slug"]] = pid
    user_management_sql += f"""
INSERT INTO permissions (id, name, slug, description, meta_data, client_id, created_at, updated_at, deleted_at)
VALUES ('{pid}', '{p["name"]}', '{p["slug"]}', NULL, NULL, '{client_id}', NOW(), NOW(), NULL);
"""

# 3. User Types
user_types = [
    {"name": "OwnDataAccess", "slug": "own_data_access"},
    {"name": "TeamDataAccess", "slug": "team_data_access"},
    {"name": "FullDataAccess", "slug": "full_data_access"},
    {"name": "ReadOnlyDataAccess", "slug": "read_only_data_access"},
]
user_type_ids = {}
for ut in user_types:
    utid = str(ULID())
    user_type_ids[ut["slug"]] = utid
    user_management_sql += f"""
INSERT INTO user_type (id, name, slug, description, meta_data, client_id, created_at, updated_at, deleted_at)
VALUES ('{utid}', '{ut["name"]}', '{ut["slug"]}', NULL, NULL, '{client_id}', NOW(), NOW(), NULL);
"""

# 4. Roles
role_id = str(ULID())
user_management_sql += f"""
INSERT INTO roles (id, name, slug, description, meta_data, client_id, created_at, updated_at, deleted_at)
VALUES ('{role_id}', 'Super Admin', 'super_admin', NULL, NULL, '{client_id}', NOW(), NOW(), NULL);
"""

# 5. Modules and hierarchy
modules = [
    {"name": "Case", "slug": "case"},
    {"name": "Case Management", "slug": "case_management", "parent_slug": "case"},
    {"name": "Role", "slug": "role"},
    {"name": "Role Management", "slug": "role_management", "parent_slug": "role"},
    {"name": "User", "slug": "user"},
    {"name": "User Management", "slug": "user_management", "parent_slug": "user"},
    {"name": "Setup", "slug": "setup"},
    {"name": "AER Numbering", "slug": "aer_numbering", "parent_slug": "setup"},
    {"name": "Code List", "slug": "code_list", "parent_slug": "setup"},
    {"name": "Null Flavour List", "slug": "null_flavour_list", "parent_slug": "setup"},
]
module_ids = {}
# First pass: assign IDs
for m in modules:
    module_ids[m["slug"]] = str(ULID())
# Second pass: insert with parent ID if any
for m in modules:
    parent_id = f"'{module_ids[m['parent_slug']]}'" if "parent_slug" in m else "NULL"
    user_management_sql += f"""
INSERT INTO modules (id, name, slug, description, meta_data, client_id, parent_module_id, created_at, updated_at, deleted_at)
VALUES ('{module_ids[m["slug"]]}', '{m["name"]}', '{m["slug"]}', NULL, NULL, '{client_id}', {parent_id}, NOW(), NOW(), NULL);
"""

# 6. Module Permission Links
for mod_slug, mod_id in module_ids.items():
    for perm_slug, perm_id in permission_ids.items():
        link_id = str(ULID())
        user_management_sql += f"""
INSERT INTO module_permission_link (id, client_id, module_id, permission_id, created_at, updated_at, deleted_at)
VALUES ('{link_id}', '{client_id}', '{mod_id}', '{perm_id}', NOW(), NOW(), NULL);
"""

# 7. Role Module Permission Links
for mod_slug, mod_id in module_ids.items():
    for perm_slug, perm_id in permission_ids.items():
        link_id = str(ULID())
        user_management_sql += f"""
INSERT INTO role_module_permission_link (id, client_id, role_id, module_id, permission_id, created_at, updated_at, deleted_at)
VALUES ('{link_id}', '{client_id}', '{role_id}', '{mod_id}', '{perm_id}', NOW(), NOW(), NULL);
"""

# 8. Super Admin User
user_id = str(ULID())
user_type_id = user_type_ids["full_data_access"]  # assign FullDataAccess
user_management_sql += f"""
INSERT INTO users (id, username, first_name, last_name, email, phone, user_type_id, description, meta_data, is_active, created_at, updated_at, deleted_at, created_by, updated_by, deleted_by)
VALUES ('{user_id}', 'super-admin', 'super', 'admin', 'super-admin@azurity.com', '+910000000000', '{user_type_id}', NULL, NULL, TRUE, NOW(), NOW(), NULL, NULL, NULL, NULL);
"""

# 9. User Role Link
user_role_link_id = str(ULID())
user_management_sql += f"""
INSERT INTO user_role_link (id, client_id, user_id, role_id, created_by, updated_by, deleted_by, created_at, updated_at, deleted_at)
VALUES ('{user_role_link_id}', '{client_id}', '{user_id}', '{role_id}', NULL, NULL, NULL, NOW(), NOW(), NULL);
"""

# 10. Update created_by and updated_by in all tables
user_management_sql += f"""
UPDATE clients SET created_by = '{user_id}', updated_by = '{user_id}' WHERE id = '{client_id}';
UPDATE permissions SET created_by = '{user_id}', updated_by = '{user_id}' WHERE client_id = '{client_id}';
UPDATE user_type SET created_by = '{user_id}', updated_by = '{user_id}' WHERE client_id = '{client_id}';
UPDATE roles SET created_by = '{user_id}', updated_by = '{user_id}' WHERE client_id = '{client_id}';
UPDATE modules SET created_by = '{user_id}', updated_by = '{user_id}' WHERE client_id = '{client_id}';
UPDATE module_permission_link SET created_by = '{user_id}', updated_by = '{user_id}' WHERE client_id = '{client_id}';
UPDATE role_module_permission_link SET created_by = '{user_id}', updated_by = '{user_id}' WHERE client_id = '{client_id}';
UPDATE user_role_link SET created_by = '{user_id}', updated_by = '{user_id}' WHERE client_id = '{client_id}';
UPDATE users SET created_by = '{user_id}', updated_by = '{user_id}' WHERE id = '{user_id}';
"""


# Tenant Management Tables Seeding

# 1. Tenant
tenant_id = str(ULID())
sql_for_tenant = f'''
INSERT INTO tenant (id, secret_key, is_active, created_at, updated_at, deleted_at, created_by, updated_by, deleted_by)
VALUES
('{tenant_id}', 'secret_key', TRUE, NOW(), NOW(), NULL, '{user_id}', '{user_id}', NULL);
'''

# 2. Tenant Users
tenant_user_id = str(ULID())
sql_for_tenant_users = f'''
INSERT INTO tenant_users (tenant_id, user_id, role, created_at, updated_at, deleted_at, created_by, updated_by, deleted_by)
VALUES
('{tenant_id}', '{user_id}', 'ADMIN', NOW(), NOW(), NULL, '{user_id}', '{user_id}', NULL);
'''
