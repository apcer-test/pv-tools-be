"""Services for Users."""

import base64
import json
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from io import BytesIO
from typing import Annotated, Any

import qrcode
from fastapi import Depends, Path, Request
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from passlib.exc import InvalidTokenError
from pydantic import EmailStr
from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload

from apps.constants import JWTokenType
from apps.modules.schemas.response import ModuleResponse
from apps.roles.execeptions import RoleNotFoundError
from apps.roles.models import Roles
from apps.roles.services import RoleService
from apps.tenant_app_configs.exceptions import (
    AppMFANotEnabledError,
    TenantAppConfigNotFoundError,
)
from apps.tenant_app_configs.models.tenant_app_configs import TenantAppConfig
from apps.tenant_app_configs.schemas.response import TenantAppConfigResponse
from apps.tenant_app_configs.services.tenant_app_configs import TenantAppConfigService
from apps.tenant_apps.models import TenantApps
from apps.user_devices.models import UserDevices
from apps.user_devices.services import UserDeviceService
from apps.user_devices.utils import generate_device_fingerprint, get_device_metadata
from apps.user_sessions.services.user_session import UserSessionService
from apps.user_sub_types.execeptions import UserSubTypeNotFoundError
from apps.user_sub_types.models import UserSubTypes
from apps.user_types.constants import UserTypeSortBy
from apps.user_types.execeptions import UserTypeNotFoundError
from apps.user_types.models import UserTypes
from apps.users.constants import (
    UserAuthAction,
    UserDefaults,
    UserErrorMessage,
    UserMessage,
    UserRedisKeys,
    UserSortBy,
)
from apps.users.exceptions import (
    EmailAlreadyExistsError,
    GeneratePasswordError,
    InvalidPasswordError,
    LockAccountError,
    PasswordMatchedError,
    PhoneAlreadyExistsError,
    PhoneOrEmailRequiredError,
    UserAlreadyMFEnrolledError,
    UserMfaNotDisableError,
    UserMFANotSetupError,
    UserNotFoundError,
    WeakPasswordError,
)
from apps.users.models import PasswordHistory, UserRoleLink, Users
from apps.users.schemas.response import (
    BaseUserResponse,
    GenerateOTPResponse,
    ListUserResponse,
    LoginResponse,
    MFAEnableResponse,
    MFAResetResponse,
    MFASetupResponse,
    MFAVerifiedResponse,
    RoleResponse,
    UpdateUserResponse,
    UserResponse,
    UserSubTypeResponse,
    UserTypeResponse,
)
from apps.users.services.login_methods import LoginMethodService
from config import settings
from core.constants import ErrorMessage
from core.db import db_session, redis
from core.dependencies.auth import access_jwt, mfa_jwt, refresh_jwt
from core.exceptions import UnauthorizedError
from core.utils.crypto import CryptoUtil
from core.utils.datetime_utils import add_to_datetime, convert_to_utc, get_utc_now
from core.utils.hashing import hash_password, verify_password
from core.utils.mfa import create_totp_factory, is_user_mfa_required
from core.utils.password import strong_password
from core.utils.resolve_context_ids import get_context_ids_from_keys
from core.utils.schema import SuccessResponse
from apps.users.utils import get_jwt_additional_claims


class UserService:
    """Service with methods to set and get values."""

    def __init__(
        self,
        session: Annotated[AsyncSession, Depends(db_session)],
        tenant_key: Annotated[int | str, Path()],
        app_key: Annotated[int | str, Path()],
        role_service: Annotated[RoleService, Depends()],
        user_session_service: Annotated[UserSessionService, Depends()],
        user_device_service: Annotated[UserDeviceService, Depends()],
    ) -> None:
        self.session = session
        self.tenant_key = tenant_key
        self.app_key = app_key
        self.role_service = role_service
        self.tenant_id = None
        self.app_id = None
        self.user_session_service = user_session_service
        self.redis = redis
        self.user_device_service = user_device_service

    async def _resolve_context_ids(self) -> None:
        if self.tenant_id and self.app_id:
            return
        tenant_id, app_id = await get_context_ids_from_keys(
            session=self.session, tenant_key=self.tenant_key, app_key=self.app_key
        )
        self.tenant_id = tenant_id
        self.app_id = app_id

    def get_scopes_from_role(self, role: RoleResponse) -> list[dict[str, list[str]]]:
        """
        Given a role object, return a list of dicts with scopes and permissions.
        """
        scopes: list[dict[str, list[str]]] = []

        def process_module(module: ModuleResponse, scope_prefix: str = "") -> None:
            current_scope = module.name.lower().replace(" ", "-")
            full_scope = (
                f"{scope_prefix}:{current_scope}" if scope_prefix else current_scope
            )
            if hasattr(module, "permissions"):
                permissions = [
                    permission.name.lower().replace(" ", "-")
                    for permission in getattr(module, "permissions", [])
                ]
                if permissions:
                    scopes.append({"scope": full_scope, "permissions": permissions})
            for child in getattr(module, "child_modules", []):
                process_module(child, full_scope)

        for module in getattr(role, "modules", []):
            process_module(module)

        return scopes

    def get_merged_scopes_from_roles(
        self, roles: list[RoleResponse]
    ) -> list[dict[str, list[str]]]:
        """
        Given a list of role objects, return a merged
        list of dicts with scopes and combined permissions.
        """
        scope_permissions = defaultdict(set)

        def process_module(module: ModuleResponse, scope_prefix: str = "") -> None:
            current_scope = module.name.lower().replace(" ", "-")
            full_scope = (
                f"{scope_prefix}:{current_scope}" if scope_prefix else current_scope
            )
            permissions = [
                permission.name.lower().replace(" ", "-")
                for permission in getattr(module, "permissions", [])
            ]
            scope_permissions[full_scope].update(permissions)
            for child in getattr(module, "child_modules", []):
                process_module(child, full_scope)

        for role in roles:
            for module in getattr(role, "modules", []):
                process_module(module)

        return [
            {"scope": scope, "permissions": sorted(perms)}
            for scope, perms in scope_permissions.items()
        ]

    async def _get_tenant_app_config(
        self, tenant_id: int, app_id: int
    ) -> TenantAppConfigResponse:
        app_config = await TenantAppConfigService(
            session=self.session, tenant_key=tenant_id, app_key=app_id
        ).get_app_config()
        if not app_config:
            raise TenantAppConfigNotFoundError
        return app_config

    async def login(  # noqa: C901, PLR0912, PLR0915
        self,
        username: str | None,
        phone: str | None,
        email: str | None,
        password: str | None,
        otp: str | None,
        request: Request,
        app_config: TenantAppConfig,
    ) -> LoginResponse:
        """Handles user login for a specific tenant and application.

        Args:
          - tenant_key (int/str): The tenant_key means tenant_id or name.
          This is required.
          - app_key (int/str): The app_key means app_id or name. This is required.
          - username (str | None): The username of the user.
          - phone (str | None): The phone number of the user.
          - email (str | None): The email address of the user.
          - password (str | None): The password of the user.
          - otp (str | None): The one-time password (OTP) provided by the user.

        Returns:
          - LoginResponse: A LoginResponse containing the login response.

        Raises:
         - UserNotFoundError: If no user with the provided username is found.
         - GeneratePasswordError: If the password cannot be generated.
         - LockAccountError: If the user's account is locked due to expiring password.
         - InvalidCredentialsError: If the provided password is incorrect.

        """

        await self._resolve_context_ids()

        user_filters = [
            Users.tenant_id == self.tenant_id,
            Users.app_id == self.app_id,
            Users.is_active.is_(True),
            Users.deleted_at.is_(None),
        ]

        if username is not None:
            user_filters.append(Users.username == username)
        if phone is not None:
            user_filters.append(Users.phone == phone)
        if email is not None:
            user_filters.append(Users.email == email)

        # Fetch user
        user = await self.session.scalar(
            select(Users)
            .options(
                load_only(
                    Users.id,
                    Users.ulid,
                    Users.username,
                    Users.email,
                    Users.password,
                    Users.password_exp,
                    Users.mfa_enabled,
                    Users.mfa_enrolled_at,
                ),
                selectinload(Users.roles),
            )
            .where(*user_filters)
        )
        if not user:
            raise UserNotFoundError

        if user.password is None:
            raise GeneratePasswordError

        if user.password_exp and convert_to_utc(user.password_exp) < get_utc_now():
            raise LockAccountError

        await LoginMethodService.is_verified_login(
            login_methods=app_config.login_methods,
            user_ulid=user.ulid,
            password=password,
            hashed_password=user.password,
            otp=otp,
            phone=phone,
            email=email,
            login_throttle_attempts=app_config.login_throttle_attempts,
            login_throttle_window_seconds=app_config.login_throttle_window_seconds,
            max_failed_logins=app_config.max_failed_logins,
            lockout_duration_minutes=app_config.lockout_duration_minutes,
        )
        if app_config.monthly_password_change_enable:
            password_history_entry = await self.session.scalar(
                select(PasswordHistory)
                .where(PasswordHistory.user_id == user.id)
                .order_by(desc(PasswordHistory.created_at))
            )
            if password_history_entry:
                password_created_at = password_history_entry.created_at
                if password_created_at.replace(tzinfo=UTC) + timedelta(
                    days=app_config.password_change_interval_days
                ) <= datetime.now(UTC):
                    decoded_jwt_secret = CryptoUtil().decrypt(app_config.jwt_secret)
                    action_token_kwargs = {
                        "subject": str(user.id),
                        "jwt_secret": decoded_jwt_secret,
                        "jwt_algorithm": app_config.jwt_algorithm,
                        "exp": UserDefaults.PASSWORD_REMINDER_TOKEN_EXPIRE,
                        "type": JWTokenType.ACCESS,
                        "purpose": UserAuthAction.CHANGE_PASSWORD,
                    }
                    action_token = access_jwt.encode(**action_token_kwargs)

                    return LoginResponse(
                        access_token=action_token,
                        refresh_token=None,
                        mfa_token=None,
                        user_id=user.id,
                        session_id=None,
                        username=user.username,
                        roles=[],
                        scopes={},
                        message=UserMessage.PASSWORD_REMINDER_MONTHLY,
                        action=UserAuthAction.CHANGE_PASSWORD,
                    )

        roles_slug = [role.slug for role in user.roles]
        additional_claims = get_jwt_additional_claims(
            additional_claims=app_config.jwt_claims,
            email=user.email,
            is_mfa_enabled=user.mfa_enabled,
            roles=roles_slug,
        )
        decoded_jwt_secret = CryptoUtil().decrypt(app_config.jwt_secret)
        access_token_exp = app_config.access_token_ttl
        refresh_token_exp = app_config.refresh_token_ttl
        access_token_kwargs = {
            "subject": str(user.id),
            "jwt_secret": decoded_jwt_secret,
            "jwt_algorithm": app_config.jwt_algorithm,
            "exp": access_token_exp,
            "type": JWTokenType.ACCESS,
            **additional_claims.model_dump(exclude_none=True),
        }

        refresh_token_kwargs = {
            "subject": str(user.id),
            "jwt_secret": decoded_jwt_secret,
            "jwt_algorithm": app_config.jwt_algorithm,
            "exp": refresh_token_exp,
            "type": JWTokenType.REFRESH,
            **additional_claims.model_dump(exclude_none=True),
        }

        mfa_token_kwargs = {
            "subject": str(user.id),
            "jwt_secret": decoded_jwt_secret,
            "jwt_algorithm": app_config.jwt_algorithm,
            "exp": settings.MFA_TOKEN_EXP,
            "type": JWTokenType.MFA,
        }

        session_id = None
        device_token = request.headers.get("device-token", "")
        is_app_mfa_required = app_config.mfa_required or False
        is_app_mfa_enabled = app_config.mfa_enabled or False
        is_user_mfa_enabled = user.mfa_enabled or False
        mfa_expires_at = get_utc_now()
        action = None
        if device_token:
            device_metadata = await get_device_metadata(request)
            # Create the user device in DB
            user_device = await self.user_device_service.create_user_device(
                session=self.session,
                user_id=user.id,
                tenant_id=self.tenant_id,
                app_id=self.app_id,
                device_metadata=device_metadata,
                device_token=device_token,
            )
            mfa_expires_at = user_device.mfa_expires_at
            # Check if MFA is required
            mfa_action = is_user_mfa_required(
                is_app_mfa_required=is_app_mfa_required,
                is_app_mfa_enabled=is_app_mfa_enabled,
                is_user_mfa_enabled=is_user_mfa_enabled,
                mfa_expires_at=mfa_expires_at,
                mfa_enrolled_at=user.mfa_enrolled_at,
            )

            # Check if MFA is required
            if mfa_action:
                action = mfa_action
            elif app_config.session_management_enabled:
                # Create the user session in DB
                session_id = await self.user_session_service.create_session(
                    session=self.session,
                    user_id=user.id,
                    tenant_id=self.tenant_id,
                    app_id=self.app_id,
                    app_config=app_config,
                    device_metadata=device_metadata,
                    device_fingerprint=user_device.device_fingerprint,
                    device_id=user_device.device_id,
                )
                access_token_kwargs["session_id"] = session_id
                refresh_token_kwargs["session_id"] = session_id
                mfa_token_kwargs["session_id"] = session_id

        access_token = None
        refresh_token = None
        mfa_token = None
        # Generate tokens
        if action in (UserAuthAction.MFA_VERIFY, UserAuthAction.MFA_SETUP):
            mfa_token_kwargs["purpose"] = action
            mfa_token = mfa_jwt.encode(**mfa_token_kwargs)
        else:
            access_token = access_jwt.encode(**access_token_kwargs)
            refresh_token = refresh_jwt.encode(**refresh_token_kwargs)

        scope_permissions_map = {}
        if not action:
            # Join roles for this user
            role_ids = [link.id for link in user.roles]
            roles = []
            scopes = []
            if role_ids:
                try:
                    roles = await self.role_service.get_roles_by_ids(
                        role_ids, self.tenant_id, self.app_id
                    )
                    scopes = self.get_merged_scopes_from_roles(roles)
                except RoleNotFoundError:
                    scopes = []

            scope_permissions_map = {
                entry["scope"]: entry.get("permissions", [])
                for entry in scopes
                if entry.get("permissions")
            }
            scopes_key = UserRedisKeys.scopes_key(
                tenant_id=self.tenant_id, app_id=self.app_id, user_id=user.id
            )
            await redis.set(
                scopes_key,
                json.dumps(scope_permissions_map),
                ex=UserDefaults.REDIS_USER_SCOPES_TTL,
            )

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            mfa_token=mfa_token,
            user_id=user.id,
            session_id=session_id,
            username=user.username,
            roles=roles_slug,
            scopes=scope_permissions_map,
            action=action,
            message=UserMessage.LOGIN_SUCCESS,
        )

    async def logout_user(self, user_id: int, session_id: str) -> None:
        """
        Logs out the currently authenticated user by invalidating their session and
        clearing authentication-related cookies.

        Args:
          - tenant_key (int/str): The tenant_key means tenant_id or name. This is required.
          - app_key (int/str): The app_key means app_id or name. This is required.

        Returns:
          - dict: A dictionary containing a message indicating successful logout.
        """

        await self._resolve_context_ids()

        await self.user_session_service.revoke_session(
            user_id=user_id,
            tenant_id=self.tenant_id,
            app_id=self.app_id,
            session_id=session_id,
        )

    async def create_user(
        self,
        tenant_app_config: TenantAppConfig,
        username: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        password: str | None = None,
        role_ids: list[int] | None = None,
        type_id: int | None = None,
        subtype_id: int | None = None,
        description: str | None = None,
        user_metadata: dict | None = None,
    ) -> BaseUserResponse:
        """
        Creates a new user with the provided information.

         Args:
          - tenant_key (int/str): The tenant_key means tenant_id or name. This is required.
          - app_key (int/str): The app_key means app_id or name. This is required.
          - username (str | None): The username of the user.
          - phone (str | None): The phone number of the user.
          - email (str | None): The email address of the user.
          - role_ids (list[int] | None) : List of role IDs to assign to the user.
          - type_id (int | None) : The Type ID of the user.
          - subtype_id (int | None) : The Subtype ID of the user.
          - password (str): The password of the user.

        Returns:
          - BaseUserResponse: A response containing the created user's basic information.

        Raises:
          - WeakPasswordError: If the provided password is weak.
          - PhoneAlreadyExistsError: If the provided phone number already exists.
          - EmailAlreadyExistsError: If the provided email address already exists.
          - RoleNotFoundError: If any of the provided role IDs do not exist.
          - UserTypeNotFoundError: If the provided type ID does not exist.
          - UserSubTypeNotFoundError: If the provided subtype ID does not exist.

        """

        if role_ids is None:
            role_ids = []
        await self._resolve_context_ids()

        if password:
            strong_pass = await strong_password(
                password, db=self.session, app_id=self.app_id, tenant_id=self.tenant_id
            )
            if not strong_pass:
                raise WeakPasswordError

        existing_user = await self.session.scalar(
            select(Users)
            .options(load_only(Users.phone, Users.email, Users.username))
            .where(
                and_(
                    Users.tenant_id == self.tenant_id,
                    Users.app_id == self.app_id,
                    or_(
                        and_(Users.phone == phone, Users.phone.is_not(None)),
                        and_(Users.email == email, Users.email.is_not(None)),
                    ),
                    Users.deleted_at.is_(None),
                )
            )
        )
        if existing_user:
            if phone and existing_user.phone == phone:
                raise PhoneAlreadyExistsError
            if email and existing_user.email == email:
                raise EmailAlreadyExistsError

        if len(role_ids) > 0:
            existing_roles_result = await self.session.scalars(
                select(Roles)
                .options(load_only(Roles.id))
                .where(
                    and_(
                        Roles.tenant_id == self.tenant_id,
                        Roles.app_id == self.app_id,
                        Roles.id.in_(role_ids),
                        Roles.deleted_at.is_(None),
                    )
                )
            )
            existing_roles = list(existing_roles_result)
            if len(existing_roles) != len(role_ids):
                raise RoleNotFoundError

        if type_id:
            existing_usertype = await self.session.scalar(
                select(UserTypes)
                .options(load_only(UserTypes.id))
                .where(
                    and_(
                        UserTypes.tenant_id == self.tenant_id,
                        UserTypes.app_id == self.app_id,
                        UserTypes.id == type_id,
                        UserTypes.deleted_at.is_(None),
                    )
                )
            )
            if not existing_usertype:
                raise UserTypeNotFoundError

        if subtype_id:
            existing_user_subtype = await self.session.scalar(
                select(UserSubTypes)
                .options(load_only(UserSubTypes.id))
                .where(
                    and_(
                        UserSubTypes.tenant_id == self.tenant_id,
                        UserSubTypes.app_id == self.app_id,
                        UserSubTypes.id == subtype_id,
                        UserSubTypes.deleted_at.is_(None),
                    )
                )
            )
            if not existing_user_subtype:
                raise UserSubTypeNotFoundError

        async with self.session.begin_nested():
            user = Users(
                username=username,
                phone=phone,
                email=email,
                password=hash_password(password) if password else None,
                type_id=type_id,
                subtype_id=subtype_id,
                app_id=self.app_id,
                tenant_id=self.tenant_id,
                description=description,
                user_metadata=user_metadata,
            )
            self.session.add(user)

        async with self.session.begin_nested():
            await self.session.refresh(user)

        if password:
            async with self.session.begin_nested():
                expires_at = None
                if tenant_app_config.password_expiry_days:
                    expires_at = add_to_datetime(
                        dt=get_utc_now(),
                        days=tenant_app_config.password_expiry_days,
                        to_utc=True,
                    )
                password_history = PasswordHistory(
                    user_id=user.id,
                    password=hash_password(password) if password else None,
                    app_id=self.app_id,
                    tenant_id=self.tenant_id,
                    expires_at=expires_at,
                )
                self.session.add(password_history)
                user.password_exp = expires_at

        async with self.session.begin_nested():
            for role_id in role_ids:
                user_role_link = UserRoleLink(
                    tenant_id=self.tenant_id,
                    app_id=self.app_id,
                    user_id=user.id,
                    role_id=role_id,
                )
                self.session.add(user_role_link)

        return BaseUserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            description=user.description,
            user_metadata=user.user_metadata,
            role_ids=role_ids,
            type_id=type_id,
            subtype_id=subtype_id,
            app_id=self.app_id,
            tenant_id=self.tenant_id,
        )

    async def get_all_users(  # noqa: C901
        self,
        page_param: Params,
        user: Users,
        user_ids: list[int] | None = None,
        username: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        role_name: str | None = None,
        type_name: str | None = None,
        sub_type_name: str | None = None,
        is_active: bool | None = None,
        sortby: UserTypeSortBy | None = None,
    ) -> Page[ListUserResponse]:
        """
        Retrieves a paginated list of users with optional filtering and sorting.

        Args:
          - tenant_key (int/str): The tenant_key means tenant_id or name. This is required.
          - app_key (int/str): The app_key means app_id or name. This is required.
          - param (Params): Pagination parameters including page number and size.
          - user_ids (list[int] | None): Optional list of user IDs to filter.
          - username (str | None): Optional filter by username.
          - email (str | None): Optional filter by email address.
          - phone (str | None): Optional filter by phone number.
          - role (str | None): Optional filter by user role.
          - type_name (str | None): Optional filter by user type.
          - sub_type (str | None): Optional filter by user sub_type.
          - is_active (bool | None): Optional filter by active status.
          - sortby (UserSortBy | None): Optional sorting field and direction.

        Returns:
          - Page[ListUserResponse]: A response containing the paginated list of users.

        Raises:
          - UserNotFoundError: If no user with the provided username is found.

        """
        await self._resolve_context_ids()

        query = (
            select(Users)
            .options(
                load_only(
                    Users.id,
                    Users.username,
                    Users.email,
                    Users.phone,
                    Users.type_id,
                    Users.subtype_id,
                    Users.app_id,
                    Users.is_active,
                    Users.description,
                    Users.user_metadata,
                ),
                selectinload(Users.type),
                selectinload(Users.subtype),
                selectinload(Users.roles),
            )
            .where(
                and_(
                    Users.tenant_id == self.tenant_id,
                    Users.app_id == self.app_id,
                    Users.deleted_at.is_(None),
                    Users.id != user.id,
                )
            )
        )

        if user_ids:
            query = query.where(Users.id.in_(user_ids))

        if username:
            query = query.where(Users.username.ilike(f"%{username}%"))

        if email:
            query = query.where(Users.email.ilike(f"%{email}%"))

        if phone:
            query = query.where(Users.phone.ilike(f"%{phone}%"))

        if role_name:
            query = query.join(Roles).where(Roles.name.ilike(f"%{role_name}%"))

        if type_name:
            query = query.join(UserTypes).where(UserTypes.name.ilike(f"%{type_name}%"))

        if sub_type_name:
            query = query.join(UserSubTypes).where(
                UserSubTypes.name.ilike(f"%{sub_type_name}%")
            )

        if is_active is not None:
            query = query.where(Users.is_active == is_active)

        if sortby in [UserSortBy.ROLE_DESC, UserSortBy.ROLE_ASC]:
            query = query.join(Roles, Users.roles.any(Roles.id == Roles.id))

        if sortby in [UserSortBy.USER_TYPE_DESC, UserSortBy.USER_TYPE_ASC]:
            query = query.join(UserTypes, Users.type_id == UserTypes.id)

        if sortby in [UserSortBy.USER_SUB_TYPE_DESC, UserSortBy.USER_SUB_TYPE_ASC]:
            query = query.join(UserSubTypes, Users.subtype_id == UserSubTypes.id)

        sort_options = {
            UserSortBy.NAME_DESC: Users.username.desc(),
            UserSortBy.NAME_ASC: Users.username.asc(),
            UserSortBy.EMAIL_DESC: Users.email.desc(),
            UserSortBy.EMAIL_ASC: Users.email.asc(),
            UserSortBy.ROLE_DESC: Roles.name.desc(),
            UserSortBy.ROLE_ASC: Roles.name.asc(),
            UserSortBy.USER_TYPE_DESC: UserTypes.name.desc(),
            UserSortBy.USER_TYPE_ASC: UserTypes.name.asc(),
            UserSortBy.USER_SUB_TYPE_DESC: UserSubTypes.name.desc(),
            UserSortBy.USER_SUB_TYPE_ASC: UserSubTypes.name.asc(),
        }

        sort_order = sort_options.get(sortby, Users.created_at.desc())
        query = query.order_by(sort_order)

        pagination = await paginate(self.session, query, page_param)
        items = [
            ListUserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                phone=user.phone,
                roles=[RoleResponse(id=role.id, name=role.name) for role in user.roles],
                type=UserTypeResponse(
                    id=user.type.id if user.type else None,
                    name=user.type.name if user.type else None,
                ),
                subtype=UserSubTypeResponse(
                    id=user.subtype.id if user.subtype else None,
                    name=user.subtype.name if user.subtype else None,
                ),
                app_id=user.app_id,
                is_active=user.is_active,
                description=user.description,
                user_metadata=user.user_metadata,
            )
            for user in pagination.items
        ]
        pagination.items = items
        return pagination

    async def get_user_by_id(self, user_id: int) -> ListUserResponse:
        """
        Retrieves detailed information about a specific user by their ID.

        Args:
            - tenant_key (int/str): The tenant_key means tenant_id or name.
            This is required.
            - app_key (int/str): The app_key means app_id or name. This is required.
            - user_id (int): The unique identifier of the user to retrieve.

        Returns:
            - ListUserResponse: A response containing the user's information.

        Raises:
            - UserNotFoundError: If no user with the provided username is found.

        """

        await self._resolve_context_ids()

        user = await self.session.scalar(
            select(Users)
            .options(
                load_only(
                    Users.id,
                    Users.username,
                    Users.email,
                    Users.phone,
                    Users.type_id,
                    Users.subtype_id,
                    Users.app_id,
                    Users.is_active,
                    Users.description,
                    Users.user_metadata,
                ),
                selectinload(Users.type),
                selectinload(Users.subtype),
                selectinload(Users.roles),
            )
            .where(
                and_(
                    Users.tenant_id == self.tenant_id,
                    Users.app_id == self.app_id,
                    Users.id == user_id,
                    Users.deleted_at.is_(None),
                )
            )
        )
        if not user:
            raise UserNotFoundError
        return ListUserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            description=user.description,
            user_metadata=user.user_metadata,
            roles=[RoleResponse(id=role.id, name=role.name) for role in user.roles],
            type=UserTypeResponse(
                id=user.type.id if user.type else None,
                name=user.type.name if user.type else None,
            ),
            subtype=UserSubTypeResponse(
                id=user.subtype.id if user.subtype else None,
                name=user.subtype.name if user.subtype else None,
            ),
            app_id=user.app_id,
            is_active=user.is_active,
        )

    async def change_user_status(self, user_id: int) -> Users:
        """
        Toggles the active status of a user by their ID.

        Args:
          - tenant_key (int/str): The tenant_key means tenant_id or name. This is required.
          - app_key (int/str): The app_key means app_id or name. This is required.
          - user_id (int): The ID of the user whose status is to be changed.

        Returns:
          - Users: A response indicating the user's updated status.

        Raises:
          - UserNotFoundError: If no user with the provided username is found.

        """

        await self._resolve_context_ids()

        existing_user = await self.session.scalar(
            select(Users)
            .options(
                load_only(
                    Users.id,
                    Users.username,
                    Users.phone,
                    Users.email,
                    Users.is_active,
                    Users.app_id,
                )
            )
            .where(
                and_(
                    Users.tenant_id == self.tenant_id,
                    Users.app_id == self.app_id,
                    Users.id == user_id,
                    Users.deleted_at.is_(None),
                )
            )
        )
        if not existing_user:
            raise UserNotFoundError

        if existing_user.is_active:
            existing_user.is_active = False
        else:
            existing_user.is_active = True

        return existing_user

    async def _assign_user_roles(
        self, session: AsyncSession, user_id: int, role_ids: list[int]
    ) -> None:
        """Synchronize user roles with the provided role_ids."""
        # Fetch current role links for the user
        existing_links = await session.scalars(
            select(UserRoleLink).where(UserRoleLink.user_id == user_id)
        )
        existing_links = list(existing_links)
        existing_role_ids = {link.role_id for link in existing_links}

        # Roles to remove
        to_remove = [link for link in existing_links if link.role_id not in role_ids]
        # Roles to add
        to_add = [role_id for role_id in role_ids if role_id not in existing_role_ids]

        # Remove unneeded links
        for link in to_remove:
            await session.delete(link)

        # Add new links
        for role_id in to_add:
            link = UserRoleLink(
                user_id=user_id,
                role_id=role_id,
                tenant_id=self.tenant_id,
                app_id=self.app_id,
            )
            session.add(link)

    async def update(  # noqa: C901
        self,
        user_id: int,
        username: str | None = None,
        email: EmailStr | None = None,
        phone: str | None = None,
        role_ids: list[int] | None = None,
        type_id: int | None = None,
        subtype_id: int | None = None,
        description: str | None = None,
        user_metadata: dict[str, Any] | None = None,
    ) -> UpdateUserResponse:
        """
        Updates the information of a specific user by their ID.

        Args:
          - tenant_key (int/str): The tenant_key means tenant_id or name. This is required.
          - app_key (int/str): The app_key means app_id or name. This is required.
          - user_id (int): The unique identifier of the user to retrieve.
          - username (str | None): The username of the user.
          - phone (str | None): The phone number of the user.
          - email (str | None): The email address of the user.
          - role_ids (list[int] | None) : List of role IDs to assign to the user.
          - type_id (int | None) : The Type ID of the user.
          - subtype_id (int | None) : The Subtype ID of the user.
          - description (str | None): The description of the user.

        Returns:
          - UpdateUserResponse: A response containing the updated user data.

        Raises:
          - UserNotFoundError: If no user with the provided username is found.
          - PhoneAlreadyExistsError: If the provided phone number already exists.
          - EmailAlreadyExistsError: If the provided email address already exists.
          - RoleNotFoundError: If the provided role ID does not exist.
          - UserTypeNotFoundError: If the provided user type ID does not exist.
          - UserSubtypeNotFoundError: If the provided user subtype ID does not exist.

        """

        await self._resolve_context_ids()

        async with self.session.begin_nested():
            existing_user = await self.session.scalar(
                select(Users)
                .options(
                    load_only(
                        Users.id,
                        Users.username,
                        Users.phone,
                        Users.email,
                        Users.type_id,
                        Users.subtype_id,
                        Users.app_id,
                        Users.description,
                        Users.user_metadata,
                    ),
                    selectinload(Users.roles),
                )
                .where(
                    and_(
                        Users.tenant_id == self.tenant_id,
                        Users.app_id == self.app_id,
                        Users.id == user_id,
                        Users.deleted_at.is_(None),
                    )
                )
            )
            if not existing_user:
                raise UserNotFoundError

            if phone:
                existing_phone = await self.session.scalar(
                    select(Users.id).where(
                        and_(
                            Users.tenant_id == self.tenant_id,
                            Users.app_id == self.app_id,
                            Users.phone == phone,
                            Users.id != user_id,
                        )
                    )
                )
                if existing_phone:
                    raise PhoneAlreadyExistsError
            if email:
                existing_email = await self.session.scalar(
                    select(Users.id).where(
                        and_(
                            Users.tenant_id == self.tenant_id,
                            Users.app_id == self.app_id,
                            Users.email == email,
                            Users.id != user_id,
                        )
                    )
                )
                if existing_email:
                    raise EmailAlreadyExistsError
            roles = existing_user.roles
            if role_ids:
                roles_result = await self.session.scalars(
                    select(Roles)
                    .options(load_only(Roles.id, Roles.name))
                    .where(
                        and_(
                            Roles.tenant_id == self.tenant_id,
                            Roles.app_id == self.app_id,
                            Roles.id.in_(role_ids),
                            Roles.deleted_at.is_(None),
                        )
                    )
                )
                existing_roles = roles_result.all()
                if len(existing_roles) != len(role_ids):
                    raise RoleNotFoundError
                await self._assign_user_roles(self.session, user_id, role_ids)
                roles = existing_roles

            if type_id:
                existing_usertype = await self.session.scalar(
                    select(UserTypes)
                    .options(load_only(UserTypes.id))
                    .where(
                        and_(
                            UserTypes.tenant_id == self.tenant_id,
                            UserTypes.app_id == self.app_id,
                            UserTypes.id == type_id,
                            UserTypes.deleted_at.is_(None),
                        )
                    )
                )
                if not existing_usertype:
                    raise UserTypeNotFoundError

            if subtype_id:
                existing_user_subtype = await self.session.scalar(
                    select(UserSubTypes)
                    .options(load_only(UserSubTypes.id))
                    .where(
                        and_(
                            UserSubTypes.tenant_id == self.tenant_id,
                            UserSubTypes.app_id == self.app_id,
                            UserSubTypes.id == subtype_id,
                            UserSubTypes.deleted_at.is_(None),
                        )
                    )
                )
                if not existing_user_subtype:
                    raise UserSubTypeNotFoundError

            existing_user.username = (
                username if username is not None else existing_user.username
            )
            existing_user.phone = phone if phone is not None else existing_user.phone
            existing_user.email = email if email is not None else existing_user.email
            existing_user.description = (
                description if description is not None else existing_user.description
            )
            existing_user.user_metadata = (
                user_metadata
                if user_metadata is not None
                else existing_user.user_metadata
            )
            existing_user.type_id = (
                type_id if type_id is not None else existing_user.type_id
            )
            existing_user.subtype_id = (
                subtype_id if subtype_id is not None else existing_user.subtype_id
            )

            return UpdateUserResponse(
                id=existing_user.id,
                username=existing_user.username,
                email=existing_user.email,
                phone=existing_user.phone,
                description=existing_user.description,
                user_metadata=existing_user.user_metadata,
                roles=[RoleResponse(id=role.id, name=role.name) for role in roles],
                user_type_id=existing_user.type_id,
                user_subtype_id=existing_user.subtype_id,
                app_id=existing_user.app_id,
            )

    async def delete(self, user_id: int) -> SuccessResponse:
        """
        Deletes a user account by their ID.

        Args:
          - tenant_key (int/str): The tenant_key means tenant_id or name. This is required.
          - app_key (int/str): The app_key means app_id or name. This is required.
          - user_id (int): The ID of the user whose status is to be changed.

        Returns:
          - SuccessResponse: A response indicating successful deletion of the user.

        Raises:
          - UserNotFoundError: If no user with the provided username is found.
        """

        await self._resolve_context_ids()

        existing_user = await self.session.scalar(
            select(Users)
            .options(load_only(Users.id, Users.username, Users.email, Users.phone))
            .where(
                and_(
                    Users.tenant_id == self.tenant_id,
                    Users.app_id == self.app_id,
                    Users.id == user_id,
                    Users.deleted_at.is_(None),
                )
            )
        )
        if not existing_user:
            raise UserNotFoundError

        existing_user.deleted_at = get_utc_now()

        return SuccessResponse(message=UserMessage.USER_DELETED)

    async def get_self(self, user_id: int) -> UserResponse:
        """
        Retrieves the profile information of the currently authenticated user.

        Args:
          - tenant_key (int/str): The tenant_key means tenant_id or name. This is required.
          - app_key (int/str): The app_key means app_id or name. This is required.

        Returns:
          - UserResponse: A response containing the user's profile information.

        Raises:
          - UserNotFoundError: If no user with the provided username is found.

        """

        await self._resolve_context_ids()

        user = await self.session.scalar(
            select(Users)
            .options(
                selectinload(Users.type),
                selectinload(Users.subtype),
                selectinload(Users.roles),
            )
            .where(
                Users.tenant_id == self.tenant_id,
                Users.app_id == self.app_id,
                Users.id == user_id,
            )
        )
        if not user:
            raise UserNotFoundError

        role_ids = [link.id for link in user.roles]

        roles = []
        if role_ids:
            roles = await self.role_service.get_roles_by_ids(
                role_ids=role_ids,
                tenant_id=self.tenant_id,
                app_id=self.app_id,
            )

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            description=user.description,
            user_metadata=user.user_metadata,
            roles=roles,
            type=(
                UserTypeResponse(id=user.type.id, name=user.type.name)
                if user.type
                else None
            ),
            subtype=(
                UserSubTypeResponse(id=user.subtype.id, name=user.subtype.name)
                if user.subtype
                else None
            ),
            created_at=user.created_at,
            updated_at=user.updated_at,
            mfa_enabled=user.mfa_enabled,
            mfa_enrolled=user.mfa_enrolled_at is not None,
        )

    async def refresh_token(
        self,
        claims: dict[str, str],
        refresh_token: str,
        request: Request,
        app_config: TenantAppConfig,
    ) -> LoginResponse:
        """
        Generates a new access token using a valid refresh token.

         Args:
          - tenant_key (int/str): The tenant_key means tenant_id or name. This is required.
          - app_key (int/str): The app_key means app_id or name. This is required.

        Returns:
          - LoginResponse: A response containing the new access token and refresh token

        Raises:
          - UnauthorizedError: If the refresh token is invalid or expired.

        """

        await self._resolve_context_ids()

        user_id = claims["sub"]

        user = await self.session.scalar(
            select(Users)
            .options(selectinload(Users.roles))
            .where(
                Users.tenant_id == self.tenant_id,
                Users.app_id == self.app_id,
                Users.id == int(user_id),
                Users.deleted_at.is_(None),
            )
        )
        if not user:
            raise UnauthorizedError(message=ErrorMessage.UNAUTHORIZED)

        if app_config.monthly_password_change_enable:
            password_history_entry = await self.session.scalar(
                select(PasswordHistory)
                .where(PasswordHistory.user_id == user.id)
                .order_by(desc(PasswordHistory.created_at))
            )
            if password_history_entry:
                password_created_at = password_history_entry.created_at
                if password_created_at.replace(tzinfo=UTC) + timedelta(
                    days=app_config.password_change_interval_days
                ) <= datetime.now(UTC):
                    decoded_jwt_secret = CryptoUtil().decrypt(app_config.jwt_secret)
                    action_token_kwargs = {
                        "subject": str(user.id),
                        "jwt_secret": decoded_jwt_secret,
                        "jwt_algorithm": app_config.jwt_algorithm,
                        "exp": UserDefaults.PASSWORD_REMINDER_TOKEN_EXPIRE,
                        "type": JWTokenType.ACCESS,
                        "purpose": UserAuthAction.CHANGE_PASSWORD,
                    }
                    action_token = access_jwt.encode(**action_token_kwargs)

                    return LoginResponse(
                        access_token=action_token,
                        refresh_token=None,
                        mfa_token=None,
                        user_id=user.id,
                        session_id=None,
                        username=user.username,
                        scopes={},
                        roles=[],
                        message=UserMessage.PASSWORD_REMINDER_MONTHLY,
                        action=UserAuthAction.CHANGE_PASSWORD,
                    )

        access_token_exp = app_config.access_token_ttl
        decoded_jwt_secret = CryptoUtil().decrypt(app_config.jwt_secret)
        roles_slug = [role.slug for role in user.roles]
        additional_claims = get_jwt_additional_claims(
            additional_claims=app_config.jwt_claims,
            email=user.email,
            is_mfa_enabled=user.mfa_enabled,
            roles=roles_slug,
        )
        access_token_kwargs = {
            "subject": str(user.id),
            "jwt_secret": decoded_jwt_secret,
            "jwt_algorithm": app_config.jwt_algorithm,
            "exp": access_token_exp,
            "type": JWTokenType.ACCESS,
            **additional_claims.model_dump(exclude_none=True),
        }
        mfa_token_kwargs = {
            "subject": str(user.id),
            "jwt_secret": decoded_jwt_secret,
            "jwt_algorithm": app_config.jwt_algorithm,
            "exp": settings.MFA_TOKEN_EXP,
            "type": JWTokenType.MFA,
        }
        session_id = None
        device_token = request.headers.get("device-token", "")
        is_app_mfa_required = app_config.mfa_required or False
        is_app_mfa_enabled = app_config.mfa_enabled or False
        is_user_mfa_enabled = user.mfa_enabled or False
        mfa_expires_at = get_utc_now()
        action = None
        if device_token:
            device_metadata = await get_device_metadata(request)
            user_device = await self.user_device_service.refresh_user_device(
                session=self.session,
                user_id=user.id,
                tenant_id=self.tenant_id,
                app_id=self.app_id,
                device_metadata=device_metadata,
                device_token=device_token,
            )

            mfa_expires_at = user_device.mfa_expires_at
            # Check if MFA is required
            mfa_action = is_user_mfa_required(
                is_app_mfa_required=is_app_mfa_required,
                is_app_mfa_enabled=is_app_mfa_enabled,
                is_user_mfa_enabled=is_user_mfa_enabled,
                mfa_expires_at=mfa_expires_at,
                mfa_enrolled_at=user.mfa_enrolled_at,
            )
            if mfa_action:
                action = mfa_action
            elif app_config.session_management_enabled:
                session_id = claims["session_id"]
                await self.user_session_service.refresh_session(
                    user_id=user.id,
                    tenant_id=self.tenant_id,
                    app_id=self.app_id,
                    session_id=session_id,
                    app_config=app_config,
                    device_metadata=device_metadata,
                    device_fingerprint=user_device.device_fingerprint,
                )
                access_token_kwargs["session_id"] = session_id

        access_token = None
        mfa_token = None
        applicable_refresh_token = None
        # Generate tokens
        if action in (UserAuthAction.MFA_VERIFY, UserAuthAction.MFA_SETUP):
            mfa_token_kwargs["purpose"] = action
            mfa_token = mfa_jwt.encode(**mfa_token_kwargs)
        else:
            access_token = access_jwt.encode(**access_token_kwargs)
            applicable_refresh_token = refresh_token

        scope_permissions_map = {}
        if not action:
            role_ids = [link.id for link in user.roles]
            scopes = []
            if role_ids:
                try:
                    roles = await self.role_service.get_roles_by_ids(
                        role_ids, self.tenant_id, self.app_id
                    )
                    scopes = self.get_merged_scopes_from_roles(roles)
                except RoleNotFoundError:
                    scopes = []

            # Map scopes to permissions
            scope_permissions_map = {
                entry["scope"]: entry.get("permissions", [])
                for entry in scopes
                if entry.get("permissions")
            }
            scopes_key = UserRedisKeys.scopes_key(
                tenant_id=self.tenant_id, app_id=self.app_id, user_id=user.id
            )
            await redis.set(
                scopes_key,
                json.dumps(scope_permissions_map),
                ex=UserDefaults.REDIS_USER_SCOPES_TTL,
            )

        # Return login response
        return LoginResponse(
            access_token=access_token,
            refresh_token=applicable_refresh_token,
            mfa_token=mfa_token,
            user_id=user.id,
            session_id=session_id,
            username=user.username,
            roles=roles_slug,
            scopes=scope_permissions_map,
            action=action,
        )

    async def reset_password(
        self,
        password: str,
        tenant_app_config: TenantAppConfig,
        phone: str | None = None,
        email: str | None = None,
    ) -> SuccessResponse:
        """Update user password."""
        await self._resolve_context_ids()

        if not phone and not email:
            raise PhoneOrEmailRequiredError

        user_filters = [
            Users.tenant_id == self.tenant_id,
            Users.app_id == self.app_id,
            Users.is_active.is_(True),
            Users.deleted_at.is_(None),
        ]

        if phone is not None:
            user_filters.append(Users.phone == phone)
        if email is not None:
            user_filters.append(Users.email == email)

        user = await self.session.scalar(
            select(Users)
            .options(
                load_only(Users.id, Users.phone, Users.created_at, Users.password_exp)
            )
            .where(*user_filters)
        )
        if not user:
            raise UserNotFoundError

        strong_pass = await strong_password(
            password, db=self.session, app_id=self.app_id, tenant_id=self.tenant_id
        )
        if not strong_pass:
            raise WeakPasswordError

        password_history = await self.session.scalars(
            select(PasswordHistory)
            .where(PasswordHistory.user_id == user.id)
            .order_by(desc(PasswordHistory.created_at))
            .limit(5)
        )
        for history in password_history:
            if verify_password(password, history.password):
                raise PasswordMatchedError

        async with self.session.begin_nested():
            expires_at = None
            if tenant_app_config.password_expiry_days:
                expires_at = add_to_datetime(
                    dt=get_utc_now(),
                    days=tenant_app_config.password_expiry_days,
                    to_utc=True,
                )
            password_history = PasswordHistory(
                user_id=user.id,
                password=hash_password(password) if password else None,
                app_id=self.app_id,
                tenant_id=self.tenant_id,
                expires_at=expires_at,
            )
            self.session.add(password_history)
            user.password_exp = expires_at

        user.password = hash_password(password)
        await self.session.commit()

        return SuccessResponse(message=UserMessage.PASSWORD_UPDATE_SUCCESS)

    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
        tenant_app_config: TenantAppConfig,
    ) -> SuccessResponse:
        """
        Changes the password for the currently authenticated user.

        Args:
          - tenant_key (int/str): The tenant_key means tenant_id or name. This is required.
          - app_key (int/str): The app_key means app_id or name. This is required.
          - current_password (str): The current password of the user.
          - new_password (str): The new password to be set.
          - user_id (int): The ID of the user whose password is to be changed.

        Returns:
          - SuccessResponse: A response indicating the success of the password change operation.

        Raises:
          - UserNotFoundError: If no user with the provided username is found.
          - InvalidPasswordError:  If the provided current password is invalid.
          - PasswordMatchedError:  If the new password is the same as the last five password.
          - PasswordNotMatchError: If the new password and confirmation password do not match.

        """
        await self._resolve_context_ids()

        user = await self.session.scalar(
            select(Users)
            .options(
                load_only(Users.id, Users.phone, Users.password, Users.password_exp)
            )
            .where(
                and_(
                    Users.tenant_id == self.tenant_id,
                    Users.app_id == self.app_id,
                    Users.id == user_id,
                    Users.deleted_at.is_(None),
                )
            )
        )
        if not user:
            raise UserNotFoundError

        if not verify_password(current_password, user.password):
            raise InvalidPasswordError

        # Check last five passwords from password_history
        password_history = await self.session.scalars(
            select(PasswordHistory)
            .where(PasswordHistory.user_id == user_id)
            .order_by(desc(PasswordHistory.created_at))
            .limit(5)
        )
        for history in password_history:
            if verify_password(new_password, history.password):
                raise PasswordMatchedError

        strong_pass = await strong_password(
            new_password, db=self.session, app_id=self.app_id, tenant_id=self.tenant_id
        )
        if not strong_pass:
            raise WeakPasswordError

        # Hash the new password and update
        hashed_new_password = hash_password(new_password)
        user.password = hashed_new_password

        # Add new password to password_history
        expires_at = None
        if tenant_app_config.password_expiry_days:
            expires_at = add_to_datetime(
                dt=get_utc_now(),
                days=tenant_app_config.password_expiry_days,
                to_utc=True,
            )
        password_history_entry = PasswordHistory(
            user_id=user_id,
            password=hashed_new_password,
            tenant_id=self.tenant_id,
            app_id=self.app_id,
            expires_at=expires_at,
        )
        self.session.add(password_history_entry)
        user.password_exp = expires_at

        return SuccessResponse(message="Password changed successfully")

    async def generate_user_otp(
        self, phone: str, app_config: TenantAppConfig
    ) -> SuccessResponse:
        """Generate OTP."""
        await self._resolve_context_ids()

        user = await self.session.scalar(
            select(Users)
            .options(load_only(Users.ulid, Users.phone))
            .where(
                and_(
                    Users.tenant_id == self.tenant_id,
                    Users.app_id == self.app_id,
                    Users.phone == phone,
                    Users.deleted_at.is_(None),
                )
            )
        )
        if not user:
            raise UserNotFoundError

        otp = await LoginMethodService.generate_and_set_otp(
            user_ulid=str(user.ulid),
            otp_length=app_config.otp_length,
            otp_type=app_config.otp_type,
            exp=app_config.otp_expire_seconds,
        )

        return GenerateOTPResponse(otp=otp)

    async def setup_user_mfa(self, user_id: int) -> MFASetupResponse:
        """Setup MFA for a user."""
        await self._resolve_context_ids()

        user = await self.session.scalar(
            select(Users)
            .options(
                load_only(
                    Users.ulid,
                    Users.username,
                    Users.mfa_enabled,
                    Users.mfa_enrolled_at,
                    Users.mfa_secret_key,
                    Users.mfa_totp_source,
                    Users.mfa_backup_codes,
                ),
                selectinload(Users.app).load_only(TenantApps.name),
            )
            .where(
                and_(
                    Users.tenant_id == self.tenant_id,
                    Users.app_id == self.app_id,
                    Users.id == user_id,
                    Users.deleted_at.is_(None),
                    Users.is_active.is_(True),
                )
            )
        )
        if not user:
            raise UserNotFoundError

        app_config = await self._get_tenant_app_config(
            tenant_id=self.tenant_id, app_id=self.app_id
        )
        if not app_config.mfa_enabled:
            raise AppMFANotEnabledError

        if user.mfa_enrolled_at:
            raise UserAlreadyMFEnrolledError

        mfa_secret_key = None
        mfa_source = None
        backup_codes = None
        totp_factory = None
        totp = None
        formatted_qrcode_base64 = None
        if user.mfa_secret_key and user.mfa_totp_source:
            mfa_secret_key = CryptoUtil().decrypt(user.mfa_secret_key)
            mfa_source = CryptoUtil().decrypt(user.mfa_totp_source)
            backup_codes = CryptoUtil().decrypt_backup_codes(user.mfa_backup_codes)
            totp_factory = create_totp_factory(
                issuer=user.app.name, totp_secret=mfa_secret_key
            )
            totp = totp_factory.from_json(source=mfa_source)
        else:
            mfa_secret_key = CryptoUtil().generate_secret_key()
            totp_factory = create_totp_factory(
                issuer=user.app.name, totp_secret=mfa_secret_key
            )
            totp = totp_factory.new(label=user.username or "")

            encrypted_mfa_source = CryptoUtil().encrypt(totp.to_json())
            encrypted_mfa_secret_key = CryptoUtil().encrypt(mfa_secret_key)
            backup_codes = CryptoUtil().generate_backup_codes()
            encrypted_backup_codes = CryptoUtil().encrypt_backup_codes(backup_codes)

            user.mfa_secret_key = encrypted_mfa_secret_key
            user.mfa_totp_source = encrypted_mfa_source
            user.mfa_backup_codes = encrypted_backup_codes

        uri = totp.to_uri()
        img = qrcode.make(uri)
        img_io = BytesIO()
        img.save(img_io, format="PNG")
        img_io.seek(0)

        qrcode_base64 = base64.b64encode(img_io.getvalue()).decode("utf-8")
        formatted_qrcode_base64 = f"data:image/png;base64,{qrcode_base64}"

        # Generate MFA token for verification
        decoded_jwt_secret = CryptoUtil().decrypt(app_config.jwt_secret)
        mfa_token = mfa_jwt.encode(
            subject=str(user.id),
            jwt_secret=decoded_jwt_secret,
            jwt_algorithm=app_config.jwt_algorithm,
            exp=settings.MFA_TOKEN_EXP,
            type=JWTokenType.MFA,
            purpose=UserAuthAction.MFA_VERIFY,
        )

        return MFASetupResponse(
            qrcode_base64=formatted_qrcode_base64,
            backup_codes=backup_codes,
            mfa_token=mfa_token,
        )

    async def verify_user_mfa(  # noqa: C901, PLR0915
        self,
        code: str,
        remember: bool | None,
        backup_code: str | None,
        user_id: int,
        request: Request,
    ) -> MFAVerifiedResponse:
        """Verify MFA for a user."""
        await self._resolve_context_ids()
        app_config = await self._get_tenant_app_config(
            tenant_id=self.tenant_id, app_id=self.app_id
        )

        user = await self.session.scalar(
            select(Users)
            .options(
                load_only(
                    Users.ulid,
                    Users.username,
                    Users.email,
                    Users.mfa_enabled,
                    Users.mfa_enrolled_at,
                    Users.mfa_totp_source,
                    Users.mfa_secret_key,
                    Users.mfa_backup_codes,
                ),
                selectinload(Users.app).load_only(TenantApps.name),
                selectinload(Users.roles),
            )
            .where(
                and_(
                    Users.tenant_id == self.tenant_id,
                    Users.app_id == self.app_id,
                    Users.deleted_at.is_(None),
                    Users.is_active.is_(True),
                    Users.id == user_id,
                )
            )
        )

        if not user:
            raise UserNotFoundError

        mfa_source = CryptoUtil().decrypt(user.mfa_totp_source)
        mfa_secret_key = CryptoUtil().decrypt(user.mfa_secret_key)
        totp_factory = create_totp_factory(
            issuer=user.app.name, totp_secret=mfa_secret_key
        )

        if backup_code:
            # If backup code is provided, verify it and remove it from the list
            existing_backup_code = CryptoUtil().decrypt_backup_codes(
                user.mfa_backup_codes
            )
            if backup_code not in existing_backup_code:
                raise UnauthorizedError(message=UserErrorMessage.INVALID_BACKUP_CODE)
            existing_backup_code.remove(backup_code)
            user.mfa_backup_codes = CryptoUtil().encrypt_backup_codes(
                existing_backup_code
            )
        else:
            # If backup code is not provided, verify the OTP
            try:
                totp_factory.verify(token=code, source=mfa_source)
            except (InvalidTokenError, ValueError, TypeError) as e:
                raise UnauthorizedError(
                    message=UserErrorMessage.INVALID_MFA_CODE
                ) from e

        device_token = request.headers.get("device-token", "")
        if device_token:
            device_metadata = await get_device_metadata(request)
            device_fingerprint = generate_device_fingerprint(
                device_type=device_metadata.device_type,
                platform=device_metadata.platform,
                device_token=device_token,
            )
            user_device = await self.session.scalar(
                select(UserDevices).where(
                    UserDevices.tenant_id == self.tenant_id,
                    UserDevices.app_id == self.app_id,
                    UserDevices.user_id == user_id,
                    UserDevices.device_fingerprint == device_fingerprint,
                    UserDevices.deleted_at.is_(None),
                )
            )
            if not user_device:
                raise UnauthorizedError(message=ErrorMessage.UNAUTHORIZED)
            user_device.mfa_expires_at = add_to_datetime(
                dt=get_utc_now(), days=app_config.mfa_expiry_days or 0
            )
            if remember:
                user_device.mfa_trusted_at = get_utc_now()

        # Enable MFA for user
        user.mfa_enabled = True
        user.mfa_enrolled_at = get_utc_now()
        role_ids = [link.id for link in user.roles]
        scopes = []
        if role_ids:
            try:
                roles = await self.role_service.get_roles_by_ids(
                    role_ids, self.tenant_id, self.app_id
                )
                scopes = self.get_merged_scopes_from_roles(roles)
            except RoleNotFoundError:
                scopes = []

        # Map scopes to permissions
        scope_permissions_map = {
            entry["scope"]: entry.get("permissions", [])
            for entry in scopes
            if entry.get("permissions")
        }
        scopes_key = UserRedisKeys.scopes_key(
            tenant_id=self.tenant_id, app_id=self.app_id, user_id=user.id
        )
        await redis.set(
            scopes_key,
            json.dumps(scope_permissions_map),
            ex=UserDefaults.REDIS_USER_SCOPES_TTL,
        )

        decoded_jwt_secret = CryptoUtil().decrypt(app_config.jwt_secret)
        access_token_exp = app_config.access_token_ttl
        refresh_token_exp = app_config.refresh_token_ttl
        roles_slug = [role.slug for role in user.roles]
        additional_claims = get_jwt_additional_claims(
            additional_claims=app_config.jwt_claims,
            email=user.email,
            is_mfa_enabled=user.mfa_enabled,
            roles=roles_slug,
        )
        access_token_kwargs = {
            "subject": str(user.id),
            "jwt_secret": decoded_jwt_secret,
            "jwt_algorithm": app_config.jwt_algorithm,
            "exp": access_token_exp,
            "type": JWTokenType.ACCESS,
            **additional_claims.model_dump(exclude_none=True),
        }

        refresh_token_kwargs = {
            "subject": str(user.id),
            "jwt_secret": decoded_jwt_secret,
            "jwt_algorithm": app_config.jwt_algorithm,
            "exp": refresh_token_exp,
            "type": JWTokenType.REFRESH,
            **additional_claims.model_dump(exclude_none=True),
        }

        session_id = None
        device_token = request.headers.get("device-token", "")
        if device_token:
            device_metadata = await get_device_metadata(request)
            # Create the user device in DB
            user_device = await self.user_device_service.create_user_device(
                session=self.session,
                user_id=user.id,
                tenant_id=self.tenant_id,
                app_id=self.app_id,
                device_metadata=device_metadata,
                device_token=device_token,
            )
            # Create the user session in DB
            session_id = await self.user_session_service.create_session(
                session=self.session,
                user_id=user.id,
                tenant_id=self.tenant_id,
                app_id=self.app_id,
                app_config=app_config,
                device_metadata=device_metadata,
                device_fingerprint=user_device.device_fingerprint,
                device_id=user_device.device_id,
            )
            access_token_kwargs["session_id"] = session_id
            refresh_token_kwargs["session_id"] = session_id

        access_token = access_jwt.encode(**access_token_kwargs)
        refresh_token = refresh_jwt.encode(**refresh_token_kwargs)

        return MFAVerifiedResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user_id,
            username=user.username,
            session_id=session_id,
            roles=roles_slug,
            scopes=scope_permissions_map,
        )

    async def reset_user_mfa(self, user_id: int, backup_code: str) -> MFASetupResponse:
        """Reset MFA for a user.

        TODO:
        - Add email or phone number to reset MFA
        """
        await self._resolve_context_ids()

        user = await self.session.scalar(
            select(Users)
            .options(
                load_only(
                    Users.ulid,
                    Users.username,
                    Users.mfa_enabled,
                    Users.mfa_enrolled_at,
                    Users.mfa_totp_source,
                    Users.mfa_secret_key,
                    Users.mfa_backup_codes,
                ),
                selectinload(Users.app).load_only(TenantApps.name),
            )
            .where(
                and_(
                    Users.tenant_id == self.tenant_id,
                    Users.app_id == self.app_id,
                    Users.deleted_at.is_(None),
                    Users.is_active.is_(True),
                    Users.id == user_id,
                )
            )
        )

        if not user:
            raise UserNotFoundError
        if not user.mfa_backup_codes:
            raise UserMFANotSetupError

        app_config = await self._get_tenant_app_config(
            tenant_id=self.tenant_id, app_id=self.app_id
        )
        if not app_config.mfa_enabled:
            raise AppMFANotEnabledError

        existing_backup_codes = CryptoUtil().decrypt_backup_codes(user.mfa_backup_codes)
        if backup_code not in existing_backup_codes:
            raise UnauthorizedError(message=UserErrorMessage.INVALID_BACKUP_CODE)

        # Generate MFA token for setup
        decoded_jwt_secret = CryptoUtil().decrypt(app_config.jwt_secret)
        mfa_token = mfa_jwt.encode(
            subject=str(user.id),
            jwt_secret=decoded_jwt_secret,
            jwt_algorithm=app_config.jwt_algorithm,
            exp=settings.MFA_TOKEN_EXP,
            type=JWTokenType.MFA,
            purpose=UserAuthAction.MFA_SETUP,
        )
        user.mfa_enrolled_at = None
        user.mfa_totp_source = None
        user.mfa_secret_key = None
        user.mfa_backup_codes = None

        return MFAResetResponse(mfa_token=mfa_token)

    async def enable_user_mfa(self, *, user_id: int, code: str | None) -> None:
        """Update MFA enable flag for a user.

        Args:
            user_id: The ID of the user
            code: Backup code for MFA
        """
        await self._resolve_context_ids()

        user = await self.session.scalar(
            select(Users)
            .options(
                load_only(
                    Users.ulid,
                    Users.username,
                    Users.mfa_enabled,
                    Users.mfa_enrolled_at,
                    Users.mfa_totp_source,
                    Users.mfa_secret_key,
                    Users.mfa_backup_codes,
                ),
                selectinload(Users.app).load_only(TenantApps.name),
            )
            .where(
                and_(
                    Users.tenant_id == self.tenant_id,
                    Users.app_id == self.app_id,
                    Users.deleted_at.is_(None),
                    Users.is_active.is_(True),
                    Users.id == user_id,
                )
            )
        )

        if not user:
            raise UserNotFoundError

        app_config = await self._get_tenant_app_config(
            tenant_id=self.tenant_id, app_id=self.app_id
        )
        if not app_config.mfa_enabled:
            raise AppMFANotEnabledError

        mfa_token = None
        action = None
        if user.mfa_enrolled_at is None:
            decoded_jwt_secret = CryptoUtil().decrypt(app_config.jwt_secret)
            mfa_token = mfa_jwt.encode(
                subject=str(user.id),
                jwt_secret=decoded_jwt_secret,
                jwt_algorithm=app_config.jwt_algorithm,
                exp=settings.MFA_TOKEN_EXP,
                type=JWTokenType.MFA,
                purpose=UserAuthAction.MFA_SETUP,
            )
            action = UserAuthAction.MFA_SETUP

        if code:
            mfa_source = CryptoUtil().decrypt(user.mfa_totp_source)
            mfa_secret_key = CryptoUtil().decrypt(user.mfa_secret_key)
            totp_factory = create_totp_factory(
                issuer=user.app.name, totp_secret=mfa_secret_key
            )
            try:
                totp_factory.verify(token=code, source=mfa_source)
            except (InvalidTokenError, ValueError, TypeError) as e:
                raise UnauthorizedError(
                    message=UserErrorMessage.INVALID_MFA_CODE
                ) from e
            # Enable here only if user mfa enrolled before
            user.mfa_enabled = True

        return MFAEnableResponse(
            message=UserMessage.MFA_ENABLED, mfa_token=mfa_token, action=action
        )

    async def disable_user_mfa(self, *, user_id: int, code: str) -> None:
        """Update MFA disable flag for a user.

        Args:
            user_id: The ID of the user
        """
        await self._resolve_context_ids()

        user = await self.session.scalar(
            select(Users)
            .options(
                load_only(
                    Users.mfa_enabled, Users.mfa_totp_source, Users.mfa_secret_key
                )
            )
            .where(
                and_(
                    Users.tenant_id == self.tenant_id,
                    Users.app_id == self.app_id,
                    Users.deleted_at.is_(None),
                    Users.is_active.is_(True),
                    Users.id == user_id,
                )
            )
        )

        if not user:
            raise UserNotFoundError

        app_config = await self._get_tenant_app_config(
            tenant_id=self.tenant_id, app_id=self.app_id
        )

        if app_config.mfa_required:
            raise UserMfaNotDisableError

        if not user.mfa_totp_source or not user.mfa_secret_key:
            raise UserMFANotSetupError

        mfa_source = CryptoUtil().decrypt(user.mfa_totp_source)
        mfa_secret_key = CryptoUtil().decrypt(user.mfa_secret_key)
        totp_factory = create_totp_factory(
            issuer=user.app.name, totp_secret=mfa_secret_key
        )
        try:
            totp_factory.verify(token=code, source=mfa_source)
        except (InvalidTokenError, ValueError, TypeError) as e:
            raise UnauthorizedError(message=UserErrorMessage.INVALID_MFA_CODE) from e

        user.mfa_enabled = False

        return MFAEnableResponse(message=UserMessage.MFA_DISABLED)
