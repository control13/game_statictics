import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Patch
from matplotlib.lines import Line2D
from matplotlib.widgets import Slider
import cv2
import pandas as pd
from scipy.interpolate import CubicSpline
import argparse
import yaml


img = cv2.imread("field.png")
plt.imshow(img, extent=[-5200, 5200, -3700, 3700])
ax = plt.gca()
fig = plt.gcf()

height = img.shape[0]
width = img.shape[1]

ax.set(xlim=(-5200, 5200), ylim=(-3700, 3700), aspect='equal')


def get_ticks(start, stop, number_of_steps, im_size):
  xlabs = ['{x:.1f}'.format(x=x) for x in np.linspace(start, stop, number_of_steps)]
  xticks = np.linspace(-im_size, im_size, len(xlabs))
  return xticks, xlabs
xticks, xlabs = get_ticks(-5.2, 5.2, 11, 5200)
yticks, ylabs = get_ticks(-3.7, 3.7, 9, 3700)


plt.xticks(xticks, xlabs)
plt.yticks(yticks, ylabs)

parser = argparse.ArgumentParser(
                    prog='tcm Viewer',
                    description='Shows robot positions')

parser.add_argument('logfile')
parser.add_argument('-tc1', '--teamcolor1')
parser.add_argument('-tc2', '--teamcolor2')
parser.add_argument('-s', '--swap', action='store_true')
args = parser.parse_args()

df = pd.read_csv(args.logfile)
# offside = https://www.youtube.com/live/VAHpvp0eZ4g?si=ox62htX6w8KTVQbD&t=26154

players = [(df["Team"][i], df["Player"][i]) for i in range(len(df["Team"]))]
players_unique = np.unique(players, axis=0)

player_coordinates = {}
for player in players_unique:
  player_coordinates[str(player)] = df.loc[(df["Team"] == player[0]) & (df["Player"] == player[1])][["Timestamp", "Pose X", "Pose Y", "Pose A", "Ball X", "Ball Y", "Ball Age", "isFallen", "Penalized"]].values

def bin_search_coordiante(player, timestamp, left_index, right_index):
  coordinates = player_coordinates[str(player)]
  middle_idx = int(round((left_index + right_index) / 2))
  if right_index - left_index <= 1:
    return left_index, right_index
  middle = coordinates[middle_idx]
  if timestamp >= middle[0]:
    return bin_search_coordiante(player, timestamp, middle_idx, right_index)
  elif timestamp < middle[0]:
    return bin_search_coordiante(player, timestamp, left_index, middle_idx)


def transform_coordinate(player_coordinates):
  for coordinate in player_coordinates:
    #Rotation
    coordinate[4] = np.cos(coordinate[3])*coordinate[4] + -np.sin(coordinate[3])*coordinate[4]
    coordinate[5] = np.sin(coordinate[3])*coordinate[5] + np.cos(coordinate[3])*coordinate[5]
    #Translation
    coordinate[4] = coordinate[4] + coordinate[1]
    coordinate[5] = coordinate[5] + coordinate[2]
  return player_coordinates


def generate_interpolation(players, player_coordinates):
  player_splines = {}
  for player in players:
    transform_coordinate(player_coordinates[str(player)])
    timestamps = [t[0] for t in player_coordinates[str(player)]]
    diffs = np.diff(timestamps)
    pos_zero = np.where(diffs == 0)
    rob_xs = [t[1] for t in player_coordinates[str(player)]]
    rob_ys = [t[2] for t in player_coordinates[str(player)]]
    rob_as = [t[3] for t in player_coordinates[str(player)]]
    ball_xs = [t[4] for t in player_coordinates[str(player)]]
    ball_ys = [t[5] for t in player_coordinates[str(player)]]

    if len(pos_zero) > 0:
      timestamps = np.delete(timestamps, pos_zero)
      rob_xs = np.delete(rob_xs, pos_zero)
      rob_ys = np.delete(rob_ys, pos_zero)
      rob_as = np.delete(rob_as, pos_zero)
      ball_xs = np.delete(ball_xs, pos_zero)
      ball_ys = np.delete(ball_ys, pos_zero)

    cs = CubicSpline(timestamps, np.c_[rob_xs, rob_ys, rob_as, ball_xs, ball_ys])
    player_splines[str(player)] = cs
  return player_splines


player_splines = generate_interpolation(players_unique, player_coordinates)


def interpolate(player, timestamp, player_splines):
  left, right = bin_search_coordiante(player, timestamp, 0, len(player_coordinates[str(player)]) - 1)
  if left == right:
    return None, None  # TODO
  left_state = player_coordinates[str(player)][left]
  right_state = player_coordinates[str(player)][right]
  # check if player is penalized
  if left_state[3] == 'P' or right_state[3] == 'P':
    return None, None
  if timestamp < left_state[0] or timestamp > right_state[0]:
    return None, None
  if right_state[0] - left_state[0] < 3000:
    ball_age = left_state[6]
    return player_splines[str(player)](timestamp), ball_age
  else:
    return None, None


def rasterize(player, time_max, player_splines):
  time = 0
  coordinates = []
  ball_ages = []
  while time < time_max:
    positions, ball_age = interpolate(player, time, player_splines)
    ball_ages.append(ball_age)
    coordinates.append(positions)
    time += 1000
  return coordinates, ball_ages


rastered_positions = {}
rastered_ball_age = {}
for player in players_unique:
  rastered_positions[str(player)], rastered_ball_age[str(player)] = rasterize(player, np.max(df["Timestamp"]), player_splines)


teams_unique = np.unique([players_unique[x][0] for x in range(len(players_unique))])
spl_teams = yaml.load(open('teams.yaml'), yaml.Loader)

match_teams = []

for team in teams_unique:
  for spl_team in spl_teams:
    if spl_team['number'] == team:
      match_teams.append(spl_team)

if args.teamcolor1:
  match_teams[0]['fieldPlayerColors'][0] = args.teamcolor1

if args.teamcolor2:
  match_teams[1]['fieldPlayerColors'][0] = args.teamcolor2


legend_el = []
for team in match_teams:
  legend_el.append(Patch(facecolor=team['fieldPlayerColors'][0],
                         edgecolor='w',
                         label=team['name']))

ax.legend(handles = legend_el)

circles = []
lines = []

def update_plot(val):
  global circles
  for c in circles:
    c.remove()
  circles = []
  global lines
  for l in lines:
    l.remove()
  lines = []
  current_time = val
  for player in players_unique:
    positions = rastered_positions[str(player)][int(round(current_time))]
    ball_age = rastered_ball_age[str(player)][int(round(current_time))]
    if positions is not None:
      rob_x, rob_y, rob_a, ball_x, ball_y = positions
      if args.swap:
        rob_x, rob_y = -rob_x, -rob_y
        ball_x, ball_y = -ball_x, -ball_y
      if player[0] == teams_unique[0]:
        color = match_teams[0]['fieldPlayerColors'][0]
        rob_x, rob_y = -rob_x, -rob_y
        ball_x, ball_y = -ball_x, -ball_y
      else:
        color = match_teams[1]['fieldPlayerColors'][0]

      if (ball_age < 10) and (ball_age > 0) and 4500 > ball_x > -4500 and 3500 > ball_y > -3500:
        line = Line2D([ball_x, rob_x], [ball_y, rob_y], marker='o', color=color, alpha=1 - ball_age*0.1, linewidth=1, markersize=3)
        lines.append(line)
        ax.add_line(line)

      rob_c = Circle((rob_x, rob_y), 150, linewidth=1, fill=True, edgecolor='w', facecolor=color)
      circles.append(rob_c)
      ax.add_patch(rob_c)



  fig.canvas.draw_idle()


axtime = fig.add_axes([0.25, 0.1, 0.65, 0.03])
time_slider = Slider(
    ax=axtime,
    label='Time [s]',
    valmin=0,
    valmax=int(round(np.max(df["Timestamp"])/1000)),
    valinit=1,
    valstep=1,
)

time_slider.on_changed(update_plot)
update_plot(1)
plt.show()
