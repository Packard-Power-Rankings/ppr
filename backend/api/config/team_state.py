from config.config import CONSTANTS_MAP, LEVEL_CONSTANTS

class TeamState():
    def __init__(self):
        self.constants_map = CONSTANTS_MAP
        self.update_info = {}

    @property.getter
    def team_power_ranking(self,level_key, team_name):
        team_info, team_id = self.constants_map[level_key][0:2]
        return team_info[team_id.get(team_name.lower())].get('power_ranking')

    @property.getter
    def team_recent_opp(self, level_key, team_name):
        team_info, team_id = self.constants_map[level_key][0:2]
        return team_info.get(team_id.get(team_name.lower())).get('recent_opp')

    @property.getter
    def team_division(self, level_key, team_name):
        team_name_map, team_id_map, team_division = \
            self.constants_map[level_key][0:3]
        return team_division[
            team_name_map[
                team_id_map.get(team_name.lower())
            ].get('division')
        ]
    @property.getter
    def team_conference(self, level_key, team_name):
        team_name_map, team_id_map, _, team_conf = \
            self.constants_map[level_key]
        return team_conf[
            team_name_map[
                team_id_map.get(team_name.lower())
            ].get('conference')
        ]

    def update_team_info(self):
        pass



class TeamLevels():
    def __init__(self):
        self.level_constants = LEVEL_CONSTANTS
