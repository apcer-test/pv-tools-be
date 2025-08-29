/* eslint-disable no-template-curly-in-string */
/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable import/no-import-module-exports */
import dotenv from "dotenv";
import type { AWS, AwsLogRetentionInDays } from "@serverless/typescript";

dotenv.config();

const serverlessConfiguration: AWS = {
  service: `${process.env.APP_NAME}-document-microservice`,
  useDotenv: true,

  custom: {
    // Our stage is based on what is passed in when running serverless
    // commands. Or falls back to what we have set in the provider section.
    envName: "${self:provider.stage}",
    bundle: {
      linting: false,
      excludeFiles: "**/*.test.ts",
      tsConfig: "tsconfig.special.json",
      forceInclude: ["swagger-ui-dist"],
      externals: ["swagger-ui-dist"],
      copyFiles: [
        // Copy documentation html file
        {
          from: "src/public/*",
          to: "./",
        },
      ],
    },
    packager: "yarn",
    packagerOptions: {
      noFrozenLockFile: true,
      scripts: [
        "rm -rf node_modules/sharp",
        "npm install --arch=x64 --platform=linux sharp",
      ],
    },
    "serverless-offline": {
      httpPort: 4000,
      lambdaPort: 4002,
      noPrependStageInUrl: true,
    },
    // Localstack for local testing (mock aws services).
    // command to deploy : sls deploy --stage local
    localstack: {
      stages: ["local"],
      host: "http://localhost", // optional - LocalStack host to connect to
      debug: true,
      edgePort: 4566, // optional - LocalStack edge port to connect to
      autostart: true, // optional - Start LocalStack in Docker on Serverless deploy
      // lambda: // have issue with handlers paths, therefore not using this feature
      //   mountCode: true  // specify either "true", or a relative path to the root Lambda mount path
      networks: ["host", "overlay"], // optional - attaches the list of networks to the localstack docker container after startup
      docker: {
        // Enable this flag to run "docker ..." commands as sudo
        sudo: false,
        compose_file: "./localstack-compose.yml", // optional to use docker compose instead of docker or localstack cli
      },
    },
  },

  provider: {
    name: "aws",
    runtime: "nodejs20.x",
    stage: "${opt:stage}",
    memorySize: 256,
    logRetentionInDays: (process.env.LOG_RETENTION ||
      7) as AwsLogRetentionInDays,
    role: "DocumentOptRole",
    // Disable automatic log group creation to avoid conflicts
    // logs: {
    //   httpApi: {
    //     accessLogging: false,
    //   },
    // },
    environment: {
      ENV_APP_NAME: "${self:custom.envName}",
      BUCKET: `${process.env.BUCKET_NAME}`,
    },
  },

  functions: {
    app: {
      enabled: '"${env:IS_DOCKER_DEPLOYMENT}" != "true"',
      handler: "src/handler.handler",
      maximumRetryAttempts: +(process.env.MAXIMUM_RETRY || 1),
      reservedConcurrency: +(process.env.RESERVED_CONCURRENCY || 1),
      timeout: 120,

      environment: {
        ZIP_PROCESSOR_FUNCTION:
          "${self:service}-${self:provider.stage}-processZip",
      },
      events: [
        {
          httpApi: {
            path: "/{proxy+}",
            method: "*",
          },
        },
      ],
    },
    generateBlurHash: {
      name: "${env:APP_NAME}-generateBlurHash-${self:provider.stage}",
      description: "generate blur hash",
      handler: "src/handlers/blurHash.generateBlurHash",
      memorySize: 256,
      timeout: 30,
      maximumRetryAttempts: +(process.env.MAXIMUM_RETRY || 1),
      reservedConcurrency: +(process.env.RESERVED_CONCURRENCY || 0),
      layers: [{ Ref: "SharpLambdaLayer" }],

      events: [
        {
          s3: {
            bucket: `${process.env.BUCKET_NAME}`,
            event: "s3:ObjectCreated:*",
            existing: process.env.EXISTING_BUCKET === "true",
            rules: "${file(./blurhash-event-rules.yml):rules}" as any,
          },
        },
      ],
    },
    processZip: {
      handler: "src/handlers/zipProcessor.processZip",
      timeout: 900, // 15 minutes
      memorySize: 256,
      environment: {
        BUCKET_NAME: process.env.BUCKET_NAME,
      },
    },
  } as any,

  resources: {
    Resources: {
      // Explicitly define log groups to avoid conflicts
      AppLogGroup: {
        Type: "AWS::Logs::LogGroup",
        Properties: {
          LogGroupName: "/aws/lambda/${self:service}-${self:provider.stage}-app",
          RetentionInDays: (process.env.LOG_RETENTION || 7) as number,
        },
      },
      GenerateBlurHashLogGroup: {
        Type: "AWS::Logs::LogGroup",
        Properties: {
          LogGroupName: "/aws/lambda/${self:service}-generateBlurHash-${self:provider.stage}",
          RetentionInDays: (process.env.LOG_RETENTION || 7) as number,
        },
      },
      ProcessZipLogGroup: {
        Type: "AWS::Logs::LogGroup",
        Properties: {
          LogGroupName: "/aws/lambda/${self:service}-${self:provider.stage}-processZip",
          RetentionInDays: (process.env.LOG_RETENTION || 7) as number,
        },
      },
      HttpApiLogGroup: {
        Type: "AWS::Logs::LogGroup",
        Properties: {
          LogGroupName: "/aws/apigateway/${self:service}-${self:provider.stage}",
          RetentionInDays: (process.env.LOG_RETENTION || 7) as number,
        },
      },
      DocumentOptRole: {
        Type: "AWS::IAM::Role",
        Properties: {
          RoleName: "${self:service}-S3-AND-LOGS-${self:provider.stage}",
          AssumeRolePolicyDocument: {
            Version: "2012-10-17",
            Statement: [
              {
                Effect: "Allow",
                Principal: {
                  Service: ["lambda.amazonaws.com"],
                },
                Action: "sts:AssumeRole",
              },
            ],
          },
          Policies: [
            {
              PolicyName:
                "${self:service}-s3-and-log-access-${self:provider.stage}",
              PolicyDocument: {
                Version: "2012-10-17",
                Statement: [
                  {
                    Effect: "Allow",
                    Action: [
                      "logs:CreateLogGroup",
                      "logs:CreateLogStream",
                      "logs:PutLogEvents",
                      "logs:TagResource",
                      "logs:UntagResource",
                      "logs:ListTagsLogGroup",
                      "logs:DeleteLogGroup",
                    ],
                    Resource: [
                      "arn:aws:logs:*:*:log-group:/aws/lambda/*:*:*",
                      "arn:aws:logs:*:*:log-group:/aws/apigateway/*:*:*",
                    ],
                  },
                  {
                    Effect: "Allow",
                    Action: ["*"],
                    Resource: [
                      "arn:aws:s3:::${self:provider.environment.BUCKET}/*",
                    ],
                  },
                  {
                    Effect: "Allow",
                    Action: ["lambda:InvokeFunction"],
                    Resource: [
                      "arn:aws:lambda:${opt:region}:${aws:accountId}:function:${self:service}-${self:provider.stage}-processZip",
                    ],
                    // Note: change this opt:region to aws:region for localstack
                  },
                  ...(process.env.AWS_SECRET_NAME
                    ? [
                        {
                          Effect: "Allow",
                          Action: ["secretsmanager:GetSecretValue"],
                          Resource: [
                            "arn:aws:secretsmanager:${opt:region}:${aws:accountId}:secret:${env:AWS_SECRET_NAME}*",
                          ],
                        },
                      ]
                    : []),
                ],
              },
            },
          ],
        },
      },
    },
  },

  package: {
    individually: true,
  },

  plugins: [
    "serverless-dotenv-plugin",
    "serverless-bundle",
    "serverless-offline",
    "serverless-tscpaths",
    "serverless-plugin-conditional-functions",
    "serverless-localstack",
  ],

  layers: {
    sharp: {
      package: {
        artifact: "./sharp-x64.zip",
      },
    },
  },
};

module.exports = serverlessConfiguration; 