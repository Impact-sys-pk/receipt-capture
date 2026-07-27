"""Resolution domain logic.

Shared by every caller that resolves a receipt: the CLI, the console, the
back-feed consumer and any future API. This package holds no I/O beyond the
repository it is handed, and never prints, prompts or imports a web framework.
"""
