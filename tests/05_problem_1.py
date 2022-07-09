from maildelivery.world import enviorment,location, package
from maildelivery.agents import robot, wait
from maildelivery.brains.brains_bots_simple import robot_planner
from maildelivery.brains.plan_parser import parse_actions

import numpy as np
import matplotlib.pyplot as plt
import gtsam

DT = 0.001 #[s]
V = 0.5 #[m/s]

def build_env():
    docks = [location(0,np.array([0,0]),'dock')]

    x1 = location(1,np.array([1,0]),'intersection')
    x2 = location(2,np.array([2,0]),'intersection')
    x3 = location(3,np.array([1,1]),'intersection')
    x4 = location(4,np.array([2,1]),'intersection')
    intersections = [x1,x2,x3,x4]

    h5 = location(5,np.array([1,2]),'house')
    h6 = location(6,np.array([2,2]),'house')
    houses = [h5,h6]

    landmarks = sorted(houses + docks + intersections)

    connectivityList = [[0,1],[1,2],[2,4],[3,4],[1,3],[3,5],[4,6]]

    p0 = package(0,5,'location',6,100,landmarks[5].xy)
    p1 = package(1,6,'location',5,100,landmarks[6].xy)
    packages = [p0,p1]

    env = enviorment(landmarks, connectivityList, packages)
    return env

#buld enviorment
env = build_env()

#spawn robot
x0 = env.locations[0].xy[0]
y0 = env.locations[0].xy[1]
theta0 = location.angle(env.locations[0],env.locations[1])
r = robot(gtsam.Pose2(x0,y0,theta0),0)
r.last_location = 0
r.goal_location = 0
r.max_forward = V * DT

#ask for plan
planner = robot_planner()
planner.create_problem(env,[r])
execution_times, actions, durations = planner.solve(engine_name = 'optic')
parsed_actions = parse_actions(actions, env)

#plot initial state
plt.ion()
_, ax = env.plot()
r.plot(ax)
for p in env.packages:
    p.plot(ax)
plt.draw()

#roll simulation
t = 0
next_action_index = 0
plotCounter = 0
action = wait(robot_id = 0)
while True:
    
    #go do next action
    if type(action) == wait and t >= execution_times[next_action_index]:
        action = parsed_actions[next_action_index]
        next_action_index += 1
        
        
    if r.act(action, env): #do action, and if its finished, start waiting allowing accepting new actions
        action = wait(robot_id = 0)
    
    #update plot        
    if plotCounter % 200 == 0:
        r.plot(ax)
        for p in env.packages:
            p.plot(ax)
        plt.pause(0.01)
    plotCounter += 1
    
    t += DT

    if next_action_index == len(parsed_actions) and type(action) == wait:
        r.plot(ax)
        for p in env.packages:
            p.plot(ax)
        break

#dont close window in the end
ax.set_title('finished!')
print(f"robot has {r.charge}/{r.max_charge} charge left")
plt.ioff()
plt.show()



