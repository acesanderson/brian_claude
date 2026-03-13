from __future__ import annotations

import os
import pytest


# Skip all integration tests unless YOUTUBE_API_KEY is set
def pytest_collection_modifyitems(config, items):
    skip_integration = pytest.mark.skip(reason="YOUTUBE_API_KEY not set")
    for item in items:
        if "integration" in item.keywords and not os.getenv("YOUTUBE_API_KEY"):
            item.add_marker(skip_integration)
