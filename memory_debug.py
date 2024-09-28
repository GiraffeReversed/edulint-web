import os
import tracemalloc
import random
import gc

import objgraph
import astroid
import pylint.checkers.utils
import pylint.message
from flask import request, Blueprint

bp = Blueprint("memory", __name__, url_prefix="/api/memory")

memory_snapshot = None

def _clear_dependency_caches():
    # This functions is NOT thread safe.
    pylint.checkers.utils.clear_lru_caches()
    pylint.message.MessageDefinitionStore.get_message_definitions.cache_clear()
    astroid.MANAGER.clear_cache()
    astroid.raw_building._CONST_PROXY.clear()
    astroid.raw_building._astroid_bootstrapping()
    gc.collect()

def memory_endpoint_authentication():
    # TODO: rework as decorator
    if os.environ.get("MEMORY_DEBUG_PASSWORD", None) is None:
        return "No password for memory debugging, the endpoint is disabled", 500
    if request.args.get("password", None) is None:
        return "Suply the password in query argument `password`", 401
    if os.environ["MEMORY_DEBUG_PASSWORD"] != request.args["password"]:
        return "Incorrect memory debug password", 401
    return None

@bp.route("/snapshot", methods=["GET"])
def memory_test():
    auth = memory_endpoint_authentication()
    if auth is not None:
        return auth

    global memory_snapshot
    tracemalloc.start()
    if not memory_snapshot:
        memory_snapshot = (
            tracemalloc.take_snapshot()
        )  # Take a snapshot of the current memory usage
    else:
        top_stats = tracemalloc.take_snapshot().compare_to(memory_snapshot, "lineno")
        return "\n".join([str(x) for x in top_stats[:100]]), 200
    return "intial snapshot taken", "200"

@bp.route("/growth", methods=["GET"])
def memory_growth():
    auth = memory_endpoint_authentication()
    if auth is not None:
        return auth

    # _clear_dependency_caches()
    return "\n".join([str(x) for x in objgraph.growth(limit=100, shortnames=False)]), "200"

@bp.route("/graphs", methods=["GET"])
def memory_graphs():
    auth = memory_endpoint_authentication()
    if auth is not None:
        return auth

    object_type = request.args["type"]
    object_specific = random.choice(objgraph.by_type(object_type))
    objgraph.show_chain(
        objgraph.find_backref_chain(
            object_specific,
            objgraph.is_proper_module),
        filename='chain-backwards.png')
    objgraph.show_chain(
        objgraph.find_ref_chain(
            object_specific,
            objgraph.is_proper_module),
        filename='chain-forward.png',
        backrefs=False)
    return "OK", 200
