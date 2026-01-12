# Schema
```json
[
  /* -----------------------------------------------------------
     USER
  ------------------------------------------------------------*/
  {
    "PK": "USER",
    "SK": "PROFILE#UserId",
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
  
  /* User index email - uuid lookup */
  {
    "PK": "USER",
    "SK": "EMAIL#emailId"
    "Type": "USER_EMAIL_INDEX",
    "UserID": "user123",
  },

  /* -----------------------------------------------------------
     EXPENSE
  ------------------------------------------------------------*/
  {
    "PK": "EXPENSE",
    "SK": "DETAILS#UserID#ExpenseID",
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

  /* ExpenseId - UserId lookup */
  {
    "PK": "EXPENSE",
    "SK": "USER#expenseId",
    "Type": "EXPENSEID_USERID_INDEX",
    "UserId": "uuid"
  }
  
  /* -----------------------------------------------------------
     ADVANCE
  ------------------------------------------------------------*/
  {
    "PK": "ADVANCE",
    "SK": "DETAILS#UserID#AdvanceID",
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
  /* AdvanceId - UserId lookup */
  {
    "PK": "ADVANCE",
    "SK": "USER#advanceId",
    "Type": "AdvanceID_USERID_INDEX",
    "UserId": "uuid"
  }

  /* -----------------------------------------------------------
     DEPARTMENTS
  ------------------------------------------------------------*/
  {
    "PK": "DEPARTMENT",
    "SK": "DETAILS#DepartmentID",
    "DepartmentID": "uuid",
    "Name": "department_name",
    "Budget": "department_budget",
    "CreatedAt": "timestamp",
    "UpdatedAt": "timestamp"
  },
  /* -----------------------------------------------------------
     PROJECTS
  ------------------------------------------------------------*/
  {
    "PK": "PROJECT",
    "SK": "DETAILS#DepID#ProjectID",
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
  
  /* ProjectId - DepartmentId index */
  {
    "PK": "PROJECT",
    "SK": "DEPARTMENT#<projectID>",
    "DepartmentID": "uuid"
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

5. Get all expenses (admin)
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
