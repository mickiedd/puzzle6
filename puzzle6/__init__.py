from gym.envs.registration import register

register(
    id='puzzle6-v0',
    entry_point='puzzle6.envs.puzzle6_env:Puzzle6Env',
)