# IAM Policy Module - Creates IAM policies with conditional statements


# Data source to get current AWS account and region
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}



# IAM Policy
resource "aws_iam_policy" "iam_policy" {
  count           = var.create_iam_policy ? 1 : 0
  name            = var.iam_policy_name
  description     = var.description

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = flatten([
      # Conditionally add CloudWatch policy statement  
      var.attach_cloudwatch_policy ? [
        {
          Action = [
            "logs:CreateLogGroup",
            "logs:CreateLogStream", 
            "logs:PutLogEvents",
            "logs:DescribeLogGroups",
            "logs:DescribeLogStreams",
            "logs:GetLogEvents",
            "logs:TagResource",
            "logs:UntagResource",
            "logs:ListTagsLogGroup",
            "logs:DeleteLogGroup",
            "logs:*",  # Full CloudWatch Logs access
            "cloudwatch:PutMetricData",
            "cloudwatch:GetMetricStatistics",
            "cloudwatch:ListMetrics",
            "cloudwatch:*"  # Full CloudWatch access
          ]
          Effect   = "Allow"
          Resource = [
            "arn:aws:logs:${var.region}:${var.account_id}:log-group:/ecs/${var.project_name}-${var.env}/*",
            "arn:aws:logs:${var.region}:${var.account_id}:log-group:/ecs/${var.project_name}-${var.env}/*:*",
            "arn:aws:logs:${var.region}:${var.account_id}:log-stream:/ecs/${var.project_name}-${var.env}/*/*",
            "arn:aws:logs:${var.region}:${var.account_id}:*",  # Full CloudWatch Logs access
            "*"  # For CloudWatch metrics and full access
          ]
        }
      ] : [],

      # Conditionally add RDS policy statement
      var.attach_rds_policy ? [
        {
          Action = [
            "rds:DescribeDBInstances",
            "rds:Connect",
            "rds:DescribeDBClusters",
            "rds:DescribeDBSubnetGroups",
            "rds:DescribeDBParameterGroups",
            "rds:DescribeDBClusterParameterGroups",
            "rds:ListTagsForResource"
          ]
          Effect   = "Allow"
          Resource = [
            "arn:aws:rds:${var.region}:${var.account_id}:db:${var.database_name}*",
            "arn:aws:rds:${var.region}:${var.account_id}:cluster:${var.database_name}*",
            "arn:aws:rds:${var.region}:${var.account_id}:subnet-group:*",
            "arn:aws:rds:${var.region}:${var.account_id}:pg:*"
          ]
        }
      ] : [],

      # Conditionally add S3 policy for all buckets
      var.attach_s3_bucket_policy ? [
        {
          Action = [
            "s3:ListBucket",        # To list the contents of the S3 bucket
            "s3:GetObject",         # To read objects from the S3 bucket
            "s3:PutObject",         # To upload objects to the S3 bucket
            "s3:DeleteObject",      # To delete objects from the S3 bucket
            "s3:CreateBucket",      # To create new S3 buckets (optional)
            "s3:PutBucketTagging",  # To tag S3 buckets
            "s3:GetBucketTagging",  # To read S3 bucket tags
            "s3:DeleteBucketTagging", # To delete S3 bucket tags
            "s3:PutEncryptionConfiguration", # To configure bucket encryption
            "s3:GetEncryptionConfiguration", # To read bucket encryption settings
            "s3:PutBucketPolicy",    # To create/update bucket policies
            "s3:GetBucketPolicy",    # To read bucket policies
            "s3:DeleteBucketPolicy"  # To delete bucket policies
          ]
          Effect = "Allow"
          Resource = [
            "arn:aws:s3:::*",         # Allows access to all buckets in your account
            "arn:aws:s3:::*/*"        # Allows access to all objects in all buckets
          ]
        }
      ] : [],

      # Conditionally add CloudFront invalidation access
      var.attach_cloudfront_access ? [
        {
          Action   = "cloudfront:CreateInvalidation"
          Effect   = "Allow"
          Resource = var.cloudfront_distribution_arn != "" ? var.cloudfront_distribution_arn : "*"
        }
      ] : [],

      # Conditionally add Lambda permissions
      var.attach_lambda_access ? [
        {
          Action = [
            "lambda:CreateFunction",           # Allows creating new Lambda functions
            "lambda:InvokeFunction",           # Allows invoking Lambda functions
            "lambda:UpdateFunctionCode",       # Allows updating Lambda function code
            "lambda:UpdateFunctionConfiguration",  # Allows updating Lambda function configuration
            "lambda:DeleteFunction",           # Allows deleting Lambda functions
            "lambda:ListFunctions",            # Allows listing Lambda functions
            "lambda:AddPermission",            # Allows adding permissions to Lambda functions
            "lambda:RemovePermission",         # Allows removing permissions from Lambda functions
            "lambda:ListVersionsByFunction",    # Allows listing versions of a Lambda function
            "lambda:PublishVersion",
            "lambda:GetFunction",
            "lambda:PublishLayerVersion",       # Allows publishing Lambda layers
            "lambda:GetLayerVersion",           # Allows getting Lambda layer versions
            "lambda:ListLayerVersions",         # Allows listing Lambda layer versions
            "lambda:DeleteLayerVersion",        # Allows deleting Lambda layer versions
            "lambda:ListLayers",                # Allows listing Lambda layers
            "lambda:GetLayerVersionPolicy",     # Allows getting Lambda layer version policies
            "lambda:AddLayerVersionPermission", # Allows adding permissions to Lambda layer versions
            "lambda:RemoveLayerVersionPermission", # Allows removing permissions from Lambda layer versions
            "lambda:TagResource",
            "lambda:PutFunctionConcurrency",
            "lambda:PutFunctionEventInvokeConfig"
          ]
          Effect   = "Allow"
          Resource = [
            "arn:aws:lambda:${var.region}:${var.account_id}:function:*",  # Applies to all Lambda functions
            "arn:aws:lambda:${var.region}:${var.account_id}:layer:*",     # Applies to all Lambda layers
            "arn:aws:lambda:${var.region}:${var.account_id}:*"            # Full Lambda access
          ]
        }
      ] : [],

      # Conditionally add IAM permissions for role creation and tagging
      var.attach_iam_role ? [
        {
          Action = [
            "iam:CreateRole",        # Allows creating IAM roles
            "iam:GetRole",           # Allows getting IAM role details
            "iam:TagRole",           # Allows tagging IAM roles
            "iam:AttachRolePolicy",  # Allows attaching IAM policies to roles
            "iam:PutRolePolicy",     # Allows adding inline policies to roles
            "iam:DeleteRole",        # Allows deleting IAM roles
            "iam:UpdateRole",        # Allows updating IAM roles
            "iam:ListRolePolicies",  # Allows listing inline policies for roles
            "iam:ListAttachedRolePolicies", # Allows listing attached policies for roles
            "iam:DetachRolePolicy",  # Allows detaching policies from roles
            "iam:DeleteRolePolicy",   # Allows deleting inline policies from roles
            "iam:GetRolePolicy"
          ]
          Effect   = "Allow"
          Resource = "*"  # Applies to all IAM roles
        }
      ] : [],

      # Conditionally add ECR permissions for pushing images
      var.attach_ecr_policy ? [
        {
          Action = [
            "ecr:GetAuthorizationToken",      # To authenticate to the ECR registry
            "ecr:BatchGetImage",              # To pull images from the ECR registry
            "ecr:BatchCheckLayerAvailability",# Check if layers already exist in the repository
            "ecr:PutImage",                   # To push images to the ECR registry
            "ecr:DescribeRepositories",       # To describe ECR repositories
            "ecr:ListImages",                 # To list images in ECR repositories
            "ecr:InitiateLayerUpload",        # To initiate the upload of image layers
            "ecr:UploadLayerPart",            # To upload parts of image layers
            "ecr:CompleteLayerUpload"         # To complete the upload of image layers
          ]
          Effect   = "Allow"
          Resource = "*"  # Applies to all ECR repositories
        }
      ] : [],

      # Conditionally add ECS permissions
      var.attach_ecs_policy ? [
        {
          Action = [
            "ecs:RegisterTaskDefinition",         # Allows registering ECS task definitions
            "ecs:UpdateService",                  # Allows updating ECS services
            "ecs:DescribeClusters",               # Allows describing ECS clusters
            "ecs:DescribeServices",               # Allows describing ECS services
            "ecs:DescribeTaskDefinition",         # Allows describing ECS task definitions
            "ecs:ListServices",                   # Allows listing ECS services
            "ecs:ListClusters",                   # Allows listing ECS clusters
            "ecs:StartTask",                      # Allows starting ECS tasks
            "ecs:StopTask",                       # Allows stopping ECS tasks
            "ecs:ListTaskDefinitions",            # Allows listing ECS task definitions
            "ecs:UpdateTaskSet",                  # Allows updating ECS task sets
            "ecs:ListTasks",                      # Allows listing ECS tasks (required for ECS service deployment)
            "ecs:DescribeTask",                   # Allows describing ECS tasks
            "ecs:CreateService",                  # Allows creating ECS services
            "ecs:DeleteService",                  # Allows deleting ECS services
            "ecs:UpdateServicePrimaryTaskSet",     # Allows updating ECS service task set (for blue/green deployments)
            "ecs:ListTaskSets",                   # Allows listing ECS task sets
            "ecs:CreateTaskSet",                  # Allows creating ECS task sets (blue/green deployments)
            "ecs:DeleteTaskSet",                  # Allows deleting ECS task sets
            "ecs:UpdateTaskSet",                  # Allows updating ECS task sets
            "ecs:DescribeTaskSets",               # Allows describing ECS task sets
            "ecs:TagResource",                    # Allows tagging ECS resources
            "iam:PassRole",                       # Allows passing IAM roles to ECS tasks
            "iam:CreateRole",                     # Allows creating IAM roles for ECS tasks
            "iam:AttachRolePolicy",               # Allows attaching IAM policies to ECS roles
            "elasticloadbalancing:DescribeLoadBalancers", # To describe ELB resources associated with ECS
            "elasticloadbalancing:DescribeTargetGroups", # To describe target groups
            "elasticloadbalancing:DescribeListeners",    # To describe listeners
            "elasticloadbalancing:RegisterTargets",      # To register ECS tasks in the load balancer
            "elasticloadbalancing:DeregisterTargets",    # To deregister ECS tasks from the load balancer
            "logs:CreateLogGroup",                   # To create CloudWatch Log groups
            "logs:CreateLogStream",                  # To create log streams for ECS task logs
            "logs:PutLogEvents"                      # To send log events to CloudWatch Logs
          ]
          Effect   = "Allow"
          Resource = "*"  # Applies to all ECS clusters, services, task definitions, IAM roles, and CloudWatch logs
        }
      ] : [],

      # Conditionally add SSM (Systems Manager) permissions
      var.attach_ssm_policy ? [
        {
          Action = [
            "ssm:GetParameter",              # Read SSM parameters
            "ssm:GetParameters",             # Read multiple SSM parameters
            "ssm:GetParametersByPath",       # Read parameters by path
            "ssm:DescribeParameters",        # List parameter metadata
            "ssm:SendCommand",               # Execute commands on instances
            "ssm:GetCommandInvocation",      # Get command execution status
            "ssm:UpdateInstanceInformation", # Update instance information
            "ssm:StartSession",              # Start Session Manager sessions
            "ssm:TerminateSession"           # Terminate Session Manager sessions
          ]
          Effect   = "Allow"
          Resource = [
            "arn:aws:ssm:${var.region}:${var.account_id}:parameter/${var.project_name}/*",
            "arn:aws:ssm:${var.region}:${var.account_id}:parameter/${var.project_name}-${var.env}/*",
            "arn:aws:ec2:${var.region}:${var.account_id}:instance/*"
          ]
        }
      ] : [],

      # Conditionally add SQS permissions
      var.attach_sqs_policy ? [
        {
          Action = [
            "sqs:SendMessage",           # Send messages to SQS queues
            "sqs:ReceiveMessage",        # Receive messages from SQS queues
            "sqs:DeleteMessage",         # Delete messages from SQS queues
            "sqs:GetQueueAttributes",    # Get queue attributes
            "sqs:GetQueueUrl",           # Get queue URL
            "sqs:ListQueues",            # List SQS queues
            "sqs:ChangeMessageVisibility" # Change message visibility timeout
          ]
          Effect   = "Allow"
          Resource = "arn:aws:sqs:${var.region}:${var.account_id}:${var.project_name}-*"
        }
      ] : [],

      # Conditionally add SNS permissions  
      var.attach_sns_policy ? [
        {
          Action = [
            "sns:Publish",              # Publish messages to SNS topics
            "sns:Subscribe",            # Subscribe to SNS topics
            "sns:Unsubscribe",          # Unsubscribe from SNS topics
            "sns:ListTopics",           # List SNS topics
            "sns:GetTopicAttributes",   # Get topic attributes
            "sns:ListSubscriptions"     # List subscriptions
          ]
          Effect   = "Allow"
          Resource = "arn:aws:sns:${var.region}:${var.account_id}:${var.project_name}-*"
        }
      ] : [],

      # Conditionally add CodeBuild permissions
      var.attach_codebuild_policy ? [
        {
          Action = [
            "codebuild:CreateProject",      # Create CodeBuild projects
            "codebuild:UpdateProject",      # Update CodeBuild projects
            "codebuild:DeleteProject",      # Delete CodeBuild projects
            "codebuild:StartBuild",         # Start CodeBuild builds
            "codebuild:StopBuild",          # Stop CodeBuild builds
            "codebuild:BatchGetBuilds",     # Get build information
            "codebuild:ListProjects",       # List CodeBuild projects
            "codebuild:BatchGetProjects"    # Get project information
          ]
          Effect   = "Allow"
          Resource = [
            "arn:aws:codebuild:${var.region}:${var.account_id}:project/${var.project_name}-*",
            "arn:aws:codebuild:${var.region}:${var.account_id}:build/${var.project_name}-*"
          ]
        }
      ] : [],

      # Conditionally add CodePipeline permissions
      var.attach_codepipeline_policy ? [
        {
          Action = [
            "codepipeline:CreatePipeline",       # Create pipelines
            "codepipeline:UpdatePipeline",       # Update pipelines
            "codepipeline:DeletePipeline",       # Delete pipelines
            "codepipeline:StartPipelineExecution", # Start pipeline execution
            "codepipeline:StopPipelineExecution",  # Stop pipeline execution
            "codepipeline:GetPipeline",          # Get pipeline configuration
            "codepipeline:GetPipelineExecution", # Get pipeline execution details
            "codepipeline:ListPipelines",        # List pipelines
            "codepipeline:PutActionRevision"     # Update action revisions
          ]
          Effect   = "Allow"
          Resource = "arn:aws:codepipeline:${var.region}:${var.account_id}:${var.project_name}-*"
        },
        {
          Action = [
            "codestar-connections:UseConnection"  # Use CodeStar connections for GitHub/GitLab
          ]
          Effect   = "Allow"
          Resource = "arn:aws:codestar-connections:${var.region}:${var.account_id}:connection/*"
        }
      ] : [],

      # Conditionally add Secrets Manager permissions
      var.attach_secrets_manager_policy ? [
        {
          Action = [
            "secretsmanager:GetSecretValue",    # Read secret values
            "secretsmanager:DescribeSecret",    # Get secret metadata
            "secretsmanager:ListSecrets",       # List secrets
            "secretsmanager:CreateSecret",      # Create secrets
            "secretsmanager:UpdateSecret",      # Update secrets
            "secretsmanager:DeleteSecret"       # Delete secrets
          ]
          Effect   = "Allow"
          Resource = "arn:aws:secretsmanager:${var.region}:${var.account_id}:secret:${var.project_name}/*"
        }
      ] : [],

      # Conditionally add API Gateway permissions
      var.attach_api_gateway_policy ? [
        {
          Action = [
            "apigateway:POST",          # Create API Gateway resources
            "apigateway:PUT",           # Update API Gateway resources
            "apigateway:PATCH",         # Patch API Gateway resources
            "apigateway:DELETE",        # Delete API Gateway resources
            "apigateway:GET",           # Read API Gateway resources
            "execute-api:Invoke",        # Invoke API Gateway APIs
            "apigateway:TagResource"
          ]
          Effect   = "Allow"
          Resource = [
            "arn:aws:apigateway:${var.region}::/*",
            "arn:aws:execute-api:${var.region}:${var.account_id}:*",
            "*"  # Full API Gateway access
          ]
        }
      ] : [],

      # Conditionally add CloudFormation permissions
      var.attach_cloudformation_policy ? [
        {
          Action = [
            "cloudformation:CreateStack",      # Create CloudFormation stacks
            "cloudformation:UpdateStack",      # Update CloudFormation stacks
            "cloudformation:DeleteStack",      # Delete CloudFormation stacks
            "cloudformation:DescribeStacks",   # Describe CloudFormation stacks
            "cloudformation:DescribeStackEvents", # Describe CloudFormation stack events
            "cloudformation:DescribeStackResource", # Describe CloudFormation stack resources
            "cloudformation:ListStacks",       # List CloudFormation stacks
            "cloudformation:GetTemplate",      # Get CloudFormation templates
            "cloudformation:CreateChangeSet",  # Create change sets
            "cloudformation:ExecuteChangeSet", # Execute change sets
            "cloudformation:DescribeChangeSet", # Describe change sets
            "cloudformation:DeleteChangeSet",  # Delete change sets
            "cloudformation:ValidateTemplate",  # Validate CloudFormation templates (global permission)
            "cloudformation:ListStackResources"
          ]
          Effect   = "Allow"
          Resource = [
            "arn:aws:cloudformation:${var.region}:${var.account_id}:stack/${var.project_name}-*/*",
            "arn:aws:cloudformation:${var.region}:${var.account_id}:stack/*-${var.env}/*",
            "arn:aws:cloudformation:${var.region}:${var.account_id}:stack/*-document-*/*",
            "arn:aws:cloudformation:${var.region}:${var.account_id}:stack/*-microservice-*/*",
            "*"  # Global permission for template validation
          ]
        }
      ] : []
    ])
  })

  tags = merge(
    {
      Name        = var.iam_policy_name
      Project     = var.project_name
      Service     = "iam-policy-${var.project_name}-${var.env}"
      Environment = var.env
      Terraform   = "true"
    },
    var.tags
  )
} 