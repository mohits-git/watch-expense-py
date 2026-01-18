import boto3

session = boto3.Session(region_name="ap-south-1")
cfn = session.client("cloudformation")


def deploy_stack(stack_name, template_path, params):
    with open(template_path) as f:
        template_body = f.read()

    try:
        cfn.create_stack(
            StackName=stack_name,
            TemplateBody=template_body,
            Parameters=params,
            Capabilities=["CAPABILITY_NAMED_IAM"]
        )
        waiter = cfn.get_waiter("stack_create_complete")
        waiter.wait(StackName=stack_name)

    except cfn.exceptions.AlreadyExistsException:
        try:
            cfn.update_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=params,
                Capabilities=["CAPABILITY_NAMED_IAM"]
            )
            waiter = cfn.get_waiter("stack_update_complete")
            waiter.wait(StackName=stack_name)
        except cfn.exceptions.ClientError as e:
            msg = e.response['Error']['Message']
            if "No updates are to be performed" in msg:
                print(f"No updates for stack: {stack_name}")
            else:
                raise


def get_outputs(stack_name):
    resp = cfn.describe_stacks(StackName=stack_name)
    outputs = resp["Stacks"][0].get("Outputs", [])
    return {o["OutputKey"]: o["OutputValue"] for o in outputs}


PARAMETRS = {  # with initial default parameters
    "Region": "ap-south-1",
    "CidrBlock": "10.0.0.0/16",
    "WatchExpenseBucketName": "watch-expense-py-bucket1",
    "WatchExpenseTableName": "watch-expense-py-table",
    "HostedZoneId": "Z10038311RTI4QU4LIGAH",
    "ApiDomain": "api.watchexpensepy.mohits.me",
    "SSLCertificateArn": "arn:aws:acm:ap-south-1:873335417993:certificate/deea0830-e20f-4f41-841c-30b801e60e01",
    "WatchExpenseSecretsArn": "arn:aws:secretsmanager:us-east-1:873335417993:secret:watch-expense-backend-cjAARe",
    "ContainerImageURI": "873335417993.dkr.ecr.ap-south-1.amazonaws.com/mohits-ecr/watch-expense-py"
}

TEMPLATES = [
    {
        "name": "network-base",
        "params": [
            "Region",
            "CidrBlock",
        ]
    },
    {
        "name": "network-endpoints",
        "params": [
            "VpcId",
            "CidrBlock",
            "PublicSubnets",
            "PrivateSubnets",
            "PrivateRouteTableIDs",
            "PublicRouteTableID",
        ]
    },
    {
        "name": "storage",
        "params": [
            "WatchExpenseBucketName",
            "WatchExpenseTableName",
        ]
    },
    {
        "name": "rules",
        "params": [
            "VpcId",
            "WatchExpenseTableArn",
            "WatchExpenseBucketName",
            "WatchExpenseSecretsArn",
        ]
    },
    # {
    #     "name": "alb",
    #     "params": [
    #         "VpcId",
    #         "PublicSubnets",
    #         "WatchExpenseLBSecurityGroupId",
    #         "HostedZoneId",
    #         "ApiDomain",
    #         "SSLCertificateArn",
    #     ]
    # },
    {
        "name": "nlb",
        "params": [
            "VpcId",
            "PrivateSubnets",
            "WatchExpenseLBSecurityGroupId",
        ]
    },
    {
        "name": "ecs",
        "params": [
            "VpcId",
            "PrivateSubnets",
            "WatchExpenseTargetGroupArn",
            "WatchExpenseTargetGroupName",
            "WatchExpenseLoadBalancerName",
            "WatchExpenseBucketName",
            "WatchExpenseTableName",
            "WatchExpenseECSTaskExecutionRoleArn",
            "WatchExpenseECSTaskRoleArn",
            "WatchExpenseECSSecurityGroupId",
            "WatchExpenseSecretsArn",
            "ContainerImageURI",
        ]
    },
    {
        "name": "apigw",
        "params": [
            "VpcId",
            "WatchExpenseLoadBalancerListenerArn",
            "WatchExpenseVPCLinkId",
            "HostedZoneId",
            "ApiDomain",
            "SSLCertificateArn",
        ]
    }
]


def orchestrate_deployment():
    stack_name_prefix = "watch-expense-"
    for template in TEMPLATES:
        stack_name = f"{stack_name_prefix}{template["name"]}"
        template_path = f"./infra/{template["name"]}.yaml"
        params = [
            {
                "ParameterKey": key,
                "ParameterValue": PARAMETRS[key],
            }
            for key in template["params"]
        ]

        print(f"Deploying stack: {stack_name}")
        deploy_stack(stack_name, template_path, params)
        print(f"Deployed stack: {stack_name}")

        outputs = get_outputs(stack_name)
        # assuming the cfn stacks output the params for the next dependent stack
        PARAMETRS.update(outputs)


if __name__ == "__main__":
    orchestrate_deployment()
