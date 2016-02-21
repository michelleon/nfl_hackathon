from collections import defaultdict
import json
import os

import matplotlib.pyplot as plt
import numpy as np


DATA_DIR = 'data'
GAME2 = 'data/full-game-2.json'
GAME3 = 'data/full-game-3.json'

POSITION_CONVERSIONS = {
    'G': 'OG',
    'T': 'OT'
}

POSITIONS_TO_DRAW_ROUTES_FOR = (
    'WR', 'RB', 'TE'
)

NUM_PLAYERS_ON_FIELD = 11


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


def iterate_plays_for_game(game_filename):
    for line in open(game_filename):
        yield json.loads(line)


def _is_special_teams_play(play_json):
    return play_json['play']['isSTPlay']


class Play(object):
    def __init__(self, play, player_by_id, play_start_event='snap'):
        self.player_by_id = player_by_id
        self.play_start_event = play_start_event
        self.id = play['ngsPlayId']
        self.play = play
        self._load_play_data(play)
        self._compute_relative_data()

    def graph(self):
        start_idx = self.get_start_idx()
        x = self.player_x_data_relative[:, start_idx]
        y = self.player_y_data_relative[:, start_idx]
        fig, ax = plt.subplots()
        ax.scatter(x, y)
        for i in xrange(len(x)):
            ax.annotate(self.positions[i], (x[i], y[i]))
        plt.show()

    def get_player_position(self, player_id):
        position = self.player_by_id[player_id]['position']
        return POSITION_CONVERSIONS.get(
            position, position
        )

    def get_start_idx(self):
        return np.where(self.events == self.play_start_event)[0][0]

    def get_start_positions(self):
        start_idx = self.get_start_idx()
        return self.player_x_data_relative[:, start_idx], self.player_y_data_relative[:, start_idx]

    @staticmethod
    def iter_players_in_play(play):
        for player in play['homeTrackingData']:
            yield player
        for player in play['awayTrackingData']:
            yield player

    def left_right_split_for_position(self, pos):
        """ Return the number of players of the position to the left and right of the center. """
        pos_idxs = np.where(self.positions == pos)[0]
        start_idx = self.get_start_idx()
        pos_xs = self.player_y_data_relative[pos_idxs][:, start_idx]
        total = len(pos_xs)
        left = sum(pos_xs < 0)
        right = total - left
        return left, right

    def is_shotgun(self):
        qb_x, qb_y = self._get_pos_starts('QB')
        c_x, c_y = self._get_pos_starts('C')
        if c_x[0] - qb_x[0] > 2:
            return True

    def is_rb_behind_qb(self):
        qb_x, qb_y = self._get_pos_starts('QB')
        rb_x, rb_y = self._get_pos_starts('RB')
        if qb_x[0] - rb_x[0] > 0.5:
            return True
        return False

    def rb_left_center_right(self):
        """ Return if the rb is left, center, or right of the QB"""
        qb_x, qb_y = self._get_pos_starts('QB')
        rb_x, rb_y = self._get_pos_starts('RB')
        if abs(qb_y[0] - rb_y[0]) < 0.5:
            return 'center'
        if qb_y[0] - rb_y[0] > 0:
            return 'right'
        return 'left'

    def left_right_wr_tight(self):
        """ Left and right counts for WRs lined up by the offensive line. """
        # WRs within 3 yards of OT
        ot_x, ot_y = self._get_pos_starts('OT')
        wr_x, wr_y = self._get_pos_starts('WR')


    def players_in_backfield(self):
        """ Return list of the positions of players in the backfield.
        Defining backfield as between and behind the tackles by at least a yard. """
        OT_x, OT_y = self._get_pos_starts('OT')
        y_min = OT_y.min()
        y_max = OT_y.max()
        x_min = OT_x.min() - 1
        start_idx = self.get_start_idx()
        xs = self.player_x_data_relative[:, start_idx]
        ys = self.player_y_data_relative[:, start_idx]
        backfield_players = (ys > y_min) & (ys < y_max) & (xs < x_min)
        return tuple(self.positions[backfield_players])

    def offensive_personnel(self):
        qb_idx = np.where(self.positions == 'QB')[0][0]
        if qb_idx < 11:
            return tuple(sorted(self.positions[:NUM_PLAYERS_ON_FIELD]))
        else:
            return tuple(sorted(self.positions[NUM_PLAYERS_ON_FIELD:]))

    def get_offense_formation_features(self):
        return (
            ('shotgun', self.is_shotgun()),
            ('wr_split', self.left_right_split_for_position('WR')),
            ('te_split', self.left_right_split_for_position('TE')),
            ('rb_behind_qb', self.is_rb_behind_qb()),
            ('players_in_backfield', self.players_in_backfield()),
            ('offensive_personnel', self.offensive_personnel()),
            ('rb_left_center_right', self.rb_left_center_right()),
        )

    def _get_pos_starts(self, pos):
        pos_idxs = np.where(self.positions == pos)[0]
        start_idx = self.get_start_idx()
        xs = self.player_x_data_relative[pos_idxs][:, start_idx]
        ys = self.player_y_data_relative[pos_idxs][:, start_idx]
        return xs, ys

    def _compute_relative_data(self):
        """ Compute player data relative to the center. Normalize so offense is moving
        left to right.
        """
        center_idx = np.where(self.positions == 'C')[0][0]
        qb_idx = np.where(self.positions == 'QB')[0][0]
        start_idx = self.get_start_idx()
        direction = self.player_x_data[qb_idx][start_idx] < self.player_x_data[center_idx][start_idx]
        x_0 = self.player_x_data[center_idx][start_idx]
        y_0 = self.player_y_data[center_idx][start_idx]
        if direction:
            self.player_x_data_relative = self.player_x_data - x_0
            self.player_y_data_relative = y_0 - self.player_y_data
        else:
            self.player_x_data_relative = x_0 - self.player_x_data
            self.player_y_data_relative = self.player_y_data - y_0

    def _load_play_data(self, play):
        x_data = None
        y_data = None
        positions = []
        for player_data in self.iter_players_in_play(play):
            x = []
            y = []
            positions.append(self.get_player_position(player_data['nflId']))
            for point in player_data['playerTrackingData']:
                x.append(point['x'])
                y.append(point['y'])
            x = np.array(x)
            y = np.array(y)
            if x_data is None:
                x_data = x
                y_data = y
            else:
                x_data = np.vstack((x_data, x))
                y_data = np.vstack((y_data, y))
        self.positions = np.array(positions)
        self.player_x_data = x_data
        self.player_y_data = y_data
        events = []
        for i, point in enumerate(player_data['playerTrackingData']):
            if 'event' not in point:
                continue
            events.append(point['event'])
        self.events = np.array(events)


def order_players(play):
    """ Return indexes that would put the players in position order with players of the
    same position ordered by leftmost starting postition.
    """
    x_starts, y_starts = play.get_start_positions()
    ordering_info = []
    for i in xrange(NUM_PLAYERS_ON_FIELD * 2):
        ordering_info.append(
            (play.positions[i], y_starts[i], i)
        )
    ordering_info.sort()
    order = map(lambda x: x[2], ordering_info)
    return order


def write_play(group, play, dir):
    with open(os.path.join(dir, 'play_%s.csv' % play.id), 'w') as file_:
        file_.write('play=%d,group=%d\n' % (play.id, group))
        for p in xrange(NUM_PLAYERS_ON_FIELD * 2):
            start_idx = play.get_start_idx()
            position = play.positions[p]
            x = play.player_x_data_relative[p][start_idx]
            y = play.player_y_data_relative[p][start_idx]
            line = '%.2f,%.2f,%s\n' % (x, y, position)
            file_.write(line)


def write_js_formation(dir_, game_num, group_num, play_group):
    filename = 'game_%d_formation_%d.js' % (game_num, group_num)
    filename = os.path.join(dir_, filename)
    first_play = play_group[0]
    num_total = len(play_group)
    num_passes = sum(map(lambda x: 1 if x.play['play']['playType'] == 'play_type_pass' else 0, play_group))
    num_runs = num_total - num_passes
    with open(filename, 'w') as file_:
        file_.write('var formation = {\n')
        file_.write('    starting_positions: [\n')
        player_order = order_players(first_play)
        # Write the starting positions as [x, y, pos, idx]
        x_starts,  y_starts = first_play.get_start_positions()
        for i in xrange(NUM_PLAYERS_ON_FIELD * 2):
            plyr_idx = player_order[i]
            line = '        [%.2f, %.2f, "%s", %d],\n' % (
                x_starts[plyr_idx], y_starts[plyr_idx], first_play.positions[plyr_idx], i
            )
            file_.write(line)
        file_.write('    ],\n')
        file_.write('    routes: [\n')
        routes = [[] for x in range(NUM_PLAYERS_ON_FIELD * 2)]
        for play in play_group:
            order = order_players(play)
            for i in xrange(NUM_PLAYERS_ON_FIELD * 2):
                if play.positions[order[i]] not in POSITIONS_TO_DRAW_ROUTES_FOR:
                    continue
                player_routes = routes[i]
                start_idx = play.get_start_idx()
                x_data = play.player_x_data_relative[order[i]][start_idx:]
                y_data = play.player_y_data_relative[order[i]][start_idx:]
                adj_x_data = x_data + (x_starts[player_order[i]] - x_data[0])
                adj_y_data = y_data + (y_starts[player_order[i]] - y_data[0])
                route = zip(
                    adj_x_data,
                    adj_y_data
                )
                route = map(lambda x: [round(x[0], 2), round(x[1], 2)], route)
                player_routes.append(route)
        # write the routes
        for player_routes in routes:
            if not player_routes:
                file_.write('        [],\n')
                continue
            file_.write('        [\n')
            for route in player_routes:
                file_.write('            ' + str(route) + ',\n')
            file_.write('        ],\n')
        file_.write('    ],\n')
        file_.write('    total: %d,\n' % num_total)
        file_.write('    run: %d,\n' % num_runs)
        file_.write('    pass: %d,\n' % num_passes)
        file_.write('    descriptions: [\n')
        # Write play descriptions
        for play in play_group:
            play_info = play.play['play']
            line = '        ["%d", "%s", "%s", "%d", "%s", "%s"],\n' % (
                play_info['quarter'],
                play_info['gameClock'],
                play_info['yardlineNumber'],
                play_info['down'],
                play_info['yardsToGo'],
                play_info['playDescription']
            )
            file_.write(line)
        file_.write('    ]\n')
        file_.write('}\n')


def mkdir_p(dir_):
    if os.path.isdir(dir_):
        return
    os.mkdir(dir_)


def iter_plays(game_filename):
    player_by_id = get_player_by_id()
    plays = []
    skipped = 0
    for i, play_json in enumerate(iterate_plays_for_game(GAME2)):
        if _is_special_teams_play(play_json):
            continue
        try:
            plays.append(Play(play_json, player_by_id))
        except Exception as e:
            print e
            skipped += 1
            continue
    print('Skipped %d due to error.' % skipped)
    return plays


def main():
    plays = iter_plays(GAME2)
    plays_by_features = defaultdict(list)
    for play in plays:
        plays_by_features[play.get_offense_formation_features()].append(play)
    play_groups = plays_by_features.values()
    play_groups.sort(key=lambda x: -len(x))
    mkdir_p('classified_plays')
    for i, group in enumerate(play_groups[:5]):
        mkdir_p('classified_plays/group_%d' % i)
        for play in group:
            write_play(i, play, 'classified_plays/group_%d' % i)
    return play_groups


def write_plays(play_ids, game_num, group_num, game_filename):
    plays_to_write = []
    for play in iter_plays(game_filename):
        if play.play['play']['playId'] not in play_ids:
            continue
        print 'found one'
        plays_to_write.append(play)
    write_js_formation('.', game_num, group_num, plays_to_write)

