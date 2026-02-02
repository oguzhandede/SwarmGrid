"""
Backend HTTP Client for telemetry transmission.
"""

import asyncio
import logging
from typing import List, Optional

import httpx

from config.settings import Settings
from features.feature_builder import TelemetryPayload


logger = logging.getLogger(__name__)


class BackendClient:
    """
    HTTP client for sending telemetry to backend.
    
    Features:
    - Retry logic with exponential backoff
    - Batch buffering
    - Connection pooling
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.telemetry_config = settings.telemetry
        self.base_url = settings.backend_url.rstrip("/")
        
        self._client: Optional[httpx.AsyncClient] = None
        self._buffer: List[TelemetryPayload] = []
        self._lock = asyncio.Lock()
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.telemetry_config.timeout_seconds),
                headers={
                    "Content-Type": "application/json",
                    "X-Camera-Id": self.settings.camera_id,
                    "X-Zone-Id": self.settings.zone_id
                }
            )
        return self._client
        
    async def send_telemetry(self, payload: TelemetryPayload) -> bool:
        """
        Send telemetry data to backend.
        
        Buffers payloads and sends in batches for efficiency.
        
        Args:
            payload: Telemetry payload to send
            
        Returns:
            True if sent successfully (or buffered), False on error
        """
        async with self._lock:
            self._buffer.append(payload)
            
            # Send when buffer is full
            if len(self._buffer) >= self.telemetry_config.batch_size:
                return await self._flush_buffer()
                
        return True
        
    async def _flush_buffer(self) -> bool:
        """Send all buffered telemetry data."""
        if not self._buffer:
            return True
            
        payloads = self._buffer.copy()
        self._buffer.clear()
        
        try:
            client = await self._get_client()
            
            # Convert payloads to JSON
            data = [p.to_dict() for p in payloads]
            
            # Send with retry
            for attempt in range(self.telemetry_config.retry_attempts):
                try:
                    response = await client.post(
                        "/api/telemetry/ingest",
                        json=data
                    )
                    
                    if response.status_code == 200:
                        logger.debug(f"Sent {len(data)} telemetry records")
                        return True
                    elif response.status_code >= 500:
                        # Server error, retry
                        logger.warning(f"Server error {response.status_code}, retrying...")
                        await asyncio.sleep(2 ** attempt)
                    else:
                        # Client error, don't retry
                        logger.error(f"Client error: {response.status_code} - {response.text}")
                        return False
                        
                except httpx.TimeoutException:
                    logger.warning(f"Request timeout, attempt {attempt + 1}")
                    await asyncio.sleep(2 ** attempt)
                except httpx.ConnectError:
                    logger.warning(f"Connection error, attempt {attempt + 1}")
                    await asyncio.sleep(2 ** attempt)
                    
            # All retries failed
            logger.error(f"Failed to send telemetry after {self.telemetry_config.retry_attempts} attempts")
            return False
            
        except Exception as e:
            logger.error(f"Telemetry send error: {e}")
            return False
            
    async def close(self) -> None:
        """Close the HTTP client."""
        # Flush remaining buffer
        async with self._lock:
            await self._flush_buffer()
            
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("Backend client closed")
