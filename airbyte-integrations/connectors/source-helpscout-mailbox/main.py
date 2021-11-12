#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_helpscout_mailbox import SourceHelpscoutMailbox

if __name__ == "__main__":
    source = SourceHelpscoutMailbox()
    launch(source, sys.argv[1:])
