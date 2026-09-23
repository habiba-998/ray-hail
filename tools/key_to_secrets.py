"""Convert a Google service-account JSON key into the Streamlit Secrets block RAY expects.

Run it YOURSELF, locally, and paste the printed text into
Streamlit Community Cloud → your app → Settings → Secrets.

    python tools/key_to_secrets.py "C:\\path\\outside\\the\\repo\\ray-streamlit-key.json" ray-hail-2026

It only prints to the terminal. It never writes files and never sends anything anywhere.
Do NOT save the output inside this repository.
"""
import json
import sys


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    try:
        with open(sys.argv[1], encoding="utf-8") as f:
            key = json.load(f)
    except (OSError, ValueError) as exc:
        print(f"Could not read a JSON key from {sys.argv[1]}: {exc}", file=sys.stderr)
        return 1
    if not isinstance(key, dict) or key.get("type") != "service_account" or "private_key" not in key:
        print("This file is not a service-account JSON key.", file=sys.stderr)
        return 1
    project = sys.argv[2] if len(sys.argv) > 2 else key.get("project_id", "")
    lines = [f"EE_PROJECT = {json.dumps(project)}", "", "[ee_service_account]"]
    # JSON string escaping (\n, \", \\, \uXXXX) is valid TOML basic-string escaping
    lines += [f"{k} = {json.dumps(v)}" for k, v in key.items() if isinstance(v, str)]
    print("\n".join(lines))
    print("\n# ↑ Paste everything above into Streamlit Secrets. Do not commit it or save it in the repo.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
