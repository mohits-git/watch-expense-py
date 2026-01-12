# Schema V2
```json
[
  /* -----------------------------------------------------------
     USER
  ------------------------------------------------------------*/
  /* User's by id */
  {
    "PK": "USER#UserId",
    "SK": "PROFILE",
    "Type": "USER",
    "UserID": "user123",
    "EmployeeID": "employeeId",
    "Name": "John Doe",
    "Email": "john@example.com",
    "Role": "Employee",
    "PasswordHash": "hashpassword",
    "DepartmentID": "dept456",
    "ProjectID": "proj789",
    "CreatedAt": "2025-01-01T00:00:00Z",
    "UpdatedAt": "2025-01-01T00:00:00Z"
  },

  /* User by email */
  {
    "PK": "USER#emailId",
    "SK": "PROFILE",
    "Type": "USER",
    "UserID": "user123",
    "EmployeeID": "employeeId",
    "Name": "John Doe",
    "Email": "john@example.com",
    "Role": "Employee",
    "PasswordHash": "hashpassword",
    "DepartmentID": "dept456",
    "ProjectID": "proj789",
    "CreatedAt": "2025-01-01T00:00:00Z",
    "UpdatedAt": "2025-01-01T00:00:00Z"
  },

  /* Query: Get All Users (for admin) */
  {
    "PK": "USER",
    "SK": "PROFILE#createdAt#UserId",
    "Type": "USER",
    "UserID": "user123",
    "EmployeeID": "employeeId",
    "Name": "John Doe",
    "Email": "john@example.com",
    "Role": "Employee",
    "PasswordHash": "hashpassword",
    "DepartmentID": "dept456",
    "ProjectID": "proj789",
    "CreatedAt": "2025-01-01T00:00:00Z",
    "UpdatedAt": "2025-01-01T00:00:00Z"
  },

  /* -----------------------------------------------------------
     EXPENSE
  ------------------------------------------------------------*/
  /* Get expense by id */
  {
    "PK": "EXPENSE#expenseId",
    "SK": "DETAILS",
    "ExpenseID": "uuid",
    "UserID": "uuid",
    "Amount": "decimal",
    "Purpose": "expense_purpose",
    "Description": "description",
    "Status": "expense_status",
    "IsReconciled": "boolean",
    "ApprovedBy?": "uuid",
    "ApprovedAt?": "timestamp",
    "ReviewedBy?": "uuid",
    "ReviewedAt?": "timestamp",
    "Bills": [
      {
        "BillID": "uuid",
        "Amount": "decimal",
        "Description": "description",
        "AttachmentURL": "url"
      }
    ],
    "CreatedAt": "timestamp",
    "UpdatedAt": "timestamp"
  },

  /* User's Expenses */
  {
    "PK": "USER#UserId",
    "SK": "EXPENSE#createdAt#expenseId",
    "Type": "EXPENSE",
    "ExpenseID": "uuid",
    "UserID": "uuid",
    "Amount": "decimal",
    "Purpose": "expense_purpose",
    "Description": "description",
    "Status": "expense_status",
    "IsReconciled": "boolean",
    "ApprovedBy?": "uuid",
    "ApprovedAt?": "timestamp",
    "ReviewedBy?": "uuid",
    "ReviewedAt?": "timestamp",
    "Bills": [
      {
        "BillID": "uuid",
        "Amount": "decimal",
        "Description": "description",
        "AttachmentURL": "url",
      }
    ],
    "CreatedAt": "timestamp",
    "UpdatedAt": "timestamp"
  },

  /* Admin fetch all expenses sorted by createdAt */
  {
    "PK": "EXPENSE",
    "SK": "DETAILS#createdAt#ExpenseID",
    "ExpenseID": "uuid",
    "UserID": "uuid",
    "Amount": "decimal",
    "Purpose": "expense_purpose",
    "Description": "description",
    "Status": "expense_status",
    "IsReconciled": "boolean",
    "ApprovedBy?": "uuid",
    "ApprovedAt?": "timestamp",
    "ReviewedBy?": "uuid",
    "ReviewedAt?": "timestamp",
    "Bills": [
      {
        "BillID": "uuid",
        "Amount": "decimal",
        "Description": "description",
        "AttachmentURL": "url",
      }
    ],
    "CreatedAt": "timestamp",
    "UpdatedAt": "timestamp"
  },  
  
  /* -----------------------------------------------------------
     ADVANCE
  ------------------------------------------------------------*/
  /* Get Advance by Id */
  {
    "PK": "ADVANCE#advanceId",
    "SK": "DETAILS",
    "AdvanceID": "uuid",
    "UserID": "uuid",
    "Amount": "decimal",
    "Purpose": "advance_purpose",
    "Description": "description",
    "Status": "advance_status",
    "ReconciledExpenseID?": "uuid",
    "ApprovedBy?": "uuid",
    "ApprovedAt?": "timestamp",
    "ReviewedBy?": "uuid",
    "ReviewedAt?": "timestamp",
    "CreatedAt": "timestamp",
    "UpdatedAt": "timestamp"
  },

  /* User's Advances */
  {
    "PK": "USER#UserId",
    "SK": "ADVANCE#createdAt#advanceId",
    "Type": "ADVANCE",
    "AdvanceID": "uuid",
    "UserID": "uuid",
    "Amount": "decimal",
    "Purpose": "advance_purpose",
    "Description": "description",
    "Status": "advance_status",
    "ReconciledExpenseID?": "uuid",
    "ApprovedBy?": "uuid",
    "ApprovedAt?": "timestamp",
    "ReviewedBy?": "uuid",
    "ReviewedAt?": "timestamp",
    "CreatedAt": "timestamp",
    "UpdatedAt": "timestamp"
  },

  /* Fetch all Advances sort by created at */
  {
    "PK": "ADVANCE",
    "SK": "DETAILS#createdAt#AdvanceID",
    "AdvanceID": "uuid",
    "UserID": "uuid",
    "Amount": "decimal",
    "Purpose": "advance_purpose",
    "Description": "description",
    "Status": "advance_status",
    "ReconciledExpenseID?": "uuid",
    "ApprovedBy?": "uuid",
    "ApprovedAt?": "timestamp",
    "ReviewedBy?": "uuid",
    "ReviewedAt?": "timestamp",
    "CreatedAt": "timestamp",
    "UpdatedAt": "timestamp"
  },

  /* -----------------------------------------------------------
     DEPARTMENTS
  ------------------------------------------------------------*/
  /* Department by id */
  {
    "PK": "DEPARTMENT#DepartmentID",
    "SK": "DETAILS",
    "DepartmentID": "uuid",
    "Name": "department_name",
    "Budget": "department_budget",
    "CreatedAt": "timestamp",
    "UpdatedAt": "timestamp"
  },

  /* Admin fetch all departments */
  {
    "PK": "DEPARTMENT",
    "SK": "DETAILS#createdAt#DepartmentID",
    "DepartmentID": "uuid",
    "Name": "department_name",
    "Budget": "department_budget",
    "CreatedAt": "timestamp",
    "UpdatedAt": "timestamp"
  },

  /* -----------------------------------------------------------
     PROJECTS
  ------------------------------------------------------------*/
  /* Get project by id */
  {
    "PK": "PROJECT#ProjectID",
    "SK": "DETAILS",
    "ProjectID": "uuid",
    "Name": "project_name",
    "Description": "description",
    "Budget": "budget",
    "StartDate": "date",
    "EndDate": "date",
    "DepartmentID": "DepID",
    "CreatedAt": "timestamp",
    "UpdatedAt": "timestamp"
  }

  /* Admin get all project's */
  {
    "PK": "PROJECT",
    "SK": "DETAILS#createdAt#projectId",
    "ProjectID": "uuid",
    "Name": "project_name",
    "Description": "description",
    "Budget": "budget",
    "StartDate": "date",
    "EndDate": "date",
    "DepartmentID": "DepID",
    "CreatedAt": "timestamp",
    "UpdatedAt": "timestamp"
  }

  /* Get department's projects */
  {
    "PK": "DEPARTMENT#depId",
    "SK": "PROJECT#createdAt#ProjectID",
    "ProjectID": "uuid",
    "Name": "project_name",
    "Description": "description",
    "Budget": "budget",
    "StartDate": "date",
    "EndDate": "date",
    "DepartmentID": "DepID",
    "CreatedAt": "timestamp",
    "UpdatedAt": "timestamp"
  }

  /* -----------------------------------------------------------
     IMAGE - USER METADATA
  ------------------------------------------------------------*/
  {
    "PK": "IMAGE",
    "SK": "IMAGE#<ImageURL>",
    "UserID": "uuid",
  }
]
```

## Access Patterns
1. Get user by ID
   → Query: PK = "USER", SK = "PROFILE#<userID>"

2. Get all users (admin)
   → Query: PK = "USER"

3. Get user by email (login)
   → Query: PK = "USER", SK = "EMAIL#<email>"
   → Then fetch: PK = "USER", SK = "PROFILE#<userID>"

5. Get all expenses sorted by createdAt (admin)
   Query: PK = "EXPENSE"

6. Get all expenses for a user
   Query: PK = "EXPENSE", SK begins_with "EXPENSE#<userID>#"

8. Get expenses by id
  Query: PK = "EXPENSE", SK begins_with "USER#<expenseID>"
  Then -> get expense -> PK = "EXPENSE", SK = "EXPENSE#<userID>#<expenseID>"

8. Get all advances (admin)
    Query: PK = "ADVANCE"

9. Get all advances for a user
    Query: PK = "ADVANCE", SK begins_with "<userID>#"

10. Get project by ID
    Query: PK = "PROJECT"
    Query: PK = "PROJECT", SK = "<ProjectID>"

11. Get all projects
    Query: PK = "PROJECT"

12. Get all projects of a department
    Query: PK = "PROJECT" SK begins_with = "PROJECT#<DepID>#"

13. Get department by ID
    Query: PK = "DEPARTMENT", SK = "<DepID>"

14. Get all departments
    Query: PK = "DEPARTMENT"
