# Watch Expense APIs

WatchExpense Backend in FastAPI python

Rewrite of Golang implementation [watch-expense](https://github.com/mohits-git/watch-expense)

## Funcational Requirements

Expense Reimbursement System

### Types of Users
- Admin
- Employee

### Requirements for Admin
1. Manage Users: Create, Update, Delete and List Users (Employee or Admin)
2. Manage Projects: Create, Update, Delete and List Projects
3. Manage Departments: Create, Update, Delete and List Departments
4. View Expenses Requests (according to status)
5. Review, Approve and Reject Expense Requests
6. View Advance Requests (according to status)
7. Review, Approve and Reject Advance Requests

### Requirements for Employee
1. Login with email and password
2. Create expenses requests with bills for review
3. Create advance requests
4. Reconcile advances after approval with new expense requests of reconcilled types
5. Get Email on Approval or Rejection of a Expense Request and Advance Requests

> NOTE: currently we are using SES in sandbox, so email is restricted currently to the verified email only
