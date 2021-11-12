#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#

from http import HTTPStatus
from unittest.mock import MagicMock

import pytest
from source_helpscout_mailbox.source import Conversations, HelpscoutMailboxStream


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


@pytest.fixture
def patch_base_class(mocker):
    # Mock abstract methods to enable instantiating abstract class
    mocker.patch.object(HelpscoutMailboxStream, "path", "v0/example_endpoint")
    mocker.patch.object(HelpscoutMailboxStream,
                        "primary_key", "test_primary_key")
    mocker.patch.object(HelpscoutMailboxStream, "__abstractmethods__", set())


def test_next_page_token(patch_base_class):
    stream = HelpscoutMailboxStream("", "", {})

    inputs = {"response": MockResponse(
        {"page": {"size": 50, "totalElements": 1, "totalPages": 2, "number": 1}}, 200)}

    expected_token = {"next_page_number": 2}

    assert stream.next_page_token(**inputs) == expected_token


def test_parse_response(patch_base_class):
    stream = Conversations("", "conversations", {})

    inputs = {
        "response": MockResponse(
            {
                "_embedded": {"conversations": [{"id": 1678805282, "number": 5, "threads": 1, "type": "email"}]},
                "page": {"size": 25, "totalElements": 5, "totalPages": 1, "number": 1},
            },
            200,
        )
    }

    expected_parsed_object = [
        {"id": 1678805282, "number": 5, "threads": 1, "type": "email"}]

    assert stream.parse_response(**inputs) == expected_parsed_object


@pytest.mark.parametrize(
    ("http_status", "should_retry"),
    [
        (HTTPStatus.OK, False),
        (HTTPStatus.BAD_REQUEST, False),
        (HTTPStatus.TOO_MANY_REQUESTS, True),
        (HTTPStatus.INTERNAL_SERVER_ERROR, True),
    ],
)
def test_should_retry(patch_base_class, http_status, should_retry):
    response_mock = MagicMock()
    response_mock.status_code = http_status
    stream = HelpscoutMailboxStream("", "", None)
    assert stream.should_retry(response_mock) == should_retry


def test_backoff_time(patch_base_class):
    response_mock = MagicMock()
    stream = HelpscoutMailboxStream("", "", None)
    expected_backoff_time = None
    assert stream.backoff_time(response_mock) == expected_backoff_time
