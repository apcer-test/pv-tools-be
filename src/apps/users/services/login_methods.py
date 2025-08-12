from apps.tenant_app_configs.constants import (
    LoginMethodEnum,
    OTPTypeEnum,
    TenantAppConfigDefaults,
)
from apps.users.constants import UserErrorMessage, UserRedisKeys
from apps.users.exceptions import InvalidCredentialsError
from apps.users.utils import generate_otp
from core.db import redis
from core.exceptions import ForbiddenError
from core.utils.hashing import generate_hash, verify_password


class LoginMethodService:
    """
    Service for handling all login methods and authentication logic
    for users per tenant/app.

    This includes:
    - Handling login with phone/password and phone/OTP.
    - Applying throttling (rate limiting) and lockout policies.
    - Generating and validating OTPs for login.
    - Integrating with Redis for session and attempt tracking.
    """

    @staticmethod
    async def handle_failed_login_attempt(
        lockout_attempts_key: str,
        lockout_key: str,
        login_throttle_window_seconds: int,
        max_failed_logins: int,
        lockout_duration_minutes: int,
        throttle_key: str,
    ) -> None:
        """Handle failed attempt: increment throttle + lockout, and raise error."""
        tx = redis.pipeline()
        tx.incr(throttle_key)
        tx.expire(throttle_key, login_throttle_window_seconds)
        tx.incr(lockout_attempts_key)
        tx.ttl(lockout_attempts_key)
        _throttle_result, _, lockout_attempts, lockout_attempts_ttl = await tx.execute()

        if lockout_attempts == 1 or lockout_attempts_ttl == -1:
            await redis.expire(lockout_attempts_key, lockout_duration_minutes * 60)
        if lockout_attempts >= max_failed_logins:
            await redis.set(lockout_key, 1, ex=lockout_duration_minutes * 60)

    @staticmethod
    async def reset_login_counters(
        lockout_key: str,
        lockout_attempts_key: str,
        throttle_key: str,
        otp_redis_key: str | None = None,
    ) -> None:
        """Reset throttle and lockout Redis keys."""
        tx = redis.pipeline()
        tx.delete(throttle_key)
        tx.delete(lockout_key)
        tx.delete(lockout_attempts_key)
        if otp_redis_key:
            tx.delete(otp_redis_key)
        await tx.execute()

    @staticmethod
    async def login_with_email_password(
        password: str,
        hashed_password: str,
        user_ulid: str,
        login_throttle_attempts: int = TenantAppConfigDefaults.LOGIN_THROTTLE_ATTEMPTS,
        login_throttle_window_seconds: int = TenantAppConfigDefaults.LOGIN_THROTTLE_WINDOW_SECONDS,
        max_failed_logins: int = TenantAppConfigDefaults.MAX_FAILED_LOGINS,
        lockout_duration_minutes: int = TenantAppConfigDefaults.LOCKOUT_DURATION_MINUTES,
    ) -> bool:
        """
        Authenticate a user using email and password.
        Verifies the provided password against the stored hash.

        Args:
            password (str): The plain text password provided by the user.
            hashed_password (str): The hashed password stored in the database.
            user_ulid (str): Unique user identifier (ULID).
            login_throttle_attempts (int): Max attempts before throttling.
            login_throttle_window_seconds (int): Throttle window in seconds.
            max_failed_logins (int): Max failed attempts before lockout.
            lockout_duration_minutes (int): Lockout duration in minutes.
        Returns:
            bool: True if authentication is successful, raises error otherwise.
        Raises:
            InvalidCredentialsError: If the password does not match.
        """

        hashed_user_ulid = generate_hash(user_ulid)
        throttle_key = UserRedisKeys.login_throttle_key(
            hashed_user_ulid=hashed_user_ulid
        )
        lockout_key = UserRedisKeys.login_lockout_key(hashed_user_ulid=hashed_user_ulid)
        lockout_attempts_key = UserRedisKeys.login_lockout_attempts_key(
            hashed_user_ulid=hashed_user_ulid
        )
        # Check if user is currently locked out (long-term lockout)
        lockout = await redis.get(lockout_key)
        if lockout:
            raise ForbiddenError(message=UserErrorMessage.ACCOUNT_LOCKED)

        # Check if user is throttled (short-term rate limit)
        failed_attempts = await redis.get(throttle_key)
        if failed_attempts and int(failed_attempts) >= login_throttle_attempts:
            raise InvalidCredentialsError(
                message=UserErrorMessage.TOO_MANY_FAILED_ATTEMPTS
            )
        if not verify_password(
            hashed_password=hashed_password, plain_password=password
        ):
            await LoginMethodService.handle_failed_login_attempt(
                throttle_key=throttle_key,
                lockout_attempts_key=lockout_attempts_key,
                lockout_key=lockout_key,
                login_throttle_window_seconds=login_throttle_window_seconds,
                max_failed_logins=max_failed_logins,
                lockout_duration_minutes=lockout_duration_minutes,
            )
            raise InvalidCredentialsError

        await LoginMethodService.reset_login_counters(
            lockout_key=lockout_key,
            lockout_attempts_key=lockout_attempts_key,
            throttle_key=throttle_key,
        )

        return True

    @staticmethod
    async def login_with_phone_password(
        password: str,
        hashed_password: str,
        user_ulid: str,
        login_throttle_attempts: int = TenantAppConfigDefaults.LOGIN_THROTTLE_ATTEMPTS,
        login_throttle_window_seconds: int = TenantAppConfigDefaults.LOGIN_THROTTLE_WINDOW_SECONDS,
        max_failed_logins: int = TenantAppConfigDefaults.MAX_FAILED_LOGINS,
        lockout_duration_minutes: int = TenantAppConfigDefaults.LOCKOUT_DURATION_MINUTES,
    ) -> bool:
        """
        Authenticate a user using phone and password.
        Verifies the provided password against the stored hash.

        Args:
            password (str): The plain text password provided by the user.
            hashed_password (str): The hashed password stored in the database.
            user_ulid (str): Unique user identifier (ULID).
            login_throttle_attempts (int): Max attempts before throttling.
            login_throttle_window_seconds (int): Throttle window in seconds.
            max_failed_logins (int): Max failed attempts before lockout.
            lockout_duration_minutes (int): Lockout duration in minutes.

        Returns:
            bool: True if authentication is successful, raises error otherwise.
        Raises:
            InvalidCredentialsError: If the password does not match.
        """
        hashed_user_ulid = generate_hash(user_ulid)
        throttle_key = UserRedisKeys.login_throttle_key(
            hashed_user_ulid=hashed_user_ulid
        )
        lockout_key = UserRedisKeys.login_lockout_key(hashed_user_ulid=hashed_user_ulid)
        lockout_attempts_key = UserRedisKeys.login_lockout_attempts_key(
            hashed_user_ulid=hashed_user_ulid
        )
        # Check if user is currently locked out (long-term lockout)
        lockout = await redis.get(lockout_key)
        if lockout:
            raise ForbiddenError(message=UserErrorMessage.ACCOUNT_LOCKED)

        # Check if user is throttled (short-term rate limit)
        failed_attempts = await redis.get(throttle_key)
        if failed_attempts and int(failed_attempts) >= login_throttle_attempts:
            raise InvalidCredentialsError(
                message=UserErrorMessage.TOO_MANY_FAILED_ATTEMPTS
            )
        if not verify_password(
            hashed_password=hashed_password, plain_password=password
        ):
            await LoginMethodService.handle_failed_login_attempt(
                throttle_key=throttle_key,
                lockout_attempts_key=lockout_attempts_key,
                lockout_key=lockout_key,
                login_throttle_window_seconds=login_throttle_window_seconds,
                max_failed_logins=max_failed_logins,
                lockout_duration_minutes=lockout_duration_minutes,
            )
            raise InvalidCredentialsError

        await LoginMethodService.reset_login_counters(
            lockout_key=lockout_key,
            lockout_attempts_key=lockout_attempts_key,
            throttle_key=throttle_key,
        )
        return True

    @staticmethod
    async def login_with_phone_otp(
        user_ulid: str,
        otp: str,
        login_throttle_attempts: int = TenantAppConfigDefaults.LOGIN_THROTTLE_ATTEMPTS,
        login_throttle_window_seconds: int = TenantAppConfigDefaults.LOGIN_THROTTLE_WINDOW_SECONDS,  # noqa: E501
        max_failed_logins: int = TenantAppConfigDefaults.MAX_FAILED_LOGINS,
        lockout_duration_minutes: int = TenantAppConfigDefaults.LOCKOUT_DURATION_MINUTES,  # noqa: E501
    ) -> bool:
        """
        Authenticate a user using phone and OTP (One-Time Password).
        Implements short-term throttling and long-term lockout using Redis.
        Increments counters and sets expiry for throttling and lockout keys.
        Resets counters on successful authentication.

        Args:
            user_ulid (str): Unique user identifier (ULID).
            otp (str): OTP provided by the user.
            login_throttle_attempts (int): Max attempts before throttling.
            login_throttle_window_seconds (int): Throttle window in seconds.
            max_failed_logins (int): Max failed attempts before lockout.
            lockout_duration_minutes (int): Lockout duration in minutes.
        Returns:
            bool: True if authentication is successful, raises error otherwise.
        Raises:
            InvalidCredentialsError: If throttled, locked out, or OTP is invalid.
        """
        hashed_user_ulid = generate_hash(user_ulid)
        otp_redis_key = UserRedisKeys.login_otp_key(hashed_user_ulid=hashed_user_ulid)
        throttle_key = UserRedisKeys.login_throttle_key(
            hashed_user_ulid=hashed_user_ulid
        )
        lockout_key = UserRedisKeys.login_lockout_key(hashed_user_ulid=hashed_user_ulid)
        lockout_attempts_key = UserRedisKeys.login_lockout_attempts_key(
            hashed_user_ulid=hashed_user_ulid
        )
        # Check if user is currently locked out (long-term lockout)
        lockout = await redis.get(lockout_key)
        if lockout:
            raise ForbiddenError(message=UserErrorMessage.ACCOUNT_LOCKED)

        # Check if user is throttled (short-term rate limit)
        failed_attempts = await redis.get(throttle_key)
        if failed_attempts and int(failed_attempts) >= login_throttle_attempts:
            raise InvalidCredentialsError(
                message=UserErrorMessage.TOO_MANY_FAILED_ATTEMPTS
            )

        # Retrieve OTP from Redis and validate
        data = await redis.get(otp_redis_key)
        if (
            not data
            or (isinstance(data, bytes) and data.decode() != otp)
            or (isinstance(data, str) and data != otp)
        ):
            # Use a Redis pipeline to increment and expire throttle and
            # lockout keys atomically
            await LoginMethodService.handle_failed_login_attempt(
                throttle_key=throttle_key,
                lockout_attempts_key=lockout_attempts_key,
                lockout_key=lockout_key,
                login_throttle_window_seconds=login_throttle_window_seconds,
                max_failed_logins=max_failed_logins,
                lockout_duration_minutes=lockout_duration_minutes,
            )
            raise InvalidCredentialsError(message=UserErrorMessage.INVALID_OTP)
        await LoginMethodService.reset_login_counters(
            lockout_key=lockout_key,
            lockout_attempts_key=lockout_attempts_key,
            throttle_key=throttle_key,
            otp_redis_key=otp_redis_key,
        )
        return True

    @staticmethod
    async def generate_and_set_otp(
        user_ulid: str, otp_length: int, otp_type: OTPTypeEnum, exp: int
    ) -> str:
        """
        Generate an OTP for the user and store it in Redis with an expiry.
        Used for phone/OTP login flows.

        Args:
            user_ulid (str): Unique user identifier (ULID).
            otp_length (int): The length of the OTP to generate.
            otp_type (OTPTypeEnum): The type of OTP (numeric, alphanumeric, etc).
            exp (int): Expiry time for the OTP in seconds.
        Returns:
            str: The generated OTP.
        """

        # Add Rate limiting
        hashed_user_ulid = generate_hash(user_ulid)
        otp_redis_key = UserRedisKeys.login_otp_key(hashed_user_ulid=hashed_user_ulid)
        lockout_key = UserRedisKeys.login_lockout_key(hashed_user_ulid=hashed_user_ulid)

        # Check if the user is currently locked out
        lockout = await redis.get(lockout_key)
        if lockout:
            raise ForbiddenError(message=UserErrorMessage.ACCOUNT_LOCKED)

        # Generate OTP
        otp = generate_otp(otp_length, otp_type)

        # Store OTP in Redis with expiry (seconds)
        await redis.set(otp_redis_key, otp, ex=exp)

        return otp

    @staticmethod
    async def is_verified_login(
        login_methods: list[LoginMethodEnum],
        user_ulid: str | None,
        password: str | None,
        hashed_password: str | None,
        otp: str | None,
        phone: str | None,
        email: str | None,
        login_throttle_attempts: int,
        login_throttle_window_seconds: int,
        max_failed_logins: int,
        lockout_duration_minutes: int,
    ) -> bool:
        """
        Verify if the provided credentials/OTP match any allowed
        login method for the user.
        Delegates the check to the appropriate authentication method based on allowed
        login methods.

        Args:
            login_methods (list[LoginMethodEnum]): List of allowed login methods for
            the user.
            user_ulid (str | None): User ULID (for OTP-based login).
            password (str | None): Plain text password (for password-based login).
            hashed_password (str | None): Hashed password from the database.
            otp (str | None): OTP provided by the user.
            login_throttle_attempts (int): Throttle attempts config.
            login_throttle_window_seconds (int): Throttle window config.
            max_failed_logins (int): Lockout attempts config.
            lockout_duration_minutes (int): Lockout duration config.
        Returns:
            bool: True if authentication is successful, raises error otherwise.
        Raises:
            InvalidCredentialsError: If none of the allowed login methods are satisfied.
        """
        # Try phone + password login if allowed
        if (
            LoginMethodEnum.PHONE_PASSWORD in login_methods
            and phone
            and hashed_password
            and password
        ):
            return await LoginMethodService.login_with_phone_password(
                password=password,
                hashed_password=hashed_password,
                user_ulid=user_ulid,
                login_throttle_attempts=login_throttle_attempts,
                login_throttle_window_seconds=login_throttle_window_seconds,
                max_failed_logins=max_failed_logins,
                lockout_duration_minutes=lockout_duration_minutes,
            )

        # Try email + password login if allowed
        if (
            LoginMethodEnum.EMAIL_PASSWORD in login_methods
            and email
            and hashed_password
            and password
        ):
            return await LoginMethodService.login_with_email_password(
                password=password,
                hashed_password=hashed_password,
                user_ulid=user_ulid,
                login_throttle_attempts=login_throttle_attempts,
                login_throttle_window_seconds=login_throttle_window_seconds,
                max_failed_logins=max_failed_logins,
                lockout_duration_minutes=lockout_duration_minutes,
            )

        # Try phone + OTP login if allowed
        if LoginMethodEnum.PHONE_OTP in login_methods and otp:
            return await LoginMethodService.login_with_phone_otp(
                user_ulid=user_ulid,
                otp=otp,
                login_throttle_attempts=login_throttle_attempts,
                login_throttle_window_seconds=login_throttle_window_seconds,
                max_failed_logins=max_failed_logins,
                lockout_duration_minutes=lockout_duration_minutes,
            )

        # If no valid login method matched, raise error
        raise InvalidCredentialsError(
            message=UserErrorMessage.INVALID_LOGIN_METHOD_OR_CREDENTIALS
        )
