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

## Get Started
1. Install dependencies:- `uv sync`
2. Activate venv: `source ./.venv/bin/activate`
3. Add `.env` as per `.env.example`
4. Run developement server: `fastapi run`

> Visit [http://localhost:8000/docs](http://localhost:8000/docs) for detailed API documentation

## Deployment

- Frontend: [watch-expense-client](https://github.com/mohits-git/watch-expense-client)
- Email Worker: [watch-expense-email-worker](https://github.com/mohits-git/watch-expense-email-worker)
- Backend API: [watch-expense-py](https://github.com/mohits-git/watch-expense-py)

> deploy the email worker and use the appropriate sqs email worker url and configuration appropriately

### FastAPI Backend Deployement on AWS
1. Generate requirements.txt
```bash
uv pip freeze > requirements.txt
```

2. Build and push docker image to ECR repository
```bash
./deploy/build-and-push.sh

# or directly run:
# docker buildx build --platform linux/amd64 -t 873335417993.dkr.ecr.ap-south-1.amazonaws.com/mohits-ecr/watch-expense-py:latest --push .
```

3. Update the parameters in the `deploy/deploy.py` script for the cfns 

4. Deploy Application Infrastructure Stacks in order:-
```bash
cd deploy
python deploy.py
```
