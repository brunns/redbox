from typing import Literal, Optional

import boto3
from botocore.exceptions import ClientError
from elasticsearch import Elasticsearch
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class ElasticLocal(BaseModel):
    host: str = "elasticsearch"
    port: int = 9200
    scheme: str = "http"
    user: str = "elastic"
    version: str = "8.11.0"
    password: str = "redboxpass"


class ElasticCloud(BaseModel):
    api_key: str
    cloud_id: str


class Settings(BaseSettings):
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    elastic_cloud: Optional[ElasticCloud] = None
    elastic_local: Optional[ElasticLocal] = None

    kibana_system_password: str = "redboxpass"
    metricbeat_internal_password: str = "redboxpass"
    filebeat_internal_password: str = "redboxpass"
    heartbeat_internal_password: str = "redboxpass"
    monitoring_internal_password: str = "redboxpass"
    beats_system_password: str = "redboxpass"

    minio_host: str = "minio"
    minio_port: int = 9000
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"

    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "eu-west-2"

    object_store: str = "minio"

    bucket_name: str = "redbox-storage-dev"
    embedding_model: str = "all-mpnet-base-v2"

    embed_queue_name: str = "redbox-embedder-queue"
    ingest_queue_name: str = "redbox-ingester-queue"

    redis_host: str = "redis"
    redis_port: int = 6379

    dev_mode: bool = False
    django_settings_module: str = "redbox_app.settings"
    debug: bool = True
    django_secret_key: str
    environment: Literal["LOCAL"] = "LOCAL"
    postgres_user: str = "redbox-core"
    postgres_db: str = "redbox-core"
    postgres_password: str
    postgres_host: str = "db"
    contact_email: str = "test@example.com"
    core_api_host: str = "http://core-api"
    core_api_port: int = 5002

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter='__')

    def elasticsearch_client(self) -> Elasticsearch:
        if self.elastic_local:
            es = Elasticsearch(
                hosts=[
                    {
                        "host": self.elastic_local.host,
                        "port": self.elastic_local.port,
                        "scheme": self.elastic_local.scheme,
                    }
                ],
                basic_auth=(self.elastic_local.user, self.elastic_local.password),
            )
            return es

        if self.elastic_cloud:
            es = Elasticsearch(cloud_id=self.elastic_cloud.cloud_id, api_key=self.elastic_cloud.api_key)
            return es

        raise ValueError("either elastic_cloud or elastic_local must be provided")

    def s3_client(self):

        if self.object_store == "minio":
            client = boto3.client(
                "s3",
                aws_access_key_id=self.minio_access_key,
                aws_secret_access_key=self.minio_secret_key,
                endpoint_url=f"http://{self.minio_host}:{self.minio_port}",
            )

        elif self.object_store == "s3":
            client = boto3.client(
                "s3",
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region,
            )
        elif self.object_store == "moto":
            from moto import mock_aws
            mock = mock_aws()
            mock.start()

            client = boto3.client(
                "s3",
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region,
            )
        else:
            raise NotImplementedError

        try:
            client.create_bucket(
                Bucket=self.bucket_name,
                CreateBucketConfiguration={"LocationConstraint": self.aws_region},
            )
        except ClientError as e:
            if e.response["Error"]["Code"] != "BucketAlreadyOwnedByYou":
                raise e

        return client

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/"
