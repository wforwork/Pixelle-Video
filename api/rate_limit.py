# Copyright (C) 2025 AIDC-AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Rate Limiter Setup

Shared limiter instance for all API endpoints.
Uses slowapi with in-memory storage (use Redis for production).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from api.config import api_config


def get_client_ip(request) -> str:
    """Get real client IP, checking X-Forwarded-For header for proxied requests."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# Create shared limiter instance
limiter = Limiter(
    key_func=get_client_ip,
    default_limits=[f"{api_config.rate_limit_per_minute}/minute"] if api_config.rate_limit_enabled else [],
    storage_uri="memory://",
)

# Endpoint-specific limits
VIDEO_RATE_LIMIT = f"{api_config.rate_limit_video_per_minute}/minute" if api_config.rate_limit_enabled else "99999/minute"
IMAGE_RATE_LIMIT = f"{api_config.rate_limit_image_per_minute}/minute" if api_config.rate_limit_enabled else "99999/minute"
