#!/usr/bin/env python3
"""Print structural workload only; no torch, data reads, provider or GPU calls."""

import json

from mb.v6_performance import workload_audit

if __name__ == "__main__":
    print(json.dumps([workload_audit(text_reference=text) for text in (False, True)], indent=2))
