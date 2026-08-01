"""HTTP request forwarder to backend nodes."""

import aiohttp

from shared.utils.logger import get_logger

logger = get_logger("forwarder")


async def forward_request(
    node_address: str,
    node_port: int,
    method: str,
    path: str,
    body: bytes | None = None,
    headers: dict | None = None,
) -> tuple[int, bytes, dict]:
    """Forward an HTTP request to a backend node.

    Args:
        node_address: Node hostname or IP.
        node_port: Node port.
        method: HTTP method.
        path: Request path.
        body: Request body bytes.
        headers: Request headers.

    Returns:
        Tuple of (status_code, response_body, response_headers).
    """
    url = f"http://{node_address}:{node_port}{path}"

    # Filter out hop-by-hop headers
    forward_headers = {}
    if headers:
        skip_headers = {"host", "connection", "keep-alive", "transfer-encoding"}
        forward_headers = {
            k: v for k, v in headers.items()
            if k.lower() not in skip_headers
        }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                data=body,
                headers=forward_headers,
                timeout=aiohttp.ClientTimeout(
                    total=30.0,
                    connect=5.0,
                    sock_read=25.0,
                ),
            ) as response:
                response_body = await response.read()
                response_headers = dict(response.headers)

                logger.debug(
                    "Request forwarded",
                    url=url,
                    status=response.status,
                )

                return response.status, response_body, response_headers

    except Exception as e:
        logger.error("Forward request failed", url=url, error=str(e))
        raise