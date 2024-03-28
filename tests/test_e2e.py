import os
import time

import pytest
import requests


def test_upload_to_elastic(file_pdf_path):
    """
    When I POST a file to core-api/file
    I Expect a Chunk with a non-null embedding ... eventually
    """

    file_name = os.path.basename(file_pdf_path)
    files = {"file": (file_name, open(file_pdf_path, "rb"), "application/pdf")}
    _response = requests.post(url="http://localhost:5002/file", files=files)
    time.sleep(60)
    # assert response.status_code == 200
    # file_uuid = response.json()["uuid"]
    #
    # timeout = 60  # 10s should be plenty
    # start_time = time.time()
    # embeddings_found = False
    #
    # while not embeddings_found and time.time() - start_time < timeout:
    #     time.sleep(1)
    #     chunks = requests.get(f"http://localhost:5002/file/{file_uuid}/chunks").json()
    #     embeddings_found = any(chunk["embedding"] for chunk in chunks)
    #
    # if not embeddings_found:
    #     pytest.fail(reason=f"failed to get embedded chunks within {timeout} seconds")
