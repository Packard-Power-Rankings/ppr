import sport_information.models as hs_models
from django.db.models import Q
import math
import copy


def update_record(home_team_id, visitor_team_id, week_id):
    try:
        last_home_weekly_data = hs_models.TeamWeeklyData.objects.filter(
            team_id=home_team_id, week_id__season_id=week_id.season_id).order_by("-week_id__num")[0]
    except:
        return
    try:
        last_visitor_weekly_data = hs_models.TeamWeeklyData.objects.filter(
            team_id=visitor_team_id, week_id__season_id=week_id.season_id).order_by("-week_id__num")[0]
    except:
        return
    home_team_games_this_season = hs_models.Game.objects.filter(Q(week_id__season_id=week_id.season_id) & (
        Q(home_team_id=home_team_id) | Q(visitor_team_id=home_team_id)))
    visitor_team_games_this_season = hs_models.Game.objects.filter(Q(week_id__season_id=week_id.season_id) & (
        Q(home_team_id=visitor_team_id) | Q(visitor_team_id=visitor_team_id)))
    last_home_weekly_data.wins = last_home_weekly_data.losses = last_home_weekly_data.ties = 0
    last_visitor_weekly_data.wins = last_visitor_weekly_data.losses = last_visitor_weekly_data.ties = 0

    for game in home_team_games_this_season:
        if game.home_team_id == home_team_id:
            if game.original_home_score > game.original_visitor_score:
                last_home_weekly_data.wins += 1
            elif game.original_home_score < game.original_visitor_score:
                last_home_weekly_data.losses += 1
            else:
                last_home_weekly_data.ties += 1
        else:
            if game.original_visitor_score > game.original_home_score:
                last_home_weekly_data.wins += 1
            elif game.original_visitor_score < game.original_home_score:
                last_home_weekly_data.losses += 1
            else:
                last_home_weekly_data.ties += 1

    for game in visitor_team_games_this_season:
        if game.visitor_team_id == visitor_team_id:
            if game.original_visitor_score > game.original_home_score:
                last_visitor_weekly_data.wins += 1
            elif game.original_visitor_score < game.original_home_score:
                last_visitor_weekly_data.losses += 1
            else:
                last_visitor_weekly_data.ties += 1
        else:
            if game.original_home_score > game.original_visitor_score:
                last_visitor_weekly_data.wins += 1
            elif game.original_home_score < game.original_visitor_score:
                last_visitor_weekly_data.losses += 1
            else:
                last_visitor_weekly_data.ties += 1

    last_visitor_weekly_data.save()
    last_home_weekly_data.save()
    return last_home_weekly_data, last_visitor_weekly_data


def update_team_record(game, name_to_team):
    """
    Updates the team record based on the game result
    """

    name_to_team[game.home_team_id.name].total_score += (
        game.original_home_score + game.original_visitor_score)
    name_to_team[game.visitor_team_id.name].total_score += (
        game.original_home_score + game.original_visitor_score)
    name_to_team[game.home_team_id.name].num_games += 2
    name_to_team[game.visitor_team_id.name].num_games += 2
    name_to_team[game.home_team_id.name].save()
    name_to_team[game.visitor_team_id.name].save()

    update_record(game.home_team_id, game.visitor_team_id, game.week_id)

    """ if game.original_home_score > game.original_visitor_score:
        name_to_team[game.home_team_id.name].wins += 1
        name_to_team[game.visitor_team_id.name].losses += 1
    elif game.original_home_score < game.original_visitor_score:
        name_to_team[game.home_team_id.name].losses += 1
        name_to_team[game.visitor_team_id.name].wins += 1
    else:
        name_to_team[game.home_team_id.name].ties += 1
        name_to_team[game.visitor_team_id.name].ties += 1 """


# expected perfomance for winning team
def get_expected_performance(expected_wl):
    return ((expected_wl + 2.0) ** 0.45) - (2.0**0.45)


def get_actual_performance(actual_wl):  # actual performance
    if actual_wl >= 0:
        return ((actual_wl + 2.0) ** 0.45) - (2.0**0.45) + 1.0  # XH
    else:
        return -1.0 * ((-1.0 * actual_wl + 2.0) ** 0.45 - (2.0**0.45)) - 1.0


def calculate_power_difference(
    game,
    name_to_team,
    expected_home_wl,
    expected_visitor_wl,
    modified_home_score,
    modified_visitor_score,
    modify_teams,
    home_team_id=None,
    visitor_team_id=None,
):
    if expected_home_wl >= 0:
        expected_home_performance = get_expected_performance(expected_home_wl)
        expected_visitor_performance = expected_home_performance * -1.0
    else:
        expected_visitor_performance = get_expected_performance(
            expected_visitor_wl)
        expected_home_performance = expected_visitor_performance * -1.0

    actual_home_wl = modified_home_score - modified_visitor_score
    actual_visitor_wl = modified_visitor_score - modified_home_score

    actual_performance_home = get_actual_performance(actual_home_wl)
    actual_performance_visitor = get_actual_performance(actual_visitor_wl)

    home_power_change = actual_performance_home - expected_home_performance
    visitor_power_change = actual_performance_visitor - expected_visitor_performance

    if home_team_id is None:
        name_to_team[game.home_team_id.name].temp_actual_change = (
            home_power_change * game.week_id.season_id.sport_id.k_value)
        name_to_team[game.visitor_team_id.name].temp_actual_change = (
            visitor_power_change * game.week_id.season_id.sport_id.k_value)
    else:
        home_team_id.temp_actual_change = (
            home_power_change * game.week_id.season_id.sport_id.k_value)
        visitor_team_id.temp_actual_change = (
            visitor_power_change * game.week_id.season_id.sport_id.k_value)

    if modify_teams:
        name_to_team[game.home_team_id.name].actual_change = name_to_team[game.home_team_id.name].temp_actual_change
        name_to_team[game.visitor_team_id.name].actual_change = name_to_team[game.visitor_team_id.name].temp_actual_change

    if home_team_id is None:
        name_to_team[game.home_team_id.name].power = round(
            name_to_team[game.home_team_id.name].power + name_to_team[game.home_team_id.name].temp_actual_change, 5)
        name_to_team[game.visitor_team_id.name].power = round(
            name_to_team[game.visitor_team_id.name].power + name_to_team[game.visitor_team_id.name].temp_actual_change, 5)
    else:
        home_team_id.power = round(
            home_team_id.power + home_team_id.temp_actual_change, 5)
        visitor_team_id.power = round(
            visitor_team_id.power + visitor_team_id.temp_actual_change, 5)


def calculate_expected_performance(
    game,
    name_to_team,
    modified_home_score,
    modified_visitor_score,
    modify_teams,
    home_team_id=None,
    visitor_team_id=None,
):
    home_field_advantage = 0
    if game.home_field_advantage:
        home_field_advantage = game.week_id.season_id.sport_id.home_advantage

    # Calculate exepcted win/loss, used to calculate expected performance
    if home_team_id is None:
        expected_home_wl = (
            game.home_team_id_weekly_data.power
            - game.visitor_team_id_weekly_data.power
            + home_field_advantage
        )
        expected_visitor_wl = (
            game.visitor_team_id_weekly_data.power
            - game.home_team_id_weekly_data.power
            + (-1.0 * home_field_advantage)
        )
    else:
        expected_home_wl = (home_team_id.power -
                            visitor_team_id.power + home_field_advantage)
        expected_visitor_wl = (
            visitor_team_id.power - home_team_id.power + (-1.0 * home_field_advantage))

    calculate_power_difference(
        game,
        name_to_team,
        expected_home_wl,
        expected_visitor_wl,
        modified_home_score,
        modified_visitor_score,
        modify_teams,
        home_team_id,
        visitor_team_id,
    )


def modify_gameset(game, name_to_team, modify_teams, home_team_id=None, visitor_team_id=None):
    TOTAL = game.week_id.season_id.sport_id.average_game_score
    if game.original_home_score - game.original_visitor_score >= 0:
        modified_home_score = (
            10.0 * TOTAL + 9.0 * game.original_home_score - 10.0 * game.original_visitor_score) / 19.0
        modified_visitor_score = TOTAL - modified_home_score
        mov = game.original_home_score - game.original_visitor_score
        mov_mod = modified_home_score - modified_visitor_score
        if game.original_home_score + game.original_visitor_score == 0:
            mov_mod1 = -9E10
        else:
            mov_mod1 = (50.0 / (game.original_home_score +
                        game.original_visitor_score)) * mov
        mov_mod2 = max(mov_mod, mov_mod1)
        if game.original_home_score + game.original_visitor_score < TOTAL:
            mov_mod2 = mov_mod
        modified_home_score = round(25.0 + 0.5 * mov_mod2, 5)
        modified_visitor_score = round(50.0 - modified_home_score, 5)
    else:
        modified_visitor_score = (
            10.0 * TOTAL + 9.0 * game.original_visitor_score - 10.0 * game.original_home_score) / 19.0
        modified_home_score = TOTAL - modified_visitor_score
        mov = game.original_visitor_score - game.original_home_score
        mov_mod = modified_visitor_score - modified_home_score
        mov_mod1 = (50.0 / (game.original_home_score +
                    game.original_visitor_score)) * mov
        mov_mod2 = max(mov_mod, mov_mod1)
        if game.original_home_score + game.original_visitor_score < TOTAL:
            mov_mod2 = mov_mod
        modified_visitor_score = round(25.0 + 0.5 * mov_mod2, 5)
        modified_home_score = round(50.0 - modified_visitor_score, 5)

    calculate_expected_performance(
        game,
        name_to_team,
        modified_home_score,
        modified_visitor_score,
        modify_teams,
        home_team_id,
        visitor_team_id,
    )


def nested_team_updates(d):
    for key, starting_team in d.items():
        actual_change = starting_team.temp_actual_change
        if actual_change == 0.0:
            continue
        for j in range(1, 6):
            if starting_team.recent_opponents[j] == 0:
                continue
            try:
                depth_1 = d[starting_team.recent_opponents[j]]
            except:
                continue
            for k in range(0, 6):
                if depth_1.recent_opponents[k] == 0:
                    continue
                try:
                    depth_2 = d[depth_1.recent_opponents[k]]
                except:
                    continue
                if k == 0:
                    depth_2.power += (
                        (1.0 / 3.0) * ((0.5) ** (j - 1 + k)) * actual_change
                    )
                    depth_2.temp_loop_change += ((1.0 / 3.0)
                                                 * ((0.5) ** (j - 1 + k)) * actual_change)
                    continue
                for m in range(0, 6):
                    if depth_2.recent_opponents[m] == 0:
                        continue
                    try:
                        depth_3 = d[depth_2.recent_opponents[m]]
                    except:
                        continue
                    if m == 0:
                        depth_3.power += (
                            (1.0 / 3.0) * ((0.5) ** (j - 1 + k + m)) * actual_change
                        )
                        depth_3.temp_loop_change += ((1.0 / 3.0) *
                                                     ((0.5) ** (j - 1 + k + m)) * actual_change)
                        continue
                    for l in range(0, 6):
                        if depth_3.recent_opponents[l] == 0:
                            continue
                        try:
                            depth_4 = d[depth_3.recent_opponents[l]]
                        except:
                            continue
                        if l == 0:
                            depth_4.power += (
                                (1.0 / 3.0)
                                * ((0.5) ** (j - 1 + k + m + l))
                                * actual_change
                            )
                            depth_4.temp_loop_change += ((1.0 / 3.0) * (
                                (0.5) ** (j - 1 + k + m + l)) * actual_change)
                            continue
                        for q in range(0, 6):
                            if depth_4.recent_opponents[q] == 0:
                                continue
                            try:
                                depth_5 = d[depth_4.recent_opponents[q]]
                            except:
                                continue
                            depth_5.power += (
                                (1.0 / 3.0)
                                * ((0.5) ** (j - 1 + k + m + l + q))
                                * actual_change
                            )
                            depth_5.temp_loop_change += ((1.0 / 3.0) * (
                                (0.5) ** (j - 1 + k + m + l + q)) * actual_change)


def update_recent_opponents(team, other_team):
    for i in range(5, 1, -1):
        team.recent_opponents[i] = team.recent_opponents[i - 1]
        other_team.recent_opponents[i] = other_team.recent_opponents[i - 1]

    team.recent_opponents[1] = other_team.team_id.team_num
    other_team.recent_opponents[1] = team.team_id.team_num

    team.recent_opponent_1 = team.recent_opponents[1]
    team.recent_opponent_2 = team.recent_opponents[2]
    team.recent_opponent_3 = team.recent_opponents[3]
    team.recent_opponent_4 = team.recent_opponents[4]
    team.recent_opponent_5 = team.recent_opponents[5]
    other_team.recent_opponent_1 = other_team.recent_opponents[1]
    other_team.recent_opponent_2 = other_team.recent_opponents[2]
    other_team.recent_opponent_3 = other_team.recent_opponents[3]
    other_team.recent_opponent_4 = other_team.recent_opponents[4]
    other_team.recent_opponent_5 = other_team.recent_opponents[5]


def sort_teams_by_division(teams):
    sorted_teams = {}
    for team in teams:
        if team.team_id.division_id not in sorted_teams:
            sorted_teams[team.team_id.division_id] = []
        if (team.team_id.state_id.name == "Colorado" or team.team_id.level != "High School") and team.team_id.division_id != None:
            sorted_teams[team.team_id.division_id].append(team)
        else:
            team.div_rank = -1
    for division in sorted_teams:
        sorted_teams[division].sort(key=lambda x: x.power, reverse=True)

    for division in sorted_teams:
        for i, team in enumerate(sorted_teams[division]):
            team.div_rank = i + 1


def sort_teams_by_rank(teams):
    colorado_teams = []
    for team in teams:

        if (team.team_id.state_id.name == "Colorado" or team.team_id.level != "High School") and team.team_id.division_id != None:
            colorado_teams.append(team)
        else:
            team.overall_rank = -1
            team.save()
    colorado_teams.sort(key=lambda x: x.power, reverse=True)
    for i, team in enumerate(colorado_teams):
        team.overall_rank = i + 1
        team.save()


def create_dicts(teams, modify_teams=True):
    name_to_team = {}
    num_to_team = {}
    for team in teams:
        name_to_team[team.team_id.name] = team
        num_to_team[team.team_id.team_num] = team
        team.temp_actual_change = 0.0
        team.temp_loop_change = 0.0
        if modify_teams:
            team.last_rank = team.overall_rank
        team.recent_opponents = [
            team.team_id.team_num,
            team.recent_opponent_1,
            team.recent_opponent_2,
            team.recent_opponent_3,
            team.recent_opponent_4,
            team.recent_opponent_5,
        ]

    return name_to_team, num_to_team


def standard_deviation(name_to_team, games):
    # games = hs_models.Game.objects.filter(week_id__season_id=season).exclude(home_team_id__isnull=True, visitor_team_id__isnull=True)
    num_games = 0
    if games.count() == 0:
        return 0.0
    actual_change_sum = 0
    for game in games:
        if name_to_team[game.home_team_id.name].temp_actual_change != 0:
            actual_change_sum += name_to_team[game.home_team_id.name].temp_actual_change ** 2
            num_games += 1
        if name_to_team[game.visitor_team_id.name].temp_actual_change != 0:
            actual_change_sum += name_to_team[game.visitor_team_id.name].temp_actual_change ** 2
            num_games += 1
    return math.sqrt(actual_change_sum / num_games)


def get_z_score(games, name_to_team):
    actual_change_sum = 0
    num_games = 0
    for game in games:
        name_to_team[game.home_team_id.name].temp_actual_change_list = name_to_team[game.home_team_id.name].actual_change_list.copy()
        name_to_team[game.visitor_team_id.name].temp_actual_change_list = name_to_team[game.visitor_team_id.name].actual_change_list.copy()
    for game in games:
        if (name_to_team[game.home_team_id.name].temp_actual_change_list[0]) != 0:
            actual_change_sum += name_to_team[game.home_team_id.name].temp_actual_change_list[0] ** 2
            actual_change_sum += name_to_team[game.visitor_team_id.name].temp_actual_change_list[0] ** 2
            num_games += 2
        name_to_team[game.home_team_id.name].temp_actual_change_list.pop(0)
        name_to_team[game.visitor_team_id.name].temp_actual_change_list.pop(0)

    return math.sqrt(actual_change_sum / num_games)


def p(absolute_power_difference):
    return 1.0 / (1.0 + 40.0 * math.e ** (-1.0 * ((absolute_power_difference / 6.0) + 2.0)))


def predict_scores(home_team_weekly_stats, visitor_team_weekly_stats, hfa, sport):
    absolute_power_difference = abs(
        home_team_weekly_stats.power - visitor_team_weekly_stats.power)
    if hfa != None:
        if (home_team_weekly_stats.power + sport.home_advantage >= visitor_team_weekly_stats.power):
            absolute_power_difference += sport.home_advantage
        else:
            absolute_power_difference -= sport.home_advantage

    victory_break_even = (
        (((absolute_power_difference + 2) ** 0.45) - 1.0) ** (20.0 / 9.0)) - 2.0

    victory_break_even = max(victory_break_even, 0)
    # margin of victory
    MOV1 = (1.0 - p(absolute_power_difference)) * absolute_power_difference + \
        p(absolute_power_difference) * victory_break_even

    WIN1 = 25.0 + 0.5 * MOV1
    LOS1 = sport.average_game_score - WIN1

    AVE = sport.average_game_score
    if home_team_weekly_stats.num_games != 0 and visitor_team_weekly_stats.num_games != 0:
        AVE = ((home_team_weekly_stats.total_score / home_team_weekly_stats.num_games) +
               (visitor_team_weekly_stats.total_score / visitor_team_weekly_stats.num_games))  # /2.0?

    WIN2 = (10.0 * AVE + 9.0 * WIN1 - 10.0 * LOS1) / 19.0

    LOS2 = AVE - WIN2
    MOV2 = WIN2 - LOS2
    MOV3 = (AVE / sport.average_game_score) * MOV1
    MOV3 = max(MOV2, MOV3)

    if sport.average_game_score < AVE and MOV3 < MOV2:
        MOV3 = MOV2
    WIN3 = AVE / 2.0 + MOV3 / 2.0
    LOS3 = AVE - WIN3

    if LOS3 < 0:
        WIN3 += abs(LOS3)
        LOS3 = 0
    if (home_team_weekly_stats.power + (sport.home_advantage if hfa else 0) - visitor_team_weekly_stats.power < 0):
        return LOS3, WIN3

    return WIN3, LOS3
