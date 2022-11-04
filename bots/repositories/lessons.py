from datetime import datetime, timedelta
from typing import List, Optional

import httpx

from config import TIMEZONE, API_URL, AUTH_HEADER


class LessonRepository:
    async def _request(self, url, method="GET", **kwargs) -> Optional[httpx.Response]:
        try:
            async with httpx.AsyncClient(headers=AUTH_HEADER) as client:
                response = await client.request(method, url, **kwargs)
                return response
        except:
            return httpx.Response(status_code=500)

    async def get_study_groups(self) -> Optional[List[str]]:
        request = await self._request(f"{API_URL}/groups")
        if request.status_code == 200:
            result = request.json()
            return result
        return []

    async def get_default_timetable(self, group: str, html=False) -> Optional[List[str]]:
        result = await self._request(f"{API_URL}/timetable/{group}?html={html}&text={not html}")
        if result.status_code == 200:
            return result.json()
        return []

    async def get_changes_timetable(self, group: str, html=False) -> Optional[List[str]]:
        start_date = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
        end_date = (datetime.now(TIMEZONE) + timedelta(days=7)).strftime("%Y-%m-%d")
        result = await self._request(
            f"{API_URL}/changes/finalize_schedule/{group}"
            f"?html={html}&text={not html}"
            f"&start_date={start_date}&end_date={end_date}"
        )
        if result.status_code == 200:
            return result.json()
        return []
