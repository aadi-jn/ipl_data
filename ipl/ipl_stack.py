from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    aws_s3 as s3,
    aws_glue as glue,
    aws_athena as athena,
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
                        glue.CfnTable.ColumnProperty(name="match_id", type="string"),
                        glue.CfnTable.ColumnProperty(name="season", type="int"),
                        glue.CfnTable.ColumnProperty(name="city", type="string"),
                        glue.CfnTable.ColumnProperty(name="venue", type="string"),
                        glue.CfnTable.ColumnProperty(name="date", type="date"),
                        glue.CfnTable.ColumnProperty(name="team1", type="string"),
                        glue.CfnTable.ColumnProperty(name="team2", type="string"),
                        glue.CfnTable.ColumnProperty(name="toss_winner", type="string"),
                        glue.CfnTable.ColumnProperty(name="toss_decision", type="string"),
                        glue.CfnTable.ColumnProperty(name="winner", type="string"),
                        glue.CfnTable.ColumnProperty(name="win_by_runs", type="int"),
                        glue.CfnTable.ColumnProperty(name="win_by_wickets", type="int"),
                        glue.CfnTable.ColumnProperty(name="player_of_match", type="string"),
                        glue.CfnTable.ColumnProperty(name="umpire1", type="string"),
                        glue.CfnTable.ColumnProperty(name="umpire2", type="string"),
                    ],
                ),
            ),
        )
        matches_table.add_dependency(glue_db)

        # -- match_players table --
        match_players_table = glue.CfnTable(
            self, "MatchPlayersTable",
            catalog_id=self.account,
            database_name="ipl_cricket",
            table_input=glue.CfnTable.TableInputProperty(
                name="match_players",
                description="Players per match and team",
                table_type="EXTERNAL_TABLE",
                parameters={
                    "classification": "parquet",
                    "compressionType": "snappy",
                },
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    location=f"{processed_location}/match_players/",
                    input_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
                    output_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
                    serde_info=glue.CfnTable.SerdeInfoProperty(
                        serialization_library="org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe",
                        parameters={"serialization.format": "1"},
                    ),
                    columns=[
                        glue.CfnTable.ColumnProperty(name="match_id", type="string"),
                        glue.CfnTable.ColumnProperty(name="team", type="string"),
                        glue.CfnTable.ColumnProperty(name="player_name", type="string"),
                        glue.CfnTable.ColumnProperty(name="registry_id", type="string"),
                    ],
                ),
            ),
        )
        match_players_table.add_dependency(glue_db)

        # -- deliveries table --
        deliveries_table = glue.CfnTable(
            self, "DeliveriesTable",
            catalog_id=self.account,
            database_name="ipl_cricket",
            table_input=glue.CfnTable.TableInputProperty(
                name="deliveries",
                description="Ball-by-ball delivery data",
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
                        glue.CfnTable.ColumnProperty(name="match_id", type="string"),
                        glue.CfnTable.ColumnProperty(name="innings", type="int"),
                        glue.CfnTable.ColumnProperty(name="over_number", type="int"),
                        glue.CfnTable.ColumnProperty(name="ball_number", type="int"),
                        glue.CfnTable.ColumnProperty(name="batsman", type="string"),
                        glue.CfnTable.ColumnProperty(name="bowler", type="string"),
                        glue.CfnTable.ColumnProperty(name="non_striker", type="string"),
                        glue.CfnTable.ColumnProperty(name="runs_batsman", type="int"),
                        glue.CfnTable.ColumnProperty(name="runs_extras", type="int"),
                        glue.CfnTable.ColumnProperty(name="runs_total", type="int"),
                        glue.CfnTable.ColumnProperty(name="extra_type", type="string"),
                        glue.CfnTable.ColumnProperty(name="wicket_type", type="string"),
                        glue.CfnTable.ColumnProperty(name="player_out", type="string"),
                        glue.CfnTable.ColumnProperty(name="fielders", type="string"),
                    ],
                ),
            ),
        )
        deliveries_table.add_dependency(glue_db)

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
        # Outputs
        # -------------------------------------------------------

        CfnOutput(self, "RawBucket", value=raw_bucket.bucket_name)
        CfnOutput(self, "ProcessedBucket", value=processed_bucket.bucket_name)
        CfnOutput(self, "FrontendBucket", value=frontend_bucket.bucket_name)
        CfnOutput(self, "FrontendUrl", value=frontend_bucket.bucket_website_url)
        CfnOutput(self, "AthenaResultsBucket", value=athena_results_bucket.bucket_name)
        CfnOutput(self, "GlueDatabase", value="ipl_cricket")
        CfnOutput(self, "AthenaWorkgroup", value="ipl-workgroup")
