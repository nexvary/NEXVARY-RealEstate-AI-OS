from __future__ import annotations

import argparse
import base64
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization


PRODUCT_ID = "real-estate-business-os"
ALL_FEATURES = ["crm", "inventory", "finance", "omnichannel", "growth", "seo", "automation", "ai"]


def canonical(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def create_license(private_key_path: Path, company: str, customer: str, machine_code: str, days: int, edition: str) -> dict:
    if not company.strip() or not customer.strip():
        raise ValueError("Company and customer are required")
    normalized_machine = machine_code.strip().upper()
    if normalized_machine != "*" and (len(normalized_machine) != 29 or any(len(part) != 4 for part in normalized_machine.split("-"))):
        raise ValueError("Computer code must be the six-part code shown in the application")
    if days < 0:
        raise ValueError("Validity days cannot be negative")
    private_key = serialization.load_pem_private_key(private_key_path.read_bytes(), password=None)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    expires_at = None if days == 0 else (now + timedelta(days=days)).isoformat().replace("+00:00", "Z")
    payload = {
        "product": PRODUCT_ID,
        "license_id": str(uuid.uuid4()),
        "customer": customer.strip(),
        "company": company.strip(),
        "machine_code": normalized_machine,
        "edition": edition,
        "features": ALL_FEATURES,
        "issued_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": expires_at,
    }
    signature = private_key.sign(canonical(payload))
    return {"payload": payload, "signature": base64.b64encode(signature).decode("ascii")}


def run_gui() -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    window = tk.Tk()
    window.title("White-Label License Manager")
    window.geometry("760x610")
    window.configure(bg="#07111D")
    values = {name: tk.StringVar() for name in ("key", "company", "customer", "machine", "days", "edition", "output")}
    values["days"].set("365")
    values["edition"].set("professional")
    values["output"].set(str(Path.cwd() / "customer.license"))

    style = ttk.Style(window)
    style.theme_use("clam")
    style.configure("TLabel", background="#07111D", foreground="#EAF3FA", font=("Segoe UI", 11))
    style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=9)
    frame = ttk.Frame(window, padding=28)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="WHITE-LABEL LICENSE MANAGER", font=("Segoe UI", 20, "bold"), foreground="#39C8FF").pack(anchor="w", pady=(0, 18))

    def row(label: str, key: str, browse: bool = False):
        ttk.Label(frame, text=label).pack(anchor="w", pady=(8, 3))
        line = ttk.Frame(frame)
        line.pack(fill="x")
        ttk.Entry(line, textvariable=values[key], font=("Segoe UI", 11)).pack(side="left", fill="x", expand=True)
        if browse:
            ttk.Button(line, text="Browse", command=lambda: values[key].set(filedialog.askopenfilename() or values[key].get())).pack(side="left", padx=(8, 0))

    row("Vendor private key (keep secret)", "key", True)
    row("Licensed company", "company")
    row("Customer / contact name", "customer")
    row("Computer code", "machine")
    row("Validity in days (0 = perpetual)", "days")
    row("Edition", "edition")
    row("Output license file", "output")

    def generate():
        try:
            document = create_license(
                Path(values["key"].get()), values["company"].get(), values["customer"].get(),
                values["machine"].get(), int(values["days"].get()), values["edition"].get())
            output = Path(values["output"].get())
            output.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
            messagebox.showinfo("License created", f"Saved to:\n{output}")
        except Exception as exc:
            messagebox.showerror("Could not create license", str(exc))

    ttk.Button(frame, text="GENERATE SIGNED LICENSE", command=generate).pack(fill="x", pady=(24, 0))
    window.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate signed customer licenses")
    parser.add_argument("--private-key")
    parser.add_argument("--company")
    parser.add_argument("--customer")
    parser.add_argument("--machine-code")
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--edition", default="professional")
    parser.add_argument("--output")
    args = parser.parse_args()
    if not args.private_key:
        run_gui()
        return
    required = (args.company, args.customer, args.machine_code, args.output)
    if not all(required):
        parser.error("--company, --customer, --machine-code and --output are required in CLI mode")
    document = create_license(Path(args.private_key), args.company, args.customer, args.machine_code, args.days, args.edition)
    Path(args.output).write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
