import phyre2
import numpy as np

frame_rate = 60
time_step = 1.0 / frame_rate
vel_iters, pos_iters = 8, 3
screen_width, screen_height = 600, 600
ppm = screen_width / 10

if __name__ == "__main__":
    # Load the level
    level = phyre2.Level(ppm)
    level.load("level_0")

    # Create the environment
    env = phyre2.PhyreEnv(level, render_level=True, max_steps=500)

    # Take random actions
    num_trials = 20
    for i in range(num_trials):
        action = env.action_space.sample()
        observation, reward, done, info = env.step(action)
        termination = info["termination"]
        print(f"Trial {i} reward: {reward} termination condition: {termination}")
        env.reset()

    action = np.array([-3, 2.5])
    observation, reward, done, info = env.step(action)
    termination = info["termination"]
    print(f"Trial {num_trials} reward: {reward} termination condition: {termination}")
    env.reset()
