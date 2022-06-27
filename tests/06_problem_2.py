from maildelivery.world import enviorment,landmark, package
from maildelivery.agents import robot
from maildelivery.brains import planner0, ROBOT_INDEX_SHIFT

import numpy as np
import matplotlib.pyplot as plt
import gtsam

def build_env():
    docks = [landmark(0,np.array([0,0]),'dock')]

    x1 = landmark(1,np.array([1,0]),'intersection')
    x2 = landmark(2,np.array([2,0]),'intersection')
    x3 = landmark(3,np.array([1,1]),'intersection')
    x4 = landmark(4,np.array([2,1]),'intersection')
    intersections = [x1,x2,x3,x4]

    h5 = landmark(5,np.array([1,2]),'house')
    h6 = landmark(6,np.array([2,2]),'house')
    houses = [h5,h6]

    landmarks = sorted(houses + docks + intersections)

    connectivityList = [[0,1],[1,2],[2,4],[1,3],[3,5],[4,6],[0,3]]

    p0 = package(0,5,6,100,landmarks[5].xy)
    p1 = package(1,6,5,100,landmarks[6].xy)
    packages = [p0,p1]

    env = enviorment(landmarks, connectivityList, packages)
    return env

#buld enviorment
env = build_env()

#spawn robots
x0 = env.landmarks[2].xy[0]
y0 = env.landmarks[2].xy[1]
theta0 = landmark.angle(env.landmarks[2],env.landmarks[6])
r0 = robot(gtsam.Pose2(x0,y0,theta0),0 + ROBOT_INDEX_SHIFT)
r0.last_landmark = 2

x0 = env.landmarks[1].xy[0]
y0 = env.landmarks[1].xy[1]
theta0 = landmark.angle(env.landmarks[1],env.landmarks[3])
r1 = robot(gtsam.Pose2(x0,y0,theta0),1 + ROBOT_INDEX_SHIFT)
r1.last_landmark = 1

r = [r0,r1]

#ask for plan
planner = planner0()
plan = planner.create_plan(env,r)
parsed_actions = planner.parse_actions(plan.actions, env)

#plot initial state
plt.ion()
ax = env.plot()
[ri.plot(ax) for ri in r]
for p in env.packages:
    p.plot(ax)
plt.draw()

#roll simulation
for action in parsed_actions:

    status = False
    while not(status):
        status = r[action.robot_id - ROBOT_INDEX_SHIFT].act(action, env)
        
        #update plot        
        for ri in r:
            ri.plot(ax)
            for p in ri.owned_packages:
                p.plot(ax)
        plt.pause(0.3)

#dont close window in the end
ax.set_title('finished!')
plt.ioff()
plt.show()


