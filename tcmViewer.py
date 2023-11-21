import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle
from matplotlib.widgets import Slider
import cv2
import pandas as pd
from scipy.interpolate import CubicSpline


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

df = pd.read_csv("/home/tobias/nao/tcm/GameController/bin/2023-07-06_18-03-41_B-HumanvsHTWK_1st.csv")  # TODO: argparse
# offside = https://www.youtube.com/live/VAHpvp0eZ4g?si=ox62htX6w8KTVQbD&t=26154

players = [(df["Team"][i], df["Player"][i]) for i in range(len(df["Team"]))]
players_unique = np.unique(players, axis=0)

player_coordinates = {}
for player in players_unique:
  player_coordinates[str(player)] = df.loc[(df["Team"] == player[0]) & (df["Player"] == player[1])][["Timestamp", "Pose X", "Pose Y", "Penalized"]].values

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


def generate_interpolation(players, player_coordinates):
  player_splines = {}
  for player in players:
    timestamp = [t[0] for t in player_coordinates[str(player)]]
    diffs = np.diff(timestamp)
    pos_zero = np.where(diffs == 0)
    xs = [t[1] for t in player_coordinates[str(player)]]
    ys = [t[2] for t in player_coordinates[str(player)]]
    if len(pos_zero) > 0:
      timestamp = np.delete(timestamp, pos_zero)
      xs = np.delete(xs, pos_zero)
      ys = np.delete(ys, pos_zero)
    cs = CubicSpline(timestamp, np.c_[xs, ys])
    player_splines[str(player)] = cs
  return player_splines


player_splines = generate_interpolation(players_unique, player_coordinates)


def interpolate(player, timestamp, player_splines):
  left, right = bin_search_coordiante(player, timestamp, 0, len(player_coordinates[str(player)]) - 1)
  if left == right:
    return None  # TODO
  left_state = player_coordinates[str(player)][left]
  right_state = player_coordinates[str(player)][right]
  # check if player is penalized
  if left_state[3] == 'P' or right_state[3] == 'P':
    return None
  if timestamp < left_state[0] or timestamp > right_state[0]:
    return None
  if right_state[0] - left_state[0] < 3000:
    return player_splines[str(player)](timestamp)
  else:
    return None


def rasterize(player, time_max, player_splines):
  time = 0
  coordinates = []
  while time < time_max:
    coordinates.append(interpolate(player, time, player_splines))
    time += 1000
  return coordinates


rastered_players = {}
for player in players_unique:
  rastered_players[str(player)] = rasterize(player, np.max(df["Timestamp"]), player_splines)


circles = []
def update_plot(val):
  global circles
  for c in circles:
    c.remove()
  circles = []
  print(val)
  current_time = val
  for player in players_unique:
    res = rastered_players[str(player)][int(round(current_time))]
    if res is not None:
      x, y = res
      if player[0] == 13:
        color = 'b'
        x, y = -x, -y  # TODO: automate this
      else:
        color = 'r'
      c = Circle((x, y), 150, linewidth=1, fill=True, edgecolor='w', facecolor=color)
      circles.append(c)
      ax.add_patch(c)
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
