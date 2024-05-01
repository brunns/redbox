import os
from typing import Generator, TypeVar

import pytest
from botocore.exceptions import ClientError
from elasticsearch import Elasticsearch
from fastapi.testclient import TestClient
from sentence_transformers import SentenceTransformer

from core_api.src.app import app as application
from core_api.src.app import env
from redbox.models import Chunk, File
from redbox.storage import ElasticsearchStorageHandler

T = TypeVar("T")

YieldFixture = Generator[T, None, None]


@pytest.fixture(autouse=True)
def small_model():
    SentenceTransformer(env.embedding_model, cache_folder="./models")


@pytest.fixture
def client():
    yield TestClient(application)


@pytest.fixture
def s3_client():
    _client = env.s3_client()
    try:
        _client.create_bucket(
            Bucket=env.bucket_name,
            CreateBucketConfiguration={"LocationConstraint": env.aws_region},
        )
    except ClientError as e:
        if e.response["Error"]["Code"] != "BucketAlreadyOwnedByYou":
            raise e

    yield _client


@pytest.fixture
def es_client() -> YieldFixture[Elasticsearch]:
    yield env.elasticsearch_client()


@pytest.fixture
def app_client():
    yield TestClient(application)


@pytest.fixture
def elasticsearch_storage_handler(es_client):
    yield ElasticsearchStorageHandler(es_client=es_client, root_index="redbox-data")


@pytest.fixture
def file(s3_client, file_pdf_path) -> YieldFixture[File]:
    file_name = os.path.basename(file_pdf_path)
    file_type = f'.{file_name.split(".")[-1]}'

    with open(file_pdf_path, "rb") as f:
        s3_client.put_object(
            Bucket=env.bucket_name,
            Body=f.read(),
            Key=file_name,
            Tagging=f"file_type={file_type}",
        )

    file_record = File(key=file_name, bucket=env.bucket_name)

    yield file_record


@pytest.fixture
def stored_file(elasticsearch_storage_handler, file) -> YieldFixture[File]:
    elasticsearch_storage_handler.write_item(file)
    elasticsearch_storage_handler.refresh()
    yield file


@pytest.fixture
def chunked_file(elasticsearch_storage_handler, stored_file) -> YieldFixture[File]:
    for i in range(5):
        chunk = Chunk(text="hello", index=i, parent_file_uuid=stored_file.uuid, metadata={})
        elasticsearch_storage_handler.write_item(chunk)
    elasticsearch_storage_handler.refresh()
    yield stored_file


@pytest.fixture
def file_pdf_path() -> YieldFixture[str]:
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
        "tests",
        "data",
        "pdf",
        "Cabinet Office - Wikipedia.pdf",
    )
    yield path
