from dataclasses import dataclass
from maildelivery.world import enviorment, location, package
from maildelivery.geometry import pose2
import matplotlib.pyplot as plt
import numpy as np

CONTROL_THETA_THRESHOLD = np.radians(0.01)
CONTROL_DIST_THRESHOLD = 0.001
REACH_DELTA = 0.001

class agent():
    id : int #to be overwritten
    def act(): #to be overwritten
        pass

@dataclass(frozen = True)
class action:
    agent : agent #to be overwritten

@dataclass(frozen = True)
class wait(action):
    agent : agent
    time_start : float = 0
    time_end : float = 0
    def __repr__(self):
        return f"{self.agent} waits"

@dataclass(frozen = True)
class move(action):
    agent : agent
    loc_from : location
    loc_to : location
    time_start : float = 0
    time_end : float = 0
    def __repr__(self):
        return f"{self.agent} moves from {self.loc_from} to {self.loc_to}"

@dataclass(frozen = True)
class pickup(action):
    agent : agent
    p : package
    loc: location
    time_start : float = 0
    time_end : float = 0
    def __repr__(self):
        return f"{self.agent} picked up {self.p} at {self.loc}"

@dataclass(frozen = True)
class drop(action):
    agent : agent
    p : package
    loc: location
    time_start : float = 0
    time_end : float = 0
    def __repr__(self):
        return f"{self.agent} dropped off {self.p} at {self.loc}"

@dataclass(frozen = True)
class chargeup(action):
    agent : agent
    loc: location
    time_start : float = 0
    time_end : float = 0
    def __repr__(self):
        return f"{self.agent} charging up at {self.loc}"

@dataclass(frozen = True)
class robot_fly(action):
    agent : agent
    time_start : float = 0
    time_end : float = 0
    def __repr__(self):
        return f"{self.agent} is preping to fly"

class robot(agent):
    def __init__(self,id, pose0, dt) -> None:
        self.id = id
        self.pose : pose2 = pose0
        self.dt = dt
        self.velocity = 1.0 #[m/s]
        self.max_rotate : float = np.pi #np.pi/4
        self.last_location : int = 0
        self.goal_location : int = 0
        self.owned_packages : list[package] = []
        self.max_charge : int = 100
        self.charge : int = 100
        self.f_dist2charge  = lambda dist: 2 * dist #some default function
        self.f_charge2time = lambda missing_charge: missing_charge/100
        self.graphics : list = []
        self.current_action : action = wait(self)
        self.return_charge = self.max_charge / 2
       
    def sense(self): #gps like sensor
        return self.pose.t()

    def act(self, a : action, env : enviorment): #perform action on self or enviorment
        if a.agent.id != self.id:
            raise('command given to wrong robot')
        if type(a) is move:
            self.motion_control(a)
            for p in self.owned_packages:
                p.xy = self.pose.t()

            if np.linalg.norm(self.pose.transformTo(a.loc_to.xy)) < REACH_DELTA:
                return True
            else:
                return False
        elif type(a) is pickup:
            if np.linalg.norm(self.pose.transformTo(a.loc.xy)) < REACH_DELTA and \
                np.linalg.norm(self.pose.transformTo(a.p.xy)) < REACH_DELTA: #due to multirobot we can be at location before package arives
                env.packages[a.p.id].owner = self.id #put robot as owner of package
                env.packages[a.p.id].owner_type = 'robot'
                self.owned_packages.append(a.p)
                return True
            else:
                return False
        elif type(a) is drop:
            if np.linalg.norm(self.pose.transformTo(a.loc.xy)) < REACH_DELTA:
                env.packages[a.p.id].owner = a.loc.id #put the landmark as owner of package
                env.packages[a.p.id].owner_type = 'location'
                env.packages[a.p.id].xy = a.loc.xy
                self.owned_packages.remove(a.p)
                return True
            else:
                return False

        elif type(a) is chargeup:
            if np.linalg.norm(self.pose.transformTo(a.loc.xy)) < REACH_DELTA:
                self.charge += self.dt/self.f_charge2time(1.0)
                self.charge = min(self.charge,self.max_charge)
            if self.charge == self.max_charge:
                return True
            else:
                return False

        elif type(a) is robot_fly:
            return False #drone will make the action -> wait after landing, enabling sucess

        elif type(a) is wait:
            return True

    def motion_control(self, action : move):
        e_theta = self.pose.bearing(action.loc_to.xy)
        if abs(e_theta) > CONTROL_THETA_THRESHOLD:
            u = np.sign(e_theta)*min(abs(e_theta),self.max_rotate)
            self.pose = self.pose + pose2(0,0,u)
            return

        e_dist = self.pose.range(action.loc_to.xy)
        if e_dist > CONTROL_DIST_THRESHOLD:
            u = min(e_dist,self.velocity * self.dt)

            if self.charge >= self.f_dist2charge(abs(u)):
                self.pose = self.pose + pose2(u,0,0)
                self.charge = self.charge - self.f_dist2charge(abs(u))
            return

    def plot(self,ax):
        if self.graphics is not None:
            [g.remove() for g in self.graphics]
        self.graphics = plot_robot(ax,self)

    def plot_deadcharge(self,ax):
        self.graphics_deadcharge = plot_robot_deadcharge(ax,self)

    def __repr__(self):
        return f"robot {self.id}"

@dataclass(frozen = True)
class drone_fly(action):
    agent : agent
    loc_from : location
    loc_to : location
    time_start : float = 0
    time_end : float = 0

    def __repr__(self):
        return f"{self.agent} now flies from {self.loc_from} to {self.loc_to}"

@dataclass(frozen = True)
class drone_fly_robot(action):
    agent : agent
    robot : robot
    loc_from : location
    loc_to : location
    time_start : float = 0
    time_end : float = 0

    def __repr__(self):
        return f"{self.agent} now carries {self.robot} from {self.loc_from} to {self.loc_to}"

class drone:
    def __init__(self, id, pose0, dt) -> None:
        self.id : int = id
        self.dt = dt
        self.pose : pose2 = pose0
        self.velocity = 1.0 #[m/s]
        self.max_rotate : float = np.pi #np.pi/4
        self.last_location : int = 0
        self.graphics : list = []
        self.width : float = 0.05
        self.current_action : action = wait(self)

    def sense(self): #gps like sensor
        return self.pose.t()

    def act(self, a : action, env :enviorment): #perform action on self or enviorment
        if a.agent.id != self.id:
            raise('command given to wrong drone')
        if type(a) is drone_fly:
            self.motion_control(a)
            if np.linalg.norm(self.pose.transformTo(a.loc_to.xy)) < REACH_DELTA:
                return True
            else:
                return False

        elif type(a) is drone_fly_robot:
            if type(a.robot.current_action) != robot_fly:
                return False
            self.motion_control(a)
            #bring robot with
            a.robot.pose = self.pose
            if np.linalg.norm(self.pose.transformTo(a.loc_to.xy)) < REACH_DELTA:
                a.robot.current_action = wait(a.robot) #robot now waits to allow for its next task
                return True
            else:
                return False

    def motion_control(self, action : drone_fly):
        e_theta = self.pose.bearing(action.loc_to.xy)
        if abs(e_theta) > CONTROL_THETA_THRESHOLD:
            u = np.sign(e_theta)*min(abs(e_theta),self.max_rotate)
            self.pose = self.pose + pose2(0,0,u)
            return

        e_dist = self.pose.range(action.loc_to.xy)
        if e_dist > CONTROL_DIST_THRESHOLD:
            u = min(e_dist,self.velocity * self.dt)
            self.pose = self.pose + pose2(u,0,0)
            return

    def plot(self,ax):
        if self.graphics is not None:
            [g.remove() for g in self.graphics]
        self.graphics = plot_drone(ax,self)

    def __repr__(self):
        return f"drone {self.id}"

#---------------------------------------------------------------------------
#--------------------------------PLOTTING FUNCTIONS-------------------------
#---------------------------------------------------------------------------

def plot_robot(ax : plt.Axes , r : robot, scale = 20, color = 'b', textcolor = 'magenta'):
        pose = r.pose
        u = np.cos(pose.theta)
        v = np.sin(pose.theta)
        graphics_quiver = ax.quiver(pose.x,pose.y,u,v, color = color, scale = scale, width = 0.02)
        graphics_circle = ax.scatter(pose.x, pose.y, marker = 'o', c = 'none',\
             s = 700, edgecolors = color, alpha = r.charge/r.max_charge)
        graphics_txt = ax.text(pose.x,pose.y,f"{r.id}    ", color = color, horizontalalignment = 'right', verticalalignment = 'center')
        return [graphics_quiver,graphics_circle,graphics_txt]

def plot_robot_deadcharge(ax, r : robot, scale = 20, color = 'r'):
    pose = r.pose
    g1 = ax.scatter(pose.x, pose.y, marker = 'o', c = 'none',\
             s = 800, edgecolors = color)
    g2 = ax.scatter(pose.x, pose.y, marker = 'o', c = 'none',\
             s = 1200, edgecolors = color)
    return [g1,g2]

def plot_drone(ax, d : drone, scale = 20, color = 'r'):
        pose = d.pose
        numsides = 4
        g1 = ax.scatter(pose.x, pose.y, marker = (numsides, 2, np.degrees(pose.theta)), c = 'magenta',\
             s = 200, edgecolors = color)
        g2 = ax.scatter(pose.x, pose.y, marker = 'o', c = 'magenta',\
             s = 200, alpha = 0.2)
        return [g1,g2]





    
        

