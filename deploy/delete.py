# script to delete all the deployed infra in order safely
import boto3

TEMPLATES = [
    "network-base",
    "network-endpoints",
    "storage",
    "rules",
    # "alb",
    "nlb",
    "ecs",
    "apigw",
]

session = boto3.Session(region_name="ap-south-1")
cfn = session.client("cloudformation")


def delete_stack(stack_name: str):
    try:
        cfn.delete_stack(StackName=stack_name)
        waiter = cfn.get_waiter('stack_delete_complete')
        waiter.wait(StackName=stack_name)
    except Exception as e:
        print(f"Error deleting stack {stack_name}: {e}")


def main():
    template_prefix = "watch-expense-"
    for template in reversed(TEMPLATES):
        stack_name = f"{template_prefix}{template}"
        print(f"Deleting stack: {stack_name}")
        delete_stack(stack_name)
        print(f"Deleted stack: {stack_name}")


if __name__ == "__main__":
    main()
