from app.errors.codes import AppErr


ERROR_MAP: dict[AppErr, tuple[int, str]] = {
    AppErr.NOT_FOUND: (404, "Resource not found"),
    AppErr.UNAUTHORIZED: (401, "Unauthorized"),
    AppErr.FORBIDDEN: (403, "Forbidden"),
    AppErr.CONFLICT: (409, "Conflict"),
    AppErr.INVALID: (400, "Invalid request"),
    AppErr.INTERNAL: (500, "Internal server error"),
    AppErr.THROTTLE: (429, "Too many requests"),
    AppErr.VALIDATION: (422, "Vaildation Error"),

    AppErr.INVALID_USER_CREDENTIALS: (401, "Invalid credentials"),
    AppErr.ADMIN_ONLY: (403, "Admin access only"),
    AppErr.PERMISSION_DENIED: (403, "Permission denied"),

    AppErr.USER_ALREADY_EXISTS: (409, "User already exists"),
    AppErr.CREATE_USER_PASSWORD_REQUIRED: (400, "Password is required"),
    AppErr.CANNOT_DELETE_SELF: (409, "Cannot delete oneself"),

    AppErr.PROJECT_ALREADY_EXISTS: (409, "Project already exists"),

    AppErr.DEPARTMENT_ALREADY_EXISTS: (409, "Department already exists"),

    AppErr.EXPENSE_ALREADY_EXISTS: (409, "Expense already exists"),
    AppErr.INVALID_EXPENSE_RECONCILE_ADVANCE: (422, "Invalid advance for reconciliation expense"),
    AppErr.EXPENSE_RECONCILE_PERMISSION_DENIED: (403, "Cannot reconcile expense with this advance"),

    AppErr.ADVANCE_ALREADY_EXISTS: (409, "Advance already exists"),

    AppErr.IMAGE_URL_ALREADY_EXIST: (409, "Image URL already exists"),
    AppErr.IMAGE_URL_INVALID: (400, "Image URL is invalid"),
    AppErr.IMAGE_UPLOAD_FAILED: (500, "Image upload failed"),
    AppErr.IMAGE_DELETE_FAILED: (500, "Image delete failed"),
    AppErr.FAILED_TO_GET_DOWNLOAD_URL: (500, "Failed to get image download URL"),
    AppErr.IMAGE_NOT_FOUND: (404, "Image not found"),
    AppErr.UNAUTHORIZED_IMAGE_ACCESS: (401, "Unauthorized image access"),

    AppErr.PASSWORD_TOO_LONG: (400, "Password is too long, must be less than 72 characters."),
    AppErr.EMPTY_PASSWORD: (400, "Empty passwords not allowed"),

    AppErr.TOKEN_EXPIRED: (401, "Token has expired"),
    AppErr.TOKEN_INVALID_SIGNATURE: (401, "Invalid token signature"),
    AppErr.TOKEN_INVALID_AUDIENCE: (401, "Invalid token audience"),
    AppErr.TOKEN_INVALID_ISSUER: (401, "Invalid token issuer"),
    AppErr.TOKEN_DECODE_ERROR: (401, "Invalid Token"),
}
