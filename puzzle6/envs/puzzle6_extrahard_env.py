import gym
from gym import error, spaces, utils
from gym.utils import seeding

class Puzzle6ExtraHardEnv(gym.Env):
  metadata = {'render.modes': ['human']}

  def __init__(self):
    print("puzzle6 inited")
  def _step(self, action):
    print("step", action)
  def _reset(self):
    print("reset")
  def _render(self, mode='human', close=False):
    print("render")
