#!/usr/bin/env python3
"""Local help/identity checks only. Never sends a target to the tools."""
import json
from echo_recon.tools import diagnostics

if __name__ == "__main__":
    print(json.dumps(diagnostics(), indent=2, ensure_ascii=False))
