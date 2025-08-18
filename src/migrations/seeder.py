from ulid import ULID
import slugify

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
client_slug = slugify.slugify("Azurity Pharmaceuticals, Inc.")
user_management_sql = f"""
INSERT INTO clients (id, name, code, slug, description, meta_data, is_active, created_at, updated_at, deleted_at)
VALUES ('{client_id}', 'Azurity Pharmaceuticals, Inc.', 'AZ', '{client_slug}', NULL, NULL, TRUE, NOW(), NOW(), NULL);
"""

# 2. Permissions
permissions = [
    {"name": "View", "slug": slugify.slugify("View")},
    {"name": "Edit", "slug": slugify.slugify("Edit")},
    {"name": "Lock", "slug": slugify.slugify("Lock")},
    {"name": "Delete", "slug": slugify.slugify("Delete")},
    {"name": "Audit", "slug": slugify.slugify("Audit")},
]
permission_ids = {}
for p in permissions:
    pid = str(ULID())
    permission_ids[p["slug"]] = pid
    user_management_sql += f"""
INSERT INTO permissions (id, name, slug, description, meta_data, created_at, updated_at, deleted_at)
VALUES ('{pid}', '{p["name"]}', '{p["slug"]}', NULL, NULL, NOW(), NOW(), NULL);
"""



# 4. Roles
roles = [
    {"name": "Super Admin", "slug": slugify.slugify("Super Admin")},
]

role_ids = {}
for r in roles:
    rid = str(ULID())
    role_ids[r["slug"]] = rid
    user_management_sql += f"""
INSERT INTO roles (id, name, slug, description, meta_data, is_active, created_at, updated_at, deleted_at)
VALUES ('{rid}', '{r["name"]}', '{r["slug"]}', NULL, NULL, TRUE, NOW(), NOW(), NULL);
"""

# 5. Modules and hierarchy
modules = [
    {"name": "Clients", "slug": "clients"},
    {"name": "Client Management", "slug": slugify.slugify("Client Management"), "parent_slug": "clients"},
    {"name": "Roles", "slug": "roles"},
    {"name": "Role Management", "slug": slugify.slugify("Role Management"), "parent_slug": "roles"},
    {"name": "User", "slug": "user"},
    {"name": "User Management", "slug": slugify.slugify("User Management"), "parent_slug": "user"},
    {"name": "Setup", "slug": "setup"},
    {"name": "AER Numbering", "slug": slugify.slugify("AER Numbering"), "parent_slug": "setup"},
    {"name": "Code List", "slug": slugify.slugify("Code List"), "parent_slug": "setup"},
    {"name": "Null Flavour List", "slug": slugify.slugify("Null Flavour List"), "parent_slug": "setup"},
]

module_ids = {}
# First pass: assign IDs
for m in modules:
    module_ids[m["slug"]] = str(ULID())
# Second pass: insert with parent ID if any
for m in modules:
    parent_id = f"'{module_ids[m['parent_slug']]}'" if "parent_slug" in m else "NULL"
    user_management_sql += f"""
INSERT INTO modules (id, name, slug, description, meta_data, parent_module_id, created_at, updated_at, deleted_at)
VALUES ('{module_ids[m["slug"]]}', '{m["name"]}', '{m["slug"]}', NULL, NULL, {parent_id}, NOW(), NOW(), NULL);
"""

# 6. Module Permission Links (Only for child modules)
for mod_slug, mod_id in module_ids.items():
    # Check if this module has a parent (i.e., it's a child module)
    mod_data = next((m for m in modules if m["slug"] == mod_slug), None)
    if mod_data and "parent_slug" in mod_data:
        # Only link permissions to child modules (parent_slug should not be NULL)
        for perm_slug, perm_id in permission_ids.items():
            link_id = str(ULID())
            user_management_sql += f"""
INSERT INTO module_permission_link (id, module_id, permission_id, created_at, updated_at, deleted_at)
VALUES ('{link_id}', '{mod_id}', '{perm_id}', NOW(), NOW(), NULL);
"""
        
# 7. Role Module Permission Links (Only for child modules)
for role_slug, role_id in role_ids.items():
    for mod_slug, mod_id in module_ids.items():
        # Check if this module has a parent (i.e., it's a child module)
        mod_data = next((m for m in modules if m["slug"] == mod_slug), None)
        if mod_data and "parent_slug" in mod_data:
            # Only link permissions to child modules (parent_slug should not be NULL)
            for perm_slug, perm_id in permission_ids.items():
                link_id = str(ULID())
                user_management_sql += f"""
INSERT INTO role_module_permission_link (id, role_id, module_id, permission_id, created_at, updated_at, deleted_at)
VALUES ('{link_id}', '{role_id}', '{mod_id}', '{perm_id}', NOW(), NOW(), NULL);
"""

# 8. Super Admin User
user_id = str(ULID())
user_management_sql += f"""
INSERT INTO users (id, first_name, last_name, email, phone, description, meta_data, is_active, created_at, updated_at, deleted_at, created_by, updated_by, deleted_by)
VALUES ('{user_id}', 'super', 'admin', 'jigarv@webelight.co.in', '+910000000000', NULL, NULL, TRUE, NOW(), NOW(), NULL, NULL, NULL, NULL);
"""

# 9. User Role Link
user_role_link_id = str(ULID())
user_management_sql += f"""
INSERT INTO user_role_link (id, client_id, user_id, role_id, created_by, updated_by, deleted_by, created_at, updated_at, deleted_at)
VALUES ('{user_role_link_id}', '{client_id}', '{user_id}', '{role_ids["super-admin"]}', NULL, NULL, NULL, NOW(), NOW(), NULL);
"""

# 10. Update created_by and updated_by in all tables
user_management_sql += f"""
UPDATE clients SET created_by = '{user_id}', updated_by = '{user_id}' WHERE id = '{client_id}';
UPDATE permissions SET created_by = '{user_id}', updated_by = '{user_id}';

UPDATE roles SET created_by = '{user_id}', updated_by = '{user_id}';
UPDATE modules SET created_by = '{user_id}', updated_by = '{user_id}';
UPDATE module_permission_link SET created_by = '{user_id}', updated_by = '{user_id}';
UPDATE role_module_permission_link SET created_by = '{user_id}', updated_by = '{user_id}';
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
