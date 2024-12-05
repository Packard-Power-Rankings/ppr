"""Task creation and storage into
Redis, an in-memory data structure store,
so the algorithm process can run in the back-
ground

    Raises:
        exc: Failure and what is causing
        the failure

    Returns:
        dict: Task completion with results
"""

import asyncio
from celery import states
# from admin_teams import AdminTeamsService
from .admin_teams import AdminTeamsService
from .celery import celery


@celery.task(bind=True, name="api.service.tasks.run_main_algorithm")
def run_main_algorithm(self, level_key, iterations: int):
    try:
        self.update_state(state=states.STARTED)
        if isinstance(level_key, list):
            level_key = tuple(level_key)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        team_services = AdminTeamsService(level_key)
        results = loop.run_until_complete(
            asyncio.sleep(120.0)
        )

        loop.close()

        return {
            "status": "completed",
            "results": results
        }
    except Exception as exc:
        self.update_state(
            state=states.FAILURE,
            meta={
                'exc_type': type(exc).__name__,
                'exc_message': str(exc)
            }
        )
        raise exc
