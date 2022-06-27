from dataclasses import dataclass
import matplotlib.pyplot as plt
import numpy as np

@dataclass(frozen = True, order = True) #ordered so they can be sorted!
class landmark:
    id : int
    xy : np.ndarray((2))
    type : str

    def angle(lm1,lm2): #akeen to lm2 - lm1
        dy = lm2.xy[1]-lm1.xy[1]
        dx = lm2.xy[0]-lm1.xy[0]
        return np.arctan2(dy,dx)

    def distance(lm1,lm2):
        dy = lm2.xy[1]-lm1.xy[1]
        dx = lm2.xy[0]-lm1.xy[0]
        return (dx**2 + dy**2)**0.5

@dataclass(frozen = False, order = True) #NOT FROZEN
class package:
    id : int
    owner : int #landmark id  or robot == ROBOT_INDEX_SHIFT + robot id
    goal : int 
    deliverytime : float
    xy : np.ndarray((2))

class enviorment:    
    def __init__(self,landmarks,connectivityList, packages = None):
        #instance attributes
        self.landmarks : list[landmark]  = sorted(landmarks)
        self.connectivityList : list[(int,int)]  = connectivityList
        self.packages : list[package] = packages

    def plot(self,ax : plt.Axes = None):
        if ax == None:
            fig , ax = spawnWorld()
        for lm in self.landmarks:
            if lm.type == "house":
                plot_house(ax,lm)
            elif lm.type == "dock":
                plot_dock(ax,lm)
            else:
                plot_intersection(ax,lm)    
        for c in self.connectivityList:
            lm1 = self.landmarks[c[0]]
            lm2 = self.landmarks[c[1]]
            plot_road(ax,lm1,lm2)
        return ax

    def find_adjacent(self,lm : landmark):
        adjacent = []
        for c in self.connectivityList:
            if lm.id in c:
                i = 1 - c.index(lm.id)
                adjacent.append(c[i])
        return adjacent

#---------------------------------------------------------------------------
#--------------------------------PLOTTING FUNCTIONS-------------------------
#---------------------------------------------------------------------------

def spawnWorld(xrange = None, yrange = None):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_xlabel('x'); ax.set_ylabel('y'); 
    ax.set_aspect('equal'); ax.grid()

    if xrange is not None: ax.set_xlim(xrange)
    if yrange is not None: ax.set_ylim(yrange)

    return fig, ax

def plot_road(ax : plt.Axes,lm1 : landmark, lm2 : landmark):
    x = lm1.xy[0], lm2.xy[0]
    y = lm1.xy[1], lm2.xy[1]
    return ax.plot(x,y,color = 'k')

def plot_intersection(ax: plt.Axes,x : landmark, markerShape = 'x', markerSize = 50, color = 'r'):
    graphics = []
    graphics.append(ax.scatter(x.xy[0],x.xy[1], marker = markerShape, c = color, s = markerSize))
    graphics.append(ax.text(x.xy[0],x.xy[1],x.id, color = color))
    return graphics

def plot_house(ax: plt.Axes, h :landmark, markerShape = 's', markerSize = 80, color = 'k'):
    graphics = []
    g = ax.scatter(h.xy[0],h.xy[1], marker = markerShape, edgecolors = color, s = markerSize)
    g.set_facecolor('none')
    graphics.append(g)
    graphics.append(ax.text(h.xy[0],h.xy[1],h.id, color = color))
    return graphics

def plot_dock(ax: plt.Axes, h :landmark, markerShape = 's', markerSize = 80, color = 'b'):
    graphics = []
    g = ax.scatter(h.xy[0],h.xy[1], marker = markerShape, edgecolors = color, s = markerSize)
    g.set_facecolor('none')
    graphics.append(g)
    graphics.append(ax.text(h.xy[0],h.xy[1],h.id, color = color))
    return graphics

def plot_house(ax: plt.Axes, h :package, markerShape = 'o', markerSize = 20, color = 'r'):
    graphics = []
    g = ax.scatter(h.xy[0],h.xy[1], marker = markerShape, edgecolors = color, s = markerSize)
    graphics.append(g)
    graphics.append(ax.text(h.xy[0],h.xy[1],h.id, color = color))
    return graphics





    

    