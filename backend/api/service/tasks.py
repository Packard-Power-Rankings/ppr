from arq import create_pool
from arq.connections import RedisSettings
from api.service.admin_teams import AdminTeamsService


async def run_main_algorithm(ctx, level_key, iterations: int):
    """Runs the main algorithm asynchronously."""
    team_services = AdminTeamsService(level_key)
    print("Did I make it here?")
    await team_services.run_main_algorithm(iterations)


async def calc_z_score(ctx, level_key):
    """Calculates Z-score asynchronously."""
    team_services = AdminTeamsService(level_key)
    await team_services.calculate_z_scores()


class WorkerSettings:
    """Configuration for Arq Worker"""
    functions = [run_main_algorithm, calc_z_score]
    redis_settings = RedisSettings(host="redis", port=6379)
