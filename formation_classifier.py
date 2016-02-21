from collections import Counter
from collections import defaultdict
import json
import os

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np

DATA_DIR = 'data'
GAME2 = 'full-game-2.json'

SHOTGUN_YARDS_FROM_CENTER = 2

POSITION_CONVERSIONS = {
    'G': 'OG',
    'T': 'OT'
}

def _is_team_roster_file(filename):
    if filename.startswith('team'):
        return True
    return False

def get_player_by_id(data_dir=DATA_DIR):
    player_by_id = {}
    roster_files = filter(_is_team_roster_file, os.listdir(data_dir))
    for roster_file in roster_files:
        roster = json.load(open(os.path.join(data_dir, roster_file)))
        for player in roster['teamPlayers']:
            player_by_id[player['nflId']] = player
    return player_by_id


def _is_special_teams_play(play_json):
    return play_json['play']['isSTPlay']


# Group plays by offensive personnel
def get_personnel(play, player_by_id):
    """ Return set of personnel on the field for offense and defense. """
    away_personnel, home_personnel = set(), set()
    times_seen_by_position = {}
    for tracking_data in ('awayTrackingData', 'homeTrackingData'):
        for player in play[tracking_data]:
            position = player_by_id[player['nflId']]['position']
            position = POSITION_CONVERSIONS.get(position, position)
            if position in times_seen_by_position:
                times_seen_by_position[position] += 1
            else:
                times_seen_by_position[position] = 1
            position += str(times_seen_by_position[position])
            if tracking_data == 'awayTrackingData':
                away_personnel.add(position)
            else:
                home_personnel.add(position)
    if 'QB1' in home_personnel or 'K1' in home_personnel:
        return home_personnel, away_personnel
    return away_personnel, home_personnel


def get_plays_by_offensive_personnel(game, player_by_id):
    plays_by_offensive_personnel = Counter()
    for play in game:
        if _is_special_teams_play(play):
            continue
        offense, defense = get_personnel(play, player_by_id)
        plays_by_offensive_personnel[tuple(sorted(offense))] += 1
    return plays_by_offensive_personnel




def get_formations(game_filename):
    player_by_id = get_player_by_id()
    plays = []
    for line in open(game_filename):
        plays.append(json.loads(line))
    formations = []
    for play in plays:
        if _is_special_teams_play(play):
            continue
        try:
            formations.append(Formation(play, player_by_id))
        except:
            pass
    return formations


def dist_between_start_points(s1, s2):
    return ((s2['x'] - s1['x']) ** 2 + (s1['y'] - s2['y']) ** 2) ** .5




class Formation(object):
    """ Contains position -> starting pos relative to center. """
    def __init__(self, play, player_by_id):
        self.offense = {}
        self.defense = {}
        self.play = play
        self.play_id = play['gsisPlayId']
        offense, defense = self._get_starting_points(play, player_by_id)
        self.offensive_starting_points = offense
        self.defensive_starting_points = defense

    # def compare_offensive_starting_points(self, other):
    #     personnel = self.offensive_personnel()
    #     if other.offensive_personnel() != self.offensive_personnel():
    #         return 100000
    #     for position in ('WR', 'TE'):
    #         if self.left_right_position_numbers(position) != other.left_right_position_numbers(position):
    #             return 100000

    #     other_starts_by_pos = defaultdict(list)
    #     starts_by_pos = defaultdict(list)
    #     for position, start_point in self.offensive_starting_points:
    #         starts_by_pos[position].append(start_point)
    #     for position, start_point in other.offensive_starting_points:
    #         other_starts_by_pos[position].append(start_point)
    #     pos_counts = Counter(personnel)
    #     diff = 0
    #     # single count positions first
    #     for pos, count in pos_counts.iteritems():
    #         if count == 1:
    #             dist = dist_between_start_points(
    #                 starts_by_pos[pos][0],
    #                 other_starts_by_pos[pos][0],
    #             )
    #             diff += dist ** 2
    #             continue
    #         self_used = set()
    #         other_used = set()
    #         distances = []
    #         for self_start_point in starts_by_pos[pos]:
    #             row = []
    #             for other_start_point in other_starts_by_pos[pos]:
    #                 row.append(dist_between_start_points(self_start_point, other_start_point))
    #             distances.append(row)
    #         distances = np.array(distances)
    #         # keep choosing the closest points and leave the others
    #         for i in xrange(len(distances)):
    #             diff += distances.min() ** 2
    #             min_element = distances.argmin()
    #             min_x = min_element % distances.shape[0]
    #             min_y = min_element / distances.shape[0]
    #             np.delete(distances, min_x, axis=0)
    #             np.delete(distances, min_y, axis=1)
    #     return diff

    def get_position_starts(self, position):
        return filter(
            lambda x: x[0] == position,
            self.offensive_starting_points + self.defensive_starting_points
        )

    def graph(self):
        starting_points = self.offensive_starting_points + self.defensive_starting_points
        x = map(lambda x: x[1]['x'], starting_points)
        y = map(lambda x: x[1]['y'], starting_points)
        pos = map(lambda x: x[0], starting_points)
        fig, ax = plt.subplots()
        ax.scatter(x, y)
        for i in xrange(len(x)):
            ax.annotate(pos[i], (x[i], y[i]))
        plt.show()

    def qb_yards_from_center(self):
        qb = filter(lambda x: x[0] == 'QB', self.offensive_starting_points)[0]
        c = filter(lambda x: x[0] == 'C', self.offensive_starting_points)[0]
        return abs(qb[1]['x'] - c[1]['x'])

    def is_shotgun(self):
        return self.qb_yards_from_center() > SHOTGUN_YARDS_FROM_CENTER

    def rb_behind_qb(self):
        rbs = self.get_position_starts('RB')
        qb = self.get_position_starts('QB')[0]
        for rb in rbs:
            if rb[1]['x'] - qb[1]['x'] < 0:
                return True
        return False

    def backfield_players(self):
        """ Return a list of the positions in the backfield. """
        # Assuming players between the tackles and back a few yards are in the back field.
        tackles = self.get_position_starts('OT')
        y_min = min(tackles, key=lambda x: x[1]['y'])[1]['y']
        y_max = max(tackles, key=lambda x: x[1]['y'])[1]['y']
        x_min = min(tackles, key=lambda x: x[1]['x'])[1]['x']
        backfield = []
        for position, start_pos in self.offensive_starting_points:
            if position not in ('RB', 'WR', 'TE', 'FB'):
                continue
            y = start_pos['y']
            x = start_pos['x']
            if y > y_min and y < y_max and x < x_min:
                backfield.append(position)
        return tuple(sorted(backfield))


    def offensive_personnel(self):
        return sorted(map(lambda x: x[0], self.offensive_starting_points))

    def left_right_position_numbers(self, position):
        """ Return number of WRs on each side of the formation. """
        wrs = self.get_position_starts(position)
        left = 0
        right = 0
        for wr in wrs:
            if wr[1]['y'] > 0:
                right += 1
            else:
                left += 1
        return left, right

    def get_offensive_starting_point_features(self):
        features = []
        for pos in ('WR', 'TE', 'RB', 'FB'):
            features.append(self.left_right_position_numbers(pos))
        features.append(self.is_shotgun())
        features.append(self.rb_behind_qb())
        features.append(self.backfield_players())
        features.append(tuple(self.offensive_personnel()))
        return features

    @staticmethod
    def _get_starting_points(play, player_by_id, event='snap'):
        offensive_starting_points = []
        defensive_starting_points = []
        center_starting_point = None
        qb_starting_point = None
        for tracking_data in ('awayTrackingData', 'homeTrackingData'):
            offense = False
            starting_points = []
            for player in play[tracking_data]:
                position = player_by_id[player['nflId']]['position']
                position = POSITION_CONVERSIONS.get(position, position)
                starting_position = filter(
                    lambda x: x.get('event', None) == event,
                    player['playerTrackingData']
                )[0]
                starting_points.append(
                    (position, starting_position.copy())
                )
                if position == 'C':
                    offense = True
                    center_starting_point = starting_position.copy()
                if position == 'QB':
                    qb_starting_point = starting_position.copy()
            if offense:
                offensive_starting_points = starting_points
            else:
                defensive_starting_points = starting_points
        direction = qb_starting_point['x'] < center_starting_point['x']
        for position, starting_point in offensive_starting_points + defensive_starting_points:
            if direction:
                starting_point['x'] -= center_starting_point['x']
                starting_point['y'] -= center_starting_point['y']
            else:
                starting_point['x'] = center_starting_point['x'] - starting_point['x']
                starting_point['y'] = center_starting_point['y'] - starting_point['y']
        return offensive_starting_points, defensive_starting_points



def main(game_filename):
    player_by_id = get_player_by_id()
    formations = get_formations(game_filename)
    plays_by_features = defaultdict(list)
    for formation in formations:
        plays_by_features[tuple(formation.get_offensive_starting_point_features())] = formation
    return plays_by_features