import logging

import begin

logger = logging.getLogger(__name__)


@begin.start
@begin.tracebacks
@begin.logging
def main():
    pass
