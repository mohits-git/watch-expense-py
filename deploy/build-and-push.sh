echo "Building and Publishing docker image to ECR..."
docker buildx build --platform linux/amd64 -t 873335417993.dkr.ecr.ap-south-1.amazonaws.com/mohits-ecr/watch-expense-py:latest --push .

echo "Creating a new (force) deployement for service..."
aws ecs update-service --region ap-south-1 --cluster watch-expense-py-cluster --service watch-expense-py-service --force-new-deployment
