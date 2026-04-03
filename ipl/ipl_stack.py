from aws_cdk import (
    Duration,
    Size,
    Stack,
    RemovalPolicy,
    CfnOutput,
    aws_s3 as s3,
    aws_glue as glue,
    aws_athena as athena,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_apigateway as apigw,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_ecr_assets,
)
from constructs import Construct


class IplStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # -------------------------------------------------------
        # S3 Buckets
        # -------------------------------------------------------

        raw_bucket = s3.Bucket(
            self, "IplRawData",
            bucket_name=f"ipl-raw-data-{self.account}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        processed_bucket = s3.Bucket(
            self, "IplProcessedData",
            bucket_name=f"ipl-processed-data-{self.account}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        frontend_bucket = s3.Bucket(
            self, "IplFrontend",
            bucket_name=f"ipl-frontend-{self.account}",
            website_index_document="index.html",
            website_error_document="error.html",
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            ),
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        athena_results_bucket = s3.Bucket(
            self, "IplAthenaResults",
            bucket_name=f"ipl-athena-results-{self.account}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # -------------------------------------------------------
        # Glue Database
        # -------------------------------------------------------

        glue_db = glue.CfnDatabase(
            self, "IplGlueDatabase",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name="ipl_cricket",
                description="IPL Cricket analytics database",
            ),
        )

        # -------------------------------------------------------
        # Glue Tables
        # -------------------------------------------------------

        processed_location = f"s3://{processed_bucket.bucket_name}"

        # -- matches table --
        matches_table = glue.CfnTable(
            self, "MatchesTable",
            catalog_id=self.account,
            database_name="ipl_cricket",
            table_input=glue.CfnTable.TableInputProperty(
                name="matches",
                description="IPL match-level data",
                table_type="EXTERNAL_TABLE",
                parameters={
                    "classification": "parquet",
                    "compressionType": "snappy",
                },
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    location=f"{processed_location}/matches/",
                    input_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
                    output_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
                    serde_info=glue.CfnTable.SerdeInfoProperty(
                        serialization_library="org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe",
                        parameters={"serialization.format": "1"},
                    ),
                    columns=[
                        glue.CfnTable.ColumnProperty(name="filename", type="string"),
                        glue.CfnTable.ColumnProperty(name="season", type="string"),
                        glue.CfnTable.ColumnProperty(name="match_number", type="double"),
                        glue.CfnTable.ColumnProperty(name="date", type="string"),
                        glue.CfnTable.ColumnProperty(name="team1", type="string"),
                        glue.CfnTable.ColumnProperty(name="team2", type="string"),
                        glue.CfnTable.ColumnProperty(name="city", type="string"),
                        glue.CfnTable.ColumnProperty(name="venue", type="string"),
                        glue.CfnTable.ColumnProperty(name="neutral_venue", type="double"),
                        glue.CfnTable.ColumnProperty(name="toss_winner", type="string"),
                        glue.CfnTable.ColumnProperty(name="toss_decision", type="string"),
                        glue.CfnTable.ColumnProperty(name="winner", type="string"),
                        glue.CfnTable.ColumnProperty(name="win_type", type="string"),
                        glue.CfnTable.ColumnProperty(name="win_margin", type="double"),
                        glue.CfnTable.ColumnProperty(name="result", type="string"),
                        glue.CfnTable.ColumnProperty(name="method", type="string"),
                        glue.CfnTable.ColumnProperty(name="eliminator", type="string"),
                        glue.CfnTable.ColumnProperty(name="player_of_match", type="string"),
                        glue.CfnTable.ColumnProperty(name="umpire1", type="string"),
                        glue.CfnTable.ColumnProperty(name="umpire2", type="string"),
                    ],
                ),
            ),
        )
        matches_table.add_dependency(glue_db)

        # -- deliveries (ball_by_ball) table --
        deliveries_table = glue.CfnTable(
            self, "DeliveriesTable",
            catalog_id=self.account,
            database_name="ipl_cricket",
            table_input=glue.CfnTable.TableInputProperty(
                name="deliveries",
                description="IPL ball-by-ball delivery data",
                table_type="EXTERNAL_TABLE",
                parameters={
                    "classification": "parquet",
                    "compressionType": "snappy",
                },
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    location=f"{processed_location}/deliveries/",
                    input_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
                    output_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
                    serde_info=glue.CfnTable.SerdeInfoProperty(
                        serialization_library="org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe",
                        parameters={"serialization.format": "1"},
                    ),
                    columns=[
                        glue.CfnTable.ColumnProperty(name="match_id", type="bigint"),
                        glue.CfnTable.ColumnProperty(name="date", type="string"),
                        glue.CfnTable.ColumnProperty(name="venue", type="string"),
                        glue.CfnTable.ColumnProperty(name="city", type="string"),
                        glue.CfnTable.ColumnProperty(name="team1", type="string"),
                        glue.CfnTable.ColumnProperty(name="team2", type="string"),
                        glue.CfnTable.ColumnProperty(name="season", type="string"),
                        glue.CfnTable.ColumnProperty(name="innings", type="bigint"),
                        glue.CfnTable.ColumnProperty(name="batting_team", type="string"),
                        glue.CfnTable.ColumnProperty(name="bowling_team", type="string"),
                        glue.CfnTable.ColumnProperty(name="over", type="bigint"),
                        glue.CfnTable.ColumnProperty(name="ball", type="bigint"),
                        glue.CfnTable.ColumnProperty(name="batter", type="string"),
                        glue.CfnTable.ColumnProperty(name="bowler", type="string"),
                        glue.CfnTable.ColumnProperty(name="non_striker", type="string"),
                        glue.CfnTable.ColumnProperty(name="batter_runs", type="bigint"),
                        glue.CfnTable.ColumnProperty(name="extras_total", type="bigint"),
                        glue.CfnTable.ColumnProperty(name="total_runs", type="bigint"),
                        glue.CfnTable.ColumnProperty(name="wides", type="bigint"),
                        glue.CfnTable.ColumnProperty(name="noballs", type="bigint"),
                        glue.CfnTable.ColumnProperty(name="byes", type="bigint"),
                        glue.CfnTable.ColumnProperty(name="legbyes", type="bigint"),
                        glue.CfnTable.ColumnProperty(name="penalty", type="bigint"),
                        glue.CfnTable.ColumnProperty(name="is_wicket", type="bigint"),
                        glue.CfnTable.ColumnProperty(name="player_out", type="string"),
                        glue.CfnTable.ColumnProperty(name="dismissal_kind", type="string"),
                        glue.CfnTable.ColumnProperty(name="fielder", type="string"),
                    ],
                ),
            ),
        )
        deliveries_table.add_dependency(glue_db)

        # -- batter_scorecard table --
        scorecard_table = glue.CfnTable(
            self, "BatterScorecardTable",
            catalog_id=self.account,
            database_name="ipl_cricket",
            table_input=glue.CfnTable.TableInputProperty(
                name="batter_scorecard",
                description="IPL per-match batter scorecard",
                table_type="EXTERNAL_TABLE",
                parameters={
                    "classification": "parquet",
                    "compressionType": "snappy",
                },
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    location=f"{processed_location}/batter_scorecard/",
                    input_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
                    output_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
                    serde_info=glue.CfnTable.SerdeInfoProperty(
                        serialization_library="org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe",
                        parameters={"serialization.format": "1"},
                    ),
                    columns=[
                        glue.CfnTable.ColumnProperty(name="match_id", type="bigint"),
                        glue.CfnTable.ColumnProperty(name="date", type="string"),
                        glue.CfnTable.ColumnProperty(name="venue", type="string"),
                        glue.CfnTable.ColumnProperty(name="city", type="string"),
                        glue.CfnTable.ColumnProperty(name="season", type="string"),
                        glue.CfnTable.ColumnProperty(name="batting_team", type="string"),
                        glue.CfnTable.ColumnProperty(name="bowling_team", type="string"),
                        glue.CfnTable.ColumnProperty(name="innings", type="bigint"),
                        glue.CfnTable.ColumnProperty(name="batter", type="string"),
                        glue.CfnTable.ColumnProperty(name="entry_score", type="bigint"),
                        glue.CfnTable.ColumnProperty(name="entry_wickets", type="bigint"),
                        glue.CfnTable.ColumnProperty(name="entry_over", type="bigint"),
                        glue.CfnTable.ColumnProperty(name="entry_bowler", type="string"),
                        glue.CfnTable.ColumnProperty(name="runs_after_5_balls", type="double"),
                        glue.CfnTable.ColumnProperty(name="runs_after_10_balls", type="double"),
                        glue.CfnTable.ColumnProperty(name="runs_after_20_balls", type="double"),
                        glue.CfnTable.ColumnProperty(name="runs_after_30_balls", type="double"),
                        glue.CfnTable.ColumnProperty(name="runs_after_40_balls", type="double"),
                        glue.CfnTable.ColumnProperty(name="runs_after_50_balls", type="double"),
                        glue.CfnTable.ColumnProperty(name="total_runs", type="bigint"),
                        glue.CfnTable.ColumnProperty(name="total_balls_faced", type="bigint"),
                        glue.CfnTable.ColumnProperty(name="out", type="boolean"),
                        glue.CfnTable.ColumnProperty(name="dismissal_kind", type="string"),
                        glue.CfnTable.ColumnProperty(name="dismissal_bowler", type="string"),
                        glue.CfnTable.ColumnProperty(name="dismissal_fielder", type="string"),
                    ],
                ),
            ),
        )
        scorecard_table.add_dependency(glue_db)

        # -------------------------------------------------------
        # Athena Workgroup
        # -------------------------------------------------------

        athena.CfnWorkGroup(
            self, "IplAthenaWorkgroup",
            name="ipl-workgroup",
            description="IPL Cricket analytics workgroup",
            state="ENABLED",
            work_group_configuration=athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                result_configuration=athena.CfnWorkGroup.ResultConfigurationProperty(
                    output_location=f"s3://{athena_results_bucket.bucket_name}/results/",
                ),
                enforce_work_group_configuration=True,
            ),
        )

        # -------------------------------------------------------
        # Lambda — ipl-ingestion
        # -------------------------------------------------------

        ingestion_role = iam.Role(
            self, "IngestionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        # S3: read + write processed data (match_info, deliveries, scorecard)
        ingestion_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket",
                "s3:GetBucketLocation",
            ],
            resources=[
                processed_bucket.bucket_arn,
                f"{processed_bucket.bucket_arn}/*",
            ],
        ))

        ingestion_fn = lambda_.DockerImageFunction(
            self, "Ingestion",
            function_name="ipl-ingestion",
            code=lambda_.DockerImageCode.from_image_asset(
                "lambda/ingestion",
                platform=aws_ecr_assets.Platform.LINUX_AMD64,
            ),
            role=ingestion_role,
            timeout=Duration.minutes(5),
            memory_size=1024,
            ephemeral_storage_size=Size.mebibytes(1024),
            environment={
                "PROCESSED_BUCKET": processed_bucket.bucket_name,
            },
        )

        # -------------------------------------------------------
        # Lambda — ipl-query-runner
        # -------------------------------------------------------

        query_runner_role = iam.Role(
            self, "QueryRunnerRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        # Athena: run queries and read results
        query_runner_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "athena:StartQueryExecution",
                "athena:GetQueryExecution",
                "athena:GetQueryResults",
                "athena:StopQueryExecution",
                "athena:GetWorkGroup",
            ],
            resources=[
                f"arn:aws:athena:{self.region}:{self.account}:workgroup/ipl-workgroup",
            ],
        ))

        # S3: read processed data + write/read Athena results
        query_runner_role.add_to_policy(iam.PolicyStatement(
            actions=["s3:GetObject", "s3:ListBucket"],
            resources=[
                processed_bucket.bucket_arn,
                f"{processed_bucket.bucket_arn}/*",
            ],
        ))
        query_runner_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket",
                "s3:GetBucketLocation",
                "s3:AbortMultipartUpload",
            ],
            resources=[
                athena_results_bucket.bucket_arn,
                f"{athena_results_bucket.bucket_arn}/*",
            ],
        ))

        # Glue: read catalog
        query_runner_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "glue:GetDatabase",
                "glue:GetDatabases",
                "glue:GetTable",
                "glue:GetTables",
                "glue:GetPartition",
                "glue:GetPartitions",
            ],
            resources=[
                f"arn:aws:glue:{self.region}:{self.account}:catalog",
                f"arn:aws:glue:{self.region}:{self.account}:database/ipl_cricket",
                f"arn:aws:glue:{self.region}:{self.account}:table/ipl_cricket/*",
            ],
        ))

        query_runner_fn = lambda_.Function(
            self, "QueryRunner",
            function_name="ipl-query-runner",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.handler",
            code=lambda_.Code.from_asset("lambda/query_runner"),
            role=query_runner_role,
            timeout=Duration.seconds(60),
            memory_size=256,
            environment={
                "ATHENA_WORKGROUP": "ipl-workgroup",
                "ATHENA_DATABASE": "ipl_cricket",
            },
        )

        # -------------------------------------------------------
        # API Gateway
        # -------------------------------------------------------

        api = apigw.RestApi(
            self, "IplApi",
            rest_api_name="ipl-api",
            description="IPL Cricket analytics API",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=["POST", "OPTIONS"],
                allow_headers=["Content-Type"],
            ),
            deploy_options=apigw.StageOptions(stage_name="prod"),
        )

        query_resource = api.root.add_resource("query")
        query_resource.add_method(
            "POST",
            apigw.LambdaIntegration(query_runner_fn, proxy=True),
        )

        # Usage plan with throttling
        plan = api.add_usage_plan(
            "IplUsagePlan",
            name="ipl-usage-plan",
            throttle=apigw.ThrottleSettings(
                rate_limit=10,
                burst_limit=20,
            ),
            quota=apigw.QuotaSettings(
                limit=1000,
                period=apigw.Period.DAY,
            ),
        )
        plan.add_api_stage(
            api=api,
            stage=api.deployment_stage,
        )

        # -------------------------------------------------------
        # CloudFront Distribution
        # -------------------------------------------------------

        distribution = cloudfront.Distribution(
            self, "IplDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.HttpOrigin(
                    f"{frontend_bucket.bucket_name}.s3-website.{self.region}.amazonaws.com",
                    protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD,
            ),
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                ),
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                ),
            ],
            price_class=cloudfront.PriceClass.PRICE_CLASS_ALL,
            comment="IPL Cricket Query Engine",
        )

        # -------------------------------------------------------
        # Outputs
        # -------------------------------------------------------

        CfnOutput(self, "RawBucket", value=raw_bucket.bucket_name)
        CfnOutput(self, "ProcessedBucket", value=processed_bucket.bucket_name)
        CfnOutput(self, "FrontendBucket", value=frontend_bucket.bucket_name)
        CfnOutput(self, "FrontendUrl", value=frontend_bucket.bucket_website_url)
        CfnOutput(self, "AthenaResultsBucket", value=athena_results_bucket.bucket_name)
        CfnOutput(self, "GlueDatabase", value="ipl_cricket")
        CfnOutput(self, "AthenaWorkgroup", value="ipl-workgroup")
        CfnOutput(self, "IngestionFunction", value=ingestion_fn.function_name)
        CfnOutput(self, "QueryRunnerFunction", value=query_runner_fn.function_name)
        CfnOutput(self, "ApiEndpoint", value=f"{api.url}query")
        CfnOutput(self, "CloudFrontUrl", value=f"https://{distribution.distribution_domain_name}")
        CfnOutput(self, "CloudFrontDistributionId", value=distribution.distribution_id)
