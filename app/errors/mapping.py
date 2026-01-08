from app.errors.codes import AppErr


ERROR_MAP: dict[AppErr, tuple[int, str]] = {
    AppErr.NOT_FOUND: (404, "Resource not found"),
    AppErr.UNAUTHORIZED: (401, "Unauthorized"),
    AppErr.FORBIDDEN: (403, "Forbidden"),
    AppErr.CONFLICT: (409, "Conflict"),
    AppErr.INVALID: (400, "Invalid request"),
    AppErr.INTERNAL: (500, "Internal server error"),
    AppErr.THROTTLE: (429, "Too many requests"),

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
}
