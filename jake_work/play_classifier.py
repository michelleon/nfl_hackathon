    from collections import defaultdict

    import matplotlib.pyplot as plt
    import numpy as np


    DATA_DIR = 'data'
    GAME2 = 'data/full-game-2.json'

    POSITION_CONVERSIONS = {
        'G': 'OG',
        'T': 'OT'
    }

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


    def main():
        player_by_id = get_player_by_id()
        plays = []
        skipped = 0
        for i, play_json in enumerate(iterate_plays_for_game(GAME2)):
            if _is_special_teams_play(play_json):
                continue
            try:
                plays.append(Play(play_json, player_by_id))
            except:
                skipped += 1
                continue
        print('Skipped %d due to error.' % skipped)
        plays_by_features = default_dict(list)
        for play in plays:
            plays_by_features[play.get_offense_formation_features()].append(play)
        play_groups = plays_by_features.values()
        play_groups.sort(key=lambda x: -len(x))
        return play_groups
