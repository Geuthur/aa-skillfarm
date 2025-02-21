"""
Skillfarm Helper
"""

import time
from functools import wraps

from bravado.exception import HTTPNotModified
from celery import signature
from celery_once import AlreadyQueued

from django.core.cache import cache

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


def no_fail_chain(func):
    """
    Decorator to chain tasks provided in the chain kwargs regardless of task failures.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        excp = None
        _ret = None
        try:
            _ret = func(*args, **kwargs)
        except Exception as e:  # pylint: disable=broad-exception-caught
            excp = e
        finally:
            _chn = kwargs.get("chain", [])
            enqueue_next_task(_chn)
            if excp:
                raise excp
        return _ret

    return wrapper


MAX_ETAG_LIFE = 60 * 60 * 24 * 7  # 7 Days


class NotModifiedError(Exception):
    pass


def get_etag_key(operation):
    """Get ETag Key"""
    return "skillfarm-" + operation._cache_key()


def get_etag_header(operation):
    """Get Cached ETag"""
    return cache.get(get_etag_key(operation), False)


def del_etag_header(operation):
    """Delete Cached ETag"""
    return cache.delete(get_etag_key(operation), False)


def inject_etag_header(operation):
    """Inject ETag header"""
    etag = get_etag_header(operation)
    logger.debug(
        "ETag: get_etag %s - %s - etag:%s",
        operation.operation.operation_id,
        stringify_params(operation),
        etag,
    )
    if etag:
        operation.future.request.headers["If-None-Match"] = etag


def rem_etag_header(operation):
    """Remove ETag header"""
    logger.debug(
        "ETag: rem_etag %s - %s",
        operation.operation.operation_id,
        stringify_params(operation),
    )
    if "If-None-Match" in operation.future.request.headers:
        del operation.future.request.headers["If-None-Match"]
        return True
    return False


def set_etag_header(operation, headers):
    """Set ETag header"""
    etag_key = get_etag_key(operation)
    etag = headers.headers.get("ETag", None)
    if etag is not None:
        result = cache.set(etag_key, etag, MAX_ETAG_LIFE)
        logger.debug(
            "ETag: set_etag %s - %s - etag: %s - stored: %s",
            operation.operation.operation_id,
            stringify_params(operation),
            etag,
            result,
        )
        return True
    return False


def stringify_params(operation):
    """Stringify Operation Params"""
    out = []
    for p, v in operation.future.request.params.items():
        out.append(f"{p}: {v}")
    return ", ".join(out)


def handle_etag_headers(operation, headers, force_refresh, etags_incomplete):
    """Handle ETag headers"""
    if (
        get_etag_header(operation) == headers.headers.get("ETag")
        and not force_refresh
        and not etags_incomplete
    ):
        logger.debug("Etag: No modified Data for %s", operation.operation.operation_id)
        raise NotModifiedError()

    if force_refresh:
        logger.debug(
            "ETag: Removing Etag %s F:%s - %s",
            operation.operation.operation_id,
            force_refresh,
            stringify_params(operation),
        )
        del_etag_header(operation)
    else:
        logger.debug(
            "ETag: Saving Etag %s F:%s - %s",
            operation.operation.operation_id,
            force_refresh,
            stringify_params(operation),
        )
        set_etag_header(operation, headers)


def handle_page_results(
    operation, current_page, total_pages, etags_incomplete, force_refresh
):
    """Handle multiple page results and use Cache if possible"""
    results = []
    while current_page <= total_pages:
        operation.future.request.params["page"] = current_page
        try:
            if not etags_incomplete and not force_refresh:
                inject_etag_header(operation)
            else:
                rem_etag_header(operation)

            result, headers = operation.result()
            total_pages = int(headers.headers["X-Pages"])
            handle_etag_headers(operation, headers, force_refresh, etags_incomplete)
            results += result
            current_page += 1

        except (HTTPNotModified, NotModifiedError) as e:
            logger.debug(e)
            if isinstance(e, NotModifiedError):
                total_pages = int(headers.headers["X-Pages"])
            else:
                total_pages = int(e.response.headers["X-Pages"])

            if not etags_incomplete:
                current_page += 1
            else:
                current_page = 1
                results = []
                etags_incomplete = False
    return results, current_page, total_pages


def etag_results(operation, token, force_refresh=False):
    """Handle ETag results"""
    _start_tm = time.perf_counter()
    operation.request_config.also_return_response = True
    if token:
        operation.future.request.headers["Authorization"] = (
            "Bearer " + token.valid_access_token()
        )
    if "page" in operation.operation.params:
        current_page = 1
        total_pages = 1
        etags_incomplete = False
        results, current_page, total_pages = handle_page_results(
            operation, current_page, total_pages, etags_incomplete, force_refresh
        )
    else:
        if not force_refresh:
            inject_etag_header(operation)
        try:
            results, headers = operation.result()
        except HTTPNotModified as e:
            logger.debug("ETag: Not Modified %s", operation.operation.operation_id)
            set_etag_header(operation, e.response)
            raise NotModifiedError() from e
        handle_etag_headers(operation, headers, force_refresh, etags_incomplete=False)
    logger.debug(
        "ESI_TIME: OVERALL %s %s %s",
        time.perf_counter() - _start_tm,
        operation.operation.operation_id,
        stringify_params(operation),
    )
    return results
