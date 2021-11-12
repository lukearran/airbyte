#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#


import json
from abc import ABC
from typing import Any, Iterable, List, Mapping, MutableMapping, Optional, Tuple

import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_cdk.sources.streams.http.auth import TokenAuthenticator


# HelpscoutInvalidCredentials Exception
# Used to raise an exception upon credentails not
# being accepted by Airbyte
class HelpscoutInvalidCredentials(Exception):
    pass


# Helpscout Api Helper Class


class HelpscoutAuthenticator:
    def __init__(self, apiClientId, apiClientSecret):
        self.client_id = apiClientId
        self.client_secret = apiClientSecret

    # Gets an Access Token to Helpscout API using
    # Client Credentials.
    def getAccessToken(self):
        if not self.client_id or not self.client_secret:
            raise HelpscoutInvalidCredentials(
                "Client Id or Client Secret cannot be null or empty.")

        # Set the URL of the API request
        url = "https://api.helpscout.net/v2/oauth2/token"

        # Set the payload for the HTTP request.
        # Include Client Id, Client Secret and Grant Type
        # to authorised using the Client Credentials oAuth flow.
        payload = json.dumps({"grant_type": "client_credentials",
                             "client_id": self.client_id, "client_secret": self.client_secret})

        # Set the headers
        headers = {"Content-Type": "application/json"}

        # Send the request and get the response
        response = requests.request("POST", url, headers=headers, data=payload)

        if response.ok:
            # Parse the respone body
            tokenResponseBody = response.json()

            # Get the Access Token
            self.access_token = tokenResponseBody["access_token"]
            self.expires_in = tokenResponseBody["expires_in"]

            return self.access_token

        else:
            # Handle a bad response
            raise HelpscoutInvalidCredentials(
                "Help Scout API responded unexpected upon requesting an oAuth Access Token.")


# Basic full refresh stream
class HelpscoutMailboxStream(HttpStream, ABC):
    # API Base URL of Help Scout
    url_base = "https://api.helpscout.net/v2/"
    # Model name
    model_name = ""

    def __init__(self, accessToken, modelName, config: Mapping[str, Any]):
        # Set the Client ID and Client Secret to properties
        self.config = config
        self.access_token = accessToken
        self.model_name = modelName

        # Oauth2Authenticator is also available if you need oauth support
        auth = TokenAuthenticator(self.access_token)

        super().__init__(authenticator=auth)

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        # Check that the response is the last page
        serverResponse = response.json()

        # Get Current Page
        currentPage = int(serverResponse["page"]["number"])
        maxPages = int(serverResponse["page"]["totalPages"])

        # If the current page is the last, then return None
        if currentPage == maxPages or maxPages == 0:
            return None
        else:
            # Get next page number
            nextPage = currentPage + 1
            # Return the next page number
            return {"next_page_number": nextPage}

    def request_params(
        self, stream_state: Mapping[str, Any], stream_slice: Mapping[str, any] = None, next_page_token: Mapping[str, Any] = None
    ) -> MutableMapping[str, Any]:
        return {}

    def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
        serverResponse = response.json()
        if "_embedded" in serverResponse:
            return serverResponse["_embedded"][self.model_name]
        else:
            return []


class ChildStreamMixin:
    parent_stream_class: Optional[HelpscoutMailboxStream] = None

    def stream_slices(self, sync_mode, **kwargs) -> Iterable[Optional[Mapping[str, any]]]:
        for item in self.parent_stream_class(self.access_token, self.parent_stream_model, config=self.config).read_records(sync_mode=sync_mode):
            yield {"id": item["id"]}

        yield from []


class Users(HelpscoutMailboxStream):
    """Return list of all users.
    API Docs: https://developer.helpscout.com/mailbox-api/endpoints/users/list/
    Endpoint: https://api.helpscout.net/v2/users
    """

    primary_key = "id"

    def path(
        self, stream_state: Mapping[str, Any] = None, stream_slice: Mapping[str, Any] = None, next_page_token: Mapping[str, Any] = None
    ) -> str:
        if next_page_token is None:
            return "users"
        else:
            return "users/" + str(next_page_token["next_page_number"])


class Teams(HelpscoutMailboxStream):
    """Return list of all teams.
    API Docs: https://developer.helpscout.com/mailbox-api/endpoints/teams/list-teams/
    Endpoint: https://api.helpscout.net/v2/teams
    """

    primary_key = "id"

    def path(
        self, stream_state: Mapping[str, Any] = None, stream_slice: Mapping[str, Any] = None, next_page_token: Mapping[str, Any] = None
    ) -> str:
        if next_page_token is None:
            return "teams"
        else:
            return "teams/" + next_page_token["next_page_number"]


class TeamMembers(ChildStreamMixin, HelpscoutMailboxStream):
    """Return list of all members of a team.
    API Docs: https://developer.helpscout.com/mailbox-api/endpoints/teams/list-team-members/
    Endpoint: https://api.helpscout.net/v2/teams/{id}/members
    """

    primary_key = "id"

    parent_stream_class = Teams
    parent_stream_model = "teams"

    def path(
        self, stream_state: Mapping[str, Any] = None, stream_slice: Mapping[str, Any] = None, next_page_token: Mapping[str, Any] = None
    ) -> str:
        if next_page_token is None:
            return f"teams/{stream_slice['id']}/members"
        else:
            return f"teams/{stream_slice['id']}/members/{next_page_token['next_page_number']}"


class Conversations(HelpscoutMailboxStream):
    """Return list of all conversations.
    API Docs: https://developer.helpscout.com/mailbox-api/endpoints/conversations/list/
    Endpoint: https://api.helpscout.net/v2/conversations
    """

    primary_key = "id"

    def path(
        self, stream_state: Mapping[str, Any] = None, stream_slice: Mapping[str, Any] = None, next_page_token: Mapping[str, Any] = None
    ) -> str:
        if next_page_token is None:
            return "conversations"
        else:
            return "conversations/" + next_page_token["next_page_number"]


class Threads(ChildStreamMixin, HelpscoutMailboxStream):
    """Return list of all threads from a conversation.
    API Docs: https://developer.helpscout.com/mailbox-api/endpoints/conversations/threads/list/
    Endpoint: https://api.helpscout.net/v2/conversations/{id}/threads
    """

    primary_key = "id"

    # Use 'Mailboxes' stream as parent
    parent_stream_class = Conversations
    parent_stream_model = "conversations"

    def path(
        self, stream_state: Mapping[str, Any] = None, stream_slice: Mapping[str, Any] = None, next_page_token: Mapping[str, Any] = None
    ) -> str:
        if next_page_token is None:
            return f"conversations/{stream_slice['id']}/threads"
        else:
            return f"conversations/{stream_slice['id']}/threads/{next_page_token['next_page_number']}"


class Customers(HelpscoutMailboxStream):
    """Return list of all customers
    API Docs: https://developer.helpscout.com/mailbox-api/endpoints/customers/list/
    Endpoint: https://api.helpscout.net/v2/customers
    """

    primary_key = "id"

    def path(
        self, stream_state: Mapping[str, Any] = None, stream_slice: Mapping[str, Any] = None, next_page_token: Mapping[str, Any] = None
    ) -> str:
        if next_page_token is None:
            return "customers"
        else:
            return "customers/" + next_page_token["next_page_number"]


class CustomerEmails(ChildStreamMixin, HelpscoutMailboxStream):
    """Return list of all emails of a customer
    API Docs: https://developer.helpscout.com/mailbox-api/endpoints/customers/emails/list/
    Endpoint: https://api.helpscout.net/v2/customers/{id}/emails
    """

    primary_key = "id"

    # Use 'Customers' stream as parent
    parent_stream_class = Customers
    parent_stream_model = "customers"

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        return None

    def path(
        self, stream_state: Mapping[str, Any] = None, stream_slice: Mapping[str, Any] = None, next_page_token: Mapping[str, Any] = None
    ) -> str:
        if next_page_token is None:
            return f"customers/{stream_slice['id']}/emails"
        else:
            return f"customers/{stream_slice['id']}/emails/{next_page_token['next_page_number']}"


class CustomerProperties(HelpscoutMailboxStream):
    """Return list of all emails of a customer
    API Docs: https://developer.helpscout.com/mailbox-api/endpoints/customer-properties
    Endpoint: https://api.helpscout.net/v2/customer-properties
    """

    primary_key = "slug"

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        return None

    def path(
        self, stream_state: Mapping[str, Any] = None, stream_slice: Mapping[str, Any] = None, next_page_token: Mapping[str, Any] = None
    ) -> str:
        if next_page_token is None:
            return "customer-properties"
        else:
            return "customer-properties/" + next_page_token["next_page_number"]


class Tags(HelpscoutMailboxStream):
    """Return list of all tags
    API Docs: https://developer.helpscout.com/mailbox-api/endpoints/tags/list/
    Endpoint: https://api.helpscout.net/v2/tags
    """

    primary_key = "id"

    def path(
        self, stream_state: Mapping[str, Any] = None, stream_slice: Mapping[str, Any] = None, next_page_token: Mapping[str, Any] = None
    ) -> str:
        if next_page_token is None:
            return "tags"
        else:
            return "tags/" + next_page_token["next_page_number"]


class Workflows(HelpscoutMailboxStream):
    """Return list of all workflows
    API Docs: https://developer.helpscout.com/mailbox-api/endpoints/workflows/list/
    Endpoint: https://api.helpscout.net/v2/workflows
    """

    primary_key = "id"

    def path(
        self, stream_state: Mapping[str, Any] = None, stream_slice: Mapping[str, Any] = None, next_page_token: Mapping[str, Any] = None
    ) -> str:
        if next_page_token is None:
            return "workflows"
        else:
            return "workflows/" + next_page_token["next_page_number"]


class Webhooks(HelpscoutMailboxStream):
    """Return list of all webhooks
    API Docs: https://developer.helpscout.com/mailbox-api/endpoints/webhooks/list/
    Endpoint: https://api.helpscout.net/v2/webooks
    """

    primary_key = "id"

    def path(
        self, stream_state: Mapping[str, Any] = None, stream_slice: Mapping[str, Any] = None, next_page_token: Mapping[str, Any] = None
    ) -> str:
        if next_page_token is None:
            return "webhooks"
        else:
            return "webhooks/" + next_page_token["next_page_number"]


class Mailboxes(HelpscoutMailboxStream):
    """Return list of all mailboxes
    API Docs: https://developer.helpscout.com/mailbox-api/endpoints/mailboxes/list/
    Endpoint: https://api.helpscout.net/v2/mailboxes
    """

    primary_key = "id"

    def path(
        self, stream_state: Mapping[str, Any] = None, stream_slice: Mapping[str, Any] = None, next_page_token: Mapping[str, Any] = None
    ) -> str:
        if next_page_token is None:
            return "mailboxes"
        else:
            return "mailboxes/" + next_page_token["next_page_number"]

    @property
    def use_cache(self) -> bool:
        return True


class MailboxFolders(ChildStreamMixin, HelpscoutMailboxStream):
    """Return list of all mailbox folders
    API Docs: https://developer.helpscout.com/mailbox-api/endpoints/mailboxes/mailbox-folders/
    Endpoint: https://api.helpscout.net/v2/mailboxes/{id}/folders
    """

    primary_key = "id"

    # Use 'Mailboxes' stream as parent
    parent_stream_class = Mailboxes
    parent_stream_model = "mailboxes"

    def path(
        self, stream_state: Mapping[str, Any] = None, stream_slice: Mapping[str, Any] = None, next_page_token: Mapping[str, Any] = None
    ) -> str:
        if next_page_token is None:
            return f"mailboxes/{stream_slice['id']}/folders"
        else:
            return f"mailboxes/{stream_slice['id']}/folders/{next_page_token['next_page_number']}"


class MailboxCustomFields(ChildStreamMixin, HelpscoutMailboxStream):
    """Return list of all mailbox folders
    API Docs: https://developer.helpscout.com/mailbox-api/endpoints/mailboxes/mailbox-fields/
    Endpoint: https://api.helpscout.net/v2/mailboxes/{id}/fields
    """

    primary_key = "id"

    # Use 'Mailboxes' stream as parent
    parent_stream_class = Mailboxes
    parent_stream_model = "mailboxes"

    def path(
        self, stream_state: Mapping[str, Any] = None, stream_slice: Mapping[str, Any] = None, next_page_token: Mapping[str, Any] = None
    ) -> str:
        if next_page_token is None:
            return f"mailboxes/{stream_slice['id']}/fields"
        else:
            return f"mailboxes/{stream_slice['id']}/fields/{next_page_token['next_page_number']}"


class SourceHelpscoutMailbox(AbstractSource):
    """
    Source Help Scout fetch data from web-based customer communication platform
    """

    def check_connection(self, logger, config) -> Tuple[bool, any]:
        """
        :param config:  the user-input config object conforming to the connector's spec.json
        :param logger:  logger object
        :return Tuple[bool, any]: (True, None) if the input config can be used to connect to the API successfully, (False, error) otherwise.
        """
        try:
            if not config["client_id"]:
                return False, "Help Scout Mailbox - Client Id must be provided."

            if not config["client_secret"]:
                return False, "Help Scout Mailbox - Client Secret must be provided."

            # Test the connection by requesting an Access Token
            helpscoutMailbox = HelpscoutAuthenticator(
                config["client_id"], config["client_secret"])
            helpscoutMailbox.getAccessToken()

            return True, None
        except Exception as e:
            return False, e

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        """
        :param config: A Mapping of the user input configuration as defined in the connector spec.
        """

        token = ""

        if "client_id" in config and "client_secret" in config:
            # Create an instance of the Helpscout API class
            helpscoutMailbox = HelpscoutAuthenticator(
                config["client_id"], config["client_secret"])

            # Oauth2Authenticator is also available if you need oauth support
            token = helpscoutMailbox.getAccessToken()

        return [
            Users(token, "users", config),
            Teams(token, "teams", config),
            Conversations(token, "conversations", config),
            Customers(token, "customers", config),
            Tags(token, "tags", config),
            Workflows(token, "workflows", config),
            Mailboxes(token, "mailboxes", config),
            MailboxFolders(token, "folders", config),
            MailboxCustomFields(token, "fields", config),
            Threads(token, "threads", config),
            CustomerEmails(token, "emails", config),
            TeamMembers(token, "users", config),
            Webhooks(token, "webhooks", config),
            CustomerProperties(token, "customer-properties", config),
        ]
