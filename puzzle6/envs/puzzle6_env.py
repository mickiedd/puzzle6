import gym
from gym import error, spaces, utils
from gym.utils import seeding

class Puzzle6Env(gym.Env):
  metadata = {'render.modes': ['human']}

  def __init__(self):
    print("puzzle6 inited")
    self.episode_over = False
    self.observation_space = spaces.Box(low=-1, high=1,
                                            shape=())
    self.action_space = spaces.Tuple((spaces.Discrete(3),
                                          spaces.Box(low=0, high=100, shape=1),
                                          spaces.Box(low=-180, high=180, shape=1),
                                          spaces.Box(low=-180, high=180, shape=1),
                                          spaces.Box(low=0, high=100, shape=1),
                                          spaces.Box(low=-180, high=180, shape=1)))
  def _step(self, action):
    print("step", action)
    ob = 0
    reward = 1
    return ob, reward, self.episode_over, {}
  def _reset(self):
    print("reset")
  def _render(self, mode='human', close=False):
    print("render")
