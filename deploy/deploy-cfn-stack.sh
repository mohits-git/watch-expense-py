aws cloudformation deploy \
--capabilities CAPABILITY_NAMED_IAM \
--stack-name watch-expense-py-stack \
--template-file deploy/template.yaml \
--region ap-south-1 \
--parameter-overrides \
  ApiDomain=api.watchexpensepy.mohits.me
