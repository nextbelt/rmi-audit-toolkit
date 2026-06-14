"""
Production server entrypoint.

Container start order that survives Railway's private network:

1. WAIT for the database to accept a connection. On Railway the DB host is
   ``postgres.railway.internal`` and the private (IPv6) network takes a moment to
   initialize after the container starts. A naive ``migrate`` / app startup that
   connects at t=0 with no timeout can HANG for the whole healthcheck window, so
   the server never binds and every healthcheck returns "service unavailable".
   We poll with a short per-attempt connect timeout until the DB is reachable
   (bounded — we proceed regardless so a real DB outage still yields a running,
   diagnosable container rather than a silent failed deploy).

2. MIGRATE synchronously (Alembic, self-healing) so the schema is at head before
   the app imports — ``main.py``'s startup expects this ordering.

3. SERVE on a single DUAL-STACK socket (IPv6 with IPV6_V6ONLY disabled), handed
   to uvicorn by fd, so the app answers on BOTH IPv6 and IPv4 — Railway's
   private-network healthcheck reaches Dockerfile containers over IPv6, and
   uvicorn's own ``--host`` binds only one stack.
"""
from __future__ import annotations

import os
import socket
import time

import uvicorn


def _log(msg: str) -> None:
    print(f"serve: {msg}", flush=True)


def _dual_stack_socket(port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    # Accept IPv4-mapped connections on the same socket (true dual stack).
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("::", port))
    sock.set_inheritable(True)
    return sock


def _wait_for_db(max_wait: float = 90.0, interval: float = 3.0) -> bool:
    """Poll until the database accepts a connection, bounded by ``max_wait``."""
    from sqlalchemy import create_engine, text

    from config import settings

    url = settings.DATABASE_URL
    # connect_timeout keeps a single attempt from hanging; postgres/psycopg only.
    connect_args = {"connect_timeout": 4} if url.startswith(("postgres", "postgresql")) else {}

    waited = 0.0
    while True:
        try:
            engine = create_engine(url, connect_args=connect_args)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine.dispose()
            _log(f"database reachable after {waited:.0f}s")
            return True
        except Exception as e:  # noqa: BLE001 - retry any connectivity error
            if waited >= max_wait:
                _log(f"database NOT reachable after {waited:.0f}s: {e!r}; continuing anyway")
                return False
            _log(f"waiting for database ({waited:.0f}/{max_wait:.0f}s): {e!r}")
            time.sleep(interval)
            waited += interval


def _run_migrations(retries: int = 5, delay: float = 3.0) -> None:
    """Bring the DB to head (self-healing). Resilient: log and continue on failure."""
    import migrate

    for attempt in range(1, retries + 1):
        try:
            migrate.main()
            _log("migrations complete")
            return
        except Exception as e:  # noqa: BLE001
            _log(f"migrate attempt {attempt}/{retries} failed: {e!r}")
            if attempt < retries:
                time.sleep(delay)
    _log("migrations did NOT complete; serving anyway (investigate DB connectivity)")


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    # _wait_for_db bounds each connection attempt (connect_timeout), so it always
    # returns within max_wait even against a host that hangs. Only migrate once
    # the DB is confirmed reachable — otherwise migrate.main() (which has no
    # connect timeout) could hang past the healthcheck window. Serving anyway
    # keeps /healthz up so the deploy succeeds and the issue is diagnosable.
    db_ok = _wait_for_db(
        max_wait=float(os.environ.get("DB_WAIT_MAX", "60")),
        interval=float(os.environ.get("DB_WAIT_INTERVAL", "3")),
    )
    if db_ok:
        _run_migrations()
    else:
        _log("skipping migrations (database unreachable); serving for liveness + diagnosis")
    sock = _dual_stack_socket(port)
    _log(f"starting uvicorn on dual-stack [::]:{port} (also serves IPv4)")
    uvicorn.run("main:app", fd=sock.fileno(), log_level="info")


if __name__ == "__main__":
    main()
