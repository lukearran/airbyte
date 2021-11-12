#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#

from unittest.mock import MagicMock

from source_helpscout_mailbox.source import SourceHelpscoutMailbox


def test_check_connection_bad_login(mocker):
    source = SourceHelpscoutMailbox()
    logger_mock, config_mock = MagicMock(), {"client_id": "bad-client-id", "client_secret": "bad-client-secret"}

    hasFailed = source.check_connection(logger_mock, config_mock)[0]

    assert hasFailed is False


def test_streams(mocker):
    source = SourceHelpscoutMailbox()
    config_mock = {}
    streams = source.streams(config_mock)
    expected_streams_number = 14
    assert len(streams) == expected_streams_number
