"""
OmniRoute authentication probe — is a Bearer key required (and is a session)?

Goal: decide, with evidence, what the OmniRoute gateway requires for a chat
completion. The gateway now enforces ``Authorization: Bearer`` (no key -> 401
"Authentication required"); a key is read platform-aware exactly like the
runtime (Windows -> OMNIROUTE_API_KEY, Linux -> OMNIROUTE_TASKQUEST_API_KEY).
Every case below issues the SAME minimal judge-style chat completion against
the SAME single combo id, changing only the HTTP headers, so the only variable
under test is authentication. No retries, no fallbacks, no silent dedup — each
row is one raw request and its exact outcome.

Combo under test: ``free-coders`` ONLY. No other model/combo is ever sent.
The effective combo can be overridden via OMNIROUTE_MODEL, and a loud warning
is printed if you do.

Run it with the OmniRoute gateway up (default http://127.0.0.1:20128/v1;
point it at a live gateway with OMNIROUTE_URL, e.g. http://ajay-hp.local:20128/v1):

    venv\\Scripts\\python.exe app\\test\\probe_omniroute_auth.py
    venv\\Scripts\\python.exe app\\test\\probe_omniroute_auth.py --cases 1,5,7
    venv\\Scripts\\python.exe app\\test\\probe_omniroute_auth.py --timeout 15

Exit code: 0 when at least one case got a valid model response, 2 otherwise.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO = Path(__file__).resolve().parents[2]

# ── Combo under test (the ONLY model ever sent) ─────────────────────────────
MODEL = os.getenv("OMNIROUTE_MODEL", "free-coders")
BASE_URL = (os.getenv("OMNIROUTE_URL") or "http://127.0.0.1:20128/v1").rstrip("/")

# Platform-aware key var, mirroring ai_assistant._resolve_api_key_env().
BEARER_ENV = "OMNIROUTE_API_KEY" if os.name == "nt" else "OMNIROUTE_TASKQUEST_API_KEY"

PROMPT_SYSTEM = "You are a strict but fair system judge. Reply with JSON only."
PROMPT_USER = ('Classify this skip reason quality. Return JSON only: '
               '{"validity": 0-100, "notes": "..."}\n'
               "Reason: An unexpected family emergency came up.")

OPENCODE_DB = Path(os.path.expanduser("~")) / ".local" / "share" / "opencode" / "opencode.db"

# Known locations of the deterministic fallback (so nothing is "undocumented"):
FALLBACK_LOCATIONS = [
    "app/utils/managers/penalty_evaluator.py      (metric-based scores when the LLM is unreachable)",
    "app/utils/managers/judge_manager.py          (PROVISIONAL marker explanation when Unreachable)",
    "app/utils/judge_status.py                    (LIVE / PROVISIONAL / OFF pill states)",
]


def discover_real_session_id() -> str | None:
    """Best-effort: find a live opencode session id to test against.

    Order: env var OMNIROUTE_SESSION_ID, then the most recently used opencode
    session for this machine from the opencode sqlite store, then None.
    """
    env = os.getenv("OMNIROUTE_SESSION_ID")
    if env and env.strip():
        return env.strip()
    if not OPENCODE_DB.exists():
        return None
    try:
        con = sqlite3.connect("file:" + str(OPENCODE_DB).replace("\\", "/") + "?mode=ro", uri=True)
        try:
            rows = con.execute(
                "SELECT id, directory, title FROM session "
                "WHERE parent_id IS NULL ORDER BY time_created DESC LIMIT 25"
            ).fetchall()
        finally:
            con.close()
        if not rows:
            return None
        # Prefer the newest non-subagent session whose directory intersects this
        # repo or its parents; fall back to the newest session overall.
        repo_parts = {str(REPO).lower(), str(REPO.parent).lower()}
        for sid, directory, _title in rows:
            if directory and str(directory).lower() in repo_parts:
                return sid
        return rows[0][0]
    except Exception:
        return None


def _mask_token(value: str | None) -> str:
    if value is None:
        return "NONE"
    if len(value) <= 8:
        return value or '"" (empty)'
    return value[:5] + "…" + value[-4:] + f" (len {len(value)})"


def _valid_json(text: str) -> bool:
    try:
        data = json.loads(text)
        return isinstance(data, dict)
    except (ValueError, TypeError):
        return False


def raw_chat(headers: dict, timeout: float) -> tuple[int, float, str]:
    """One POST /chat/completions with EXACTLY the given headers (urllib)."""
    url = BASE_URL + "/chat/completions"
    body = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": PROMPT_SYSTEM},
            {"role": "user", "content": PROMPT_USER},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            return resp.status, time.monotonic() - started, text
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", errors="replace")
        return e.code, time.monotonic() - started, text
    except urllib.error.URLError as e:
        return 0, time.monotonic() - started, f"URLError: {e.reason}"
    except TimeoutError:
        return 0, time.monotonic() - started, f"TIMEOUT after {timeout:g}s"


def sdk_chat(api_key: str, extra_headers: dict | None, timeout: float) -> tuple[int, float, str]:
    """Mirror the exact runtime path (openai SDK like ai_assistant.py)."""
    url = BASE_URL + "/chat/completions"
    hdrs = {"Content-Type": "application/json"}
    if api_key is not None:
        hdrs["Authorization"] = "Bearer " + api_key
    if extra_headers:
        hdrs.update(extra_headers)
    return raw_chat(hdrs, timeout)


def describe(text: str) -> str:
    if not text.strip():
        return "empty body"
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "error" in data:
            err = data["error"]
            if isinstance(err, dict):
                return f'error: {err.get("message") or err}'[:220]
            return f"error: {err}"[:220]
    except (ValueError, TypeError):
        pass
    return text[:220].replace("\n", " ")


def is_router_error(text: str) -> bool:
    low = text.lower()
    return any(k in low for k in ("insufficient_quota", "is not supported",
                                  "permission_error", "invalid api key",
                                  "model_not_found", "provider"))


ROUTER_HITS: set[str] = set()


def build_cases(session_real: str | None, session_fake: str, bearer_env: str | None):
    bearer_app = bearer_env or "not-needed"
    # Minimal raw headers (mirrors a bare HTTP client)
    no_h: dict = {"Content-Type": "application/json"}
    with_h: dict = {"Content-Type": "application/json", "Authorization": "Bearer " + bearer_app}
    sh_real = {"Content-Type": "application/json", "x-opencode-session": session_real}
    sh_fake = {"Content-Type": "application/json", "x-opencode-session": session_fake}
    both_real = {"Content-Type": "application/json",
                 "Authorization": "Bearer " + bearer_app,
                 "x-opencode-session": session_real}
    # SDK-like raw headers (what the openai SDK actually sends)
    sdk_style = {"Content-Type": "application/json",
                 "Accept": "application/json",
                 "User-Agent": "openai-python/1.x omni-judge-probe"}
    sdk_no = dict(sdk_style)
    sdk_real = {**sdk_style, "x-opencode-session": session_real}
    sdk_fake = {**sdk_style, "x-opencode-session": session_fake}
    return [
        ("C01", "no session, Bearer 'not-needed'  (REST_MINIMAL app default w/o envs)",
         no_h, "no", "raw"),
        ("C02", "no session, no Authorization header at all",
         dict(no_h), "no", "raw"),
        ("C03", "no session, Bearer <real/any key>",
         dict(with_h), "no", "raw"),
        ("C04", "x-opencode-session=REAL id, no Bearer",
         dict(sh_real), "real", "raw"),
        ("C05", "x-opencode-session=<arbitrary uuid>, no Bearer",
         dict(sh_fake), "fake", "raw"),
        ("C06", "x-opencode-session=REAL id + Bearer (full auth, REST_MINIMAL)",
         dict(both_real), "real", "raw"),
        ("C07", "x-opencode-session=<arbitrary uuid> + Bearer",
         dict({**sh_fake, "Authorization": "Bearer " + bearer_app}), "fake", "raw"),
        ("C08", "Authorization: Bearer '' (empty) + x-opencode-session=REAL",
         dict({"Content-Type": "application/json", "Authorization": "Bearer ",
               "x-opencode-session": session_real}), "real", "raw"),
        ("C09", "SDK-style headers (Accept+UA), no session, no Bearer",
         dict(sdk_no), "no", "raw"),
        ("C10", "SDK-style headers, no session, Bearer real/not-needed",
         dict({**sdk_no, "Authorization": "Bearer " + bearer_app}), "no", "raw"),
        ("C11", "SDK-style headers, session=REAL, no Bearer",
         dict(sdk_real), "real", "raw"),
        ("C12", "SDK-style headers, session=<arbitrary uuid>, no Bearer",
         dict(sdk_fake), "fake", "raw"),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cases", help="comma list, e.g. 1,5,7 (default: all)")
    parser.add_argument("--timeout", type=float, default=30.0,
                        help="per-case timeout in seconds (app default is 90s)")
    parser.add_argument("--session", default=None,
                        help="session id to treat as REAL (default: env/discovery)")
    parser.add_argument("--quiet-sdk", action="store_true",
                        help="skip the openai SDK parity case at the end")
    args = parser.parse_args()

    if args.cases:
        wanted = {int(x) for x in args.cases.split(",")}
    else:
        wanted = None

    if MODEL != "free-coders":
        print(f"!! WARNING: OMNIROUTE_MODEL is set to '{MODEL}', not 'free-coders'.\n"
              "   The probe will send THIS combo only (never any other).")

    real = args.session or discover_real_session_id()
    fake = str(uuid.uuid4())
    bearer_env = os.getenv(BEARER_ENV)
    if bearer_env:
        print(f"{BEARER_ENV} found: {_mask_token(bearer_env)}")
    else:
        print(f"{BEARER_ENV} not set -> probes use 'not-needed' or no Bearer at all")

    print(f"gateway        : {BASE_URL}/chat/completions")
    print(f"combo (only)   : {MODEL}")
    print(f"real session   : {real or 'NONE found'}")
    print(f"arbitrary ssn  : {fake}")
    print(f"timeout        : {args.timeout:g}s per case (warn: app uses 90s)")
    print()

    cases = build_cases(real, fake, bearer_env)
    results = []
    for cid, name, headers, ssn_kind, via in cases:
        if wanted is not None and int(cid[1:]) not in wanted:
            continue
        shown = {k: v for k, v in headers.items() if k.lower() not in ("authorization", "x-opencode-session")}
        shown["Authorization"] = ("Bearer " + _mask_token(
            headers.get("Authorization", "not-needed").replace("Bearer ", ""))) \
            if headers.get("Authorization") else "ABSENT"
        shown["x-opencode-session"] = _mask_token(headers.get("x-opencode-session")) \
            if headers.get("x-opencode-session") else "ABSENT"
        print(f"-- {cid}  {name}")
        print(f"   headers: {shown}")
        status, elapsed, text = raw_chat(headers, args.timeout)
        ok = status == 200 and _valid_json(text)
        if is_router_error(text):
            ROUTER_HITS.add(cid)
        print(f"   -> HTTP {status if status else '---'} in {elapsed:6.2f}s  "
              f"{'VALID' if ok else 'INVALID'}  :: {describe(text)}")
        print()
        results.append((cid, status, ok, ssn_kind, via, elapsed))

    if not args.quiet_sdk:
        def _sdk_case(label, ssn_kind, api_key, extra):
            try:
                from openai import OpenAI  # noqa: PLC0415
            except Exception:
                print("   openai SDK not importable; skipping parity cases")
                return False
            print(f"-- {label}")
            client = OpenAI(base_url=BASE_URL, api_key=api_key,
                            timeout=args.timeout, max_retries=0,
                            default_headers=extra or None)
            started = time.monotonic()
            try:
                resp = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "system", "content": PROMPT_SYSTEM},
                              {"role": "user", "content": PROMPT_USER}],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                )
                print(f"   -> HTTP 200 in {time.monotonic() - started:6.2f}s  VALID")
                results.append((label.split()[0], 200, True, ssn_kind, "sdk",
                                time.monotonic() - started))
            except Exception as e:
                detail = str(e)[:260].replace("\n", " ")
                status = getattr(getattr(e, "response", None), "status_code", 0)
                print(f"   -> HTTP {status if status else '---'} in "
                      f"{time.monotonic() - started:6.2f}s  INVALID  :: {detail}")
                if is_router_error(detail):
                    ROUTER_HITS.add(label.split()[0])
                results.append((label.split()[0], status, False, ssn_kind, "sdk",
                                time.monotonic() - started))
            return True

        _sdk_case("SDK-PARITY  no session, Bearer 'not-needed' (exact app default)",
                  "no", "not-needed", None)
        _sdk_case("SDK        session=REAL + Bearer",
                  "real", bearer_env or "not-needed",
                  {"x-opencode-session": real})
        _sdk_case("SDK        session=<arbitrary uuid> + Bearer",
                  "fake", bearer_env or "not-needed",
                  {"x-opencode-session": fake})
        print()

    # ── Conclusion ──
    print("=" * 78)
    print("RESULT TABLE")
    print(f"{'case':<5}{'http':<6}{'valid':<6}{'session':<8}{'via':<5} outcome")
    for cid, status, ok, ssn_kind, via, _el in results:
        print(f"{cid:<5}{status if status else '---':<6}{'YES' if ok else 'no':<6}"
              f"{ssn_kind:<8}{via:<5} {'accepted' if ok else 'rejected/down'}")
    print()
    print("CONCLUSION")
    no_session_ok = any(ok for _c, _s, ok, kind, _v, _e in results if kind == "no")
    real_ok = any(ok for _c, _s, ok, kind, _v, _e in results if kind == "real")
    fake_ok = any(ok for _c, _s, ok, kind, _v, _e in results if kind == "fake")
    any_ok = any(ok for _c, _s, ok, _kind, _v, _e in results)
    if not any_ok and not results:
        print("  No cases ran.")
    elif no_session_ok:
        print("  -> x-opencode-session is NOT required: at least one no-session case returned a")
        print("    valid model response. TaskQuest can omit OMNIROUTE_SESSION_ID.")
    elif real_ok and fake_ok:
        print("  -> A session HEADER is required but ANY value works: the gateway only checks")
        print("    presence of x-opencode-session. Set OMNIROUTE_SESSION_ID to anything.")
    elif real_ok:
        print("  -> The gateway requires the header to carry a REAL opencode session id; an")
        print("    arbitrary value is rejected. TaskQuest must set OMNIROUTE_SESSION_ID to a")
        print("    live opencode session id.")
    elif any_ok:
        print("  -> VALID only for a different session/bearer combination. Inspect the table above.")
    elif ROUTER_HITS:
        print("  -> The gateway ACCEPTED the requests (reached the model router) in every")
        print("    tested header combo, but the router then rejected resolution of the combo")
        print(f"    '{MODEL}' at the PROVIDER layer. Error signature seen in:")
        print(f"    {sorted(ROUTER_HITS)}  (insufficient_quota / 'not supported' / permission_error).")
        print()
        print("    That is NOT an x-opencode-session problem: the session header never gates")
        print("    this - the combo's backing provider connection (e.g. OmniRoute <-> Google")
        print("    auth / quota) is what is failing. Fix the provider connection in OmniRoute")
        print("    or pick a combo whose backing provider is authenticated.")
    else:
        print("  -> No case yielded a valid response. The gateway is either down (all show ---/")
        print("    TIMEOUT), or the combo 'free-coders' does not exist / is not routable there.")
        print("    Check OmniRoute is running on", BASE_URL, "and that the combo is enabled.")
    print()
    print("In the app, when every request fails this probe the runtime does NOT surface raw")
    print("errors: it silently falls back to deterministic metrics. Where those live:")
    for line in FALLBACK_LOCATIONS:
        print("   -", line)
    return 0 if any_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())