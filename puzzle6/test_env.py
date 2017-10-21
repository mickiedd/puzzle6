import gym
from gym_soccer.envs import soccer_env
from puzzle6.envs import puzzle6_env
env = gym.make('puzzle6-v0')
print(env.action_space)
print(env.observation_space)
env.reset()
t = 0
env.render()
while True:
    t = t + 1
    #print(observation)
    print(env.action_space)
    action = env.action_space.sample()
    observation, reward, done, info = env.step(action)
    print(str(observation))
    if reward > 0.0:
        break;
    if done:
        print("Episode finished after {} timesteps".format(t + 1))
        break