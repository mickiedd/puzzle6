import gym
from gym import error, spaces, utils
from gym.utils import seeding
import os
import sys
import random
from ctypes import *
import math
from gym.envs.classic_control import rendering

def run(data):
  # update the data
  t, y = data
  xdata.append(t)
  ydata.append(y)
  xmin, xmax = ax.get_xlim()

  if t >= xmax:
      ax.set_xlim(xmin, 2*xmax)
      ax.figure.canvas.draw()
  line.set_data(xdata, ydata)

  return line,

class Puzzle6Env(gym.Env):
  metadata = {'render.modes': ['human']}
        
  def __init__(self):
   
    print("puzzle6 inited")
    
    chessPropertiesTablePath = b"/home/mickie/course/puzzle6/data/LogicData/ChessPropertiesTable.bin"
    stageConfigPath = b"/home/mickie/course/puzzle6/data/DataConfig/StageData/Normal/stage_0061_0000.bin"
    commonPath = b"/home/mickie/course/puzzle6/data/DataConfig/"
    
    self.dll = cdll.LoadLibrary('/home/mickie/Downloads/libwe6remove.so')

    #create game instance
    self.gameInstanceRet = self.dll.we6_game_new_ctx('', 0)
    
    #start the game
    self.dll.we6_game_quick_run(self.gameInstanceRet, chessPropertiesTablePath, stageConfigPath, commonPath)
    len3 = c_int()
    print("Original:")
    print(c_char_p(self.dll.we6_board_nodes_data(self.gameInstanceRet, byref(len3))).value)
    print(len3)
    print("=========")
    
    self.episode_over = False
    self.observation_space = spaces.Box(low=-1, high=1,
                                            shape=())
    self.action_space = spaces.Tuple((spaces.Discrete(3),
                                          spaces.Box(low=0, high=100, shape=1),
                                          spaces.Box(low=-180, high=180, shape=1),
                                          spaces.Box(low=-180, high=180, shape=1),
                                          spaces.Box(low=0, high=100, shape=1),
                                          spaces.Box(low=-180, high=180, shape=1)))
    
    #graphic
    self.viewer = None
    # Angle at which to fail the episode
    self.theta_threshold_radians = 12 * 2 * math.pi / 360
    self.x_threshold = 2.4
    self.state = None
    
  def _step(self, action):
    print("step", action)
    
    op = 0
    item_type = 4
    from_row = int(random.uniform(0, 10))
    from_col = int(random.uniform(0, 10))
    to_row = int(random.uniform(0, 10))
    to_col = int(random.uniform(0, 10))
    value1 = 0
    value2 = 0
    print("Take action.from:", from_row, from_col, ", to:", to_row, to_col)
    print(c_int(self.dll.we6_game_input_by_detail(self.gameInstanceRet, op, item_type, from_row, from_col, to_row, to_col, value1, value2)).value)
    
    print("Now board nodes:")
    len3 = c_int()
    print(c_char_p(self.dll.we6_board_nodes_data(self.gameInstanceRet, byref(len3))).value)
    print(len3)
    
    print("=========")
    
    ob = 0
    reward = 1
    return ob, reward, self.episode_over, {}
  def _reset(self):
    print("reset")
    
  def get_chess(self):
    cartwidth = 30.0
    cartheight = 30.0
    l,r,t,b = -cartwidth/2, cartwidth/2, cartheight/2, -cartheight/2
    pole = rendering.FilledPolygon([(l,b), (l,t), (r,t), (r,b)])
    pole.set_color(.8,.6,.4)
    axleoffset =cartheight/4.0
    pole.trans = rendering.Transform(translation=(0, axleoffset))
    pole.add_attr(pole.trans)
    self.viewer.add_geom(pole)
    return pole
    
  def _render(self, mode='human', close=False):
    print("render")
    if close:
        if self.viewer is not None:
            self.viewer.close()
            self.viewer = None
            return
    screen_width = 600
    screen_height = 400

    world_width = self.x_threshold*2
    pole = None
    if self.viewer == None:
        self.viewer = rendering.Viewer(screen_width, screen_height)
        pole = self.get_chess()
    pole.trans.set_translation(50, 25)
    return self.viewer.render(return_rgb_array = mode=='rgb_array')