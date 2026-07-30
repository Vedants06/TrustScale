"""Proxy route for forwarding requests to backend nodes."""

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, Response

from services.load_balancer.routing.forwarder import forward_request
from services.load_balancer.routing.router import select_node
from shared.utils.logger import get_logger

logger = get_logger("proxy")

router = APIRouter()


@router.api_route("/work", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_work(request: Request):
    """Forward work requests to a backend node using the active routing strategy."""
    request_id = str(uuid4())

    selected_node = await select_node()
    if selected_node is None:
        logger.warning("No nodes available for routing", request_id=request_id)
        raise HTTPException(status_code=503, detail="No nodes available")

    body = await request.body()

    try:
        status, response_body, _response_headers = await forward_request(
            node_address=selected_node["address"],
            node_port=selected_node["port"],
            method=request.method,
            path="/work",
            body=body if body else None,
            headers=dict(request.headers),
        )

        logger.info(
            "Request proxied",
            request_id=request_id,
            selected_node=selected_node["node_id"],
            node_address=selected_node["address"],
            node_port=selected_node["port"],
            status=status,
        )

        return Response(
            content=response_body,
            status_code=status,
            media_type="application/json",
        )

    except Exception as error:
        logger.error(
            "Proxy failed",
            request_id=request_id,
            selected_node=selected_node["node_id"],
            error=str(error),
        )
        raise HTTPException(status_code=502, detail="Backend node unavailable")