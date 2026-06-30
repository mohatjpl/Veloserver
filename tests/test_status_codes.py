#!/usr/bin/env python3
"""Status-code tests: bad requests must return 400 (not 200-with-body or 500),
and valid requests must return 200.

Run standalone:  python3 tests/test_status_codes.py
Or via the suite: python3 tests/run_all.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import Results, fetch, recent_time, PROJWIN


def _expect_status(r, name, path, expected):
    status, body, err = fetch(path)
    if err:
        return r.failed(name, f"ERROR {err}")
    msg = body[:80].decode("utf-8", "replace").strip()
    r.check(name, status == expected, f"got {status} (want {expected}) {msg!r}")


def run(r):
    T = recent_time()

    r.section("Bad requests should return 400")
    # gribjson is velocity-only; scalar products must be rejected, not return []
    _expect_status(r, "scalar gribjson -> 400", f"/data?model=hrrr&product=temp_2m&format=gribjson&time={T}", 400)
    _expect_status(r, "unknown product -> 400", f"/data?model=hrrr&product=bogus&format=png&time={T}", 400)
    _expect_status(r, "unknown model -> 400", f"/data?model=mars&format=gribjson&time={T}", 400)
    _expect_status(r, "malformed projwin (3 vals) -> 400",
                   f"/data?model=hrrr&product=winds&format=gribjson&time={T}&projwin=1,2,3", 400)

    r.section("Path-injection / malformed input should return 400 (Sonar S2083)")
    _expect_status(r, "COG unknown product -> 400", f"/cog?product=bogus&time={T}Z", 400)
    _expect_status(r, "COG missing product -> 400", f"/cog?time={T}Z", 400)
    # Malformed COG time must be a clean 400 (parse_cog_time), not a 500. Regression
    # guard: serve_cog used to call fromisoformat outside its try and 500 on bad input.
    _expect_status(r, "COG malformed time -> 400", "/cog?product=winds&time=2024-13-45T99:00:00Z", 400)
    _expect_status(r, "projwin non-numeric -> 400", f"/data?model=gfs&format=gribjson&time={T}&projwin=a,b,c,d", 400)
    _expect_status(r, "projwin dotdot -> 400", f"/data?model=gfs&format=gribjson&time={T}&projwin=..,..,..,..", 400)
    _expect_status(r, "unknown format -> 400", f"/data?model=gfs&format=xml&time={T}", 400)
    _expect_status(r, "missing required params -> 400", "/data?model=hrrr", 400)

    r.section("Valid requests should return 200")
    _expect_status(r, "winds gribjson -> 200", f"/data?model=hrrr&product=winds&format=gribjson&time={T}", 200)
    _expect_status(r, "scalar geotiff -> 200", f"/data?model=hrrr&product=temp_2m&format=geotiff&time={T}", 200)
    _expect_status(r, "gfs gribjson +projwin -> 200",
                   f"/data?model=gfs&format=gribjson&time={T}&projwin={PROJWIN}", 200)


if __name__ == "__main__":
    from helpers import server_up, clear_cache
    if not server_up():
        print("Server not reachable at helpers.BASE — start it (docker compose up -d).")
        sys.exit(2)
    clear_cache()
    r = Results()
    run(r)
    sys.exit(0 if r.summary() else 1)
