"""
Skillfarm Helper
"""

from celery import signature
from celery_once import AlreadyQueued

from skillfarm.decorators import log_timing
from skillfarm.hooks import get_extension_logger

logger = get_extension_logger(__name__)


def enqueue_next_task(chain):
    """
    Queue next task, and attach the rest of the chain to it.
    """
    while len(chain):
        _t = chain.pop(0)
        _t = signature(_t)
        _t.kwargs.update({"chain": chain})
        try:
            _t.apply_async(priority=9)
        except AlreadyQueued:
            # skip this task as it is already in the queue
            logger.debug("Skipping task as its already queued %s", _t)
            continue
        break


# pylint: disable=too-many-locals, unused-argument
@log_timing(logger)
def update_character_skillfarm(character_id, force_refresh=False):
    pass
