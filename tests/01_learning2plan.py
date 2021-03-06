import unified_planning
from unified_planning.shortcuts import UserType, BoolType, IntType, Int,\
        Fluent, DurativeAction, SimulatedEffect, Problem, Object, OneshotPlanner,\
        StartTiming, EndTiming,  GE, Or, Not
unified_planning.shortcuts.get_env().credits_stream = None #removes the printing planners credits 
from unified_planning.io.pddl_writer import PDDLWriter

from maildelivery import optic_wrapper

# --------------------------------------------- Define problem variables and actions
#constants (time can be float, but otherwise stick to ints and bools to avoid segmentation faults)
FULLTANK = 100
DEFAULT_LOCATION_DISTANCE = 1
PICKUP_TIME = 1.0
DROP_TIME = 1.0
CHARGING_TIME = 1.0

def dist2chargeUse(dist):# -> int:
        return 2 * dist

#problem types ~ objectsv
location = UserType('location')
robot = UserType('robot')
package = UserType('package')

#problem variables that are changed by actions on objects (no floats please, they cause problems to solvers)
robot_at = Fluent('robot_at', BoolType(), r = robot, l = location)
is_connected = Fluent('is_connected', BoolType(), l_from = location, l_to = location)
is_free = Fluent('is_free', BoolType(), l = location)
distance = Fluent('distance', IntType(), l_from = location, l_to = location)
delivery_time = Fluent('delivery_time', IntType(), p = package)
robot_has_package = Fluent('robot_has_package', BoolType(), p = package, r = robot)
location_has_package = Fluent('location_has_package', BoolType(), p = package, l = location)
location_is_dock = Fluent('location_is_dock', BoolType(), l = location)
charge = Fluent('charge', IntType(0,100), r = robot)
not_targeted = Fluent('not_targeted', BoolType(), l_to = location)

#actions
move = DurativeAction('move',  r = robot, l_from = location, l_to = location)
r = move.parameter('r')
l_from = move.parameter('l_from')
l_to = move.parameter('l_to')
move.set_fixed_duration(distance(l_from,l_to))
move.add_condition(StartTiming(),Or(is_connected(l_from, l_to), \
                                    is_connected(l_to, l_from)))
move.add_condition(StartTiming(),GE(charge(r),dist2chargeUse(distance(l_from,l_to))))
move.add_condition(StartTiming(), robot_at(r, l_from))
move.add_condition(EndTiming(), is_free(l_to))
move.add_condition(StartTiming(), not_targeted(l_to))
move.add_effect(StartTiming(), robot_at(r, l_from), False)
move.add_effect(StartTiming(), is_free(l_from), True)
move.add_effect(StartTiming(), not_targeted(l_to), False)
move.add_effect(EndTiming(), robot_at(r, l_to), True)
move.add_effect(EndTiming(), is_free(l_to), False)
move.add_effect(EndTiming(), not_targeted(l_to), True)
def decrease_charge_fun(problem, state, actual_params):
        dist = state.get_value(distance(actual_params.get(l_from),actual_params.get(l_to))).constant_value()
        requiredCharge = dist2chargeUse(dist)
        currentCharge = state.get_value(charge(actual_params.get(r))).constant_value()
        return [Int(currentCharge-requiredCharge)]
move.set_simulated_effect(StartTiming(),SimulatedEffect([charge(r)], decrease_charge_fun))

pickup = DurativeAction('pickup', p = package, r = robot, l = location)
p = pickup.parameter('p')
r = pickup.parameter('r')
l = pickup.parameter('l')
pickup.set_fixed_duration(PICKUP_TIME)
pickup.add_condition(StartTiming(),robot_at(r, l))
pickup.add_condition(StartTiming(),location_has_package(p, l))
pickup.add_effect(StartTiming(),location_has_package(p, l), False)
pickup.add_effect(EndTiming(),robot_has_package(p, r), True)

drop = DurativeAction('drop', p = package, r = robot, l = location)
p = drop.parameter('p')
r = drop.parameter('r')
l = drop.parameter('l')
drop.set_fixed_duration(DROP_TIME)
drop.add_condition(StartTiming(),robot_at(r, l))
drop.add_condition(StartTiming(),robot_has_package(p, r))
drop.add_effect(StartTiming(),robot_has_package(p, r), False)
drop.add_effect(EndTiming(),location_has_package(p, l), True)

fillcharge = DurativeAction('fillcharge', r = robot, l = location)
r = fillcharge.parameter('r')
l = fillcharge.parameter('l')
fillcharge.set_fixed_duration(CHARGING_TIME)
fillcharge.add_condition(StartTiming(), location_is_dock(l))
fillcharge.add_condition(StartTiming(), robot_at(r, l))
fillcharge.add_effect(EndTiming(), charge(r), FULLTANK)

problem = Problem('maildelivery')
problem.add_action(move)
problem.add_action(pickup)
problem.add_action(drop)
problem.add_action(fillcharge)
problem.add_fluent(robot_at, default_initial_value = False)
problem.add_fluent(is_connected, default_initial_value = False)
problem.add_fluent(is_free, default_initial_value = True)
problem.add_fluent(distance, default_initial_value = DEFAULT_LOCATION_DISTANCE)
problem.add_fluent(delivery_time, default_initial_value = 0) #unsolvable problem without initating this value
problem.add_fluent(robot_has_package, default_initial_value = False)
problem.add_fluent(location_has_package, default_initial_value = False)
problem.add_fluent(location_is_dock, default_initial_value = False)
problem.add_fluent(charge, default_initial_value = 0) #unsolvable problem without initating this value
problem.add_fluent(not_targeted, default_initial_value = True)

# --------------------------------------------- Set specific values
#objects of problem
locations = [Object(f"l{i}", location) for i in range(4)]
deliverybot = Object("r",robot)
note = Object("p",package)
problem.add_objects(locations + [deliverybot] + [note])
# #initial values of grid locations
problem.set_initial_value(is_connected(locations[0],locations[1]),True)
problem.set_initial_value(is_connected(locations[1],locations[2]),True)
problem.set_initial_value(is_connected(locations[2],locations[3]),True)
problem.set_initial_value(distance(locations[0],locations[1]),1)
problem.set_initial_value(distance(locations[1],locations[2]),2)
problem.set_initial_value(distance(locations[2],locations[3]),3)
problem.set_initial_value(distance(locations[3],locations[2]),4)
#connect pump to grid
problem.set_initial_value(location_is_dock(locations[1]),True)
#robot at start
problem.set_initial_value(robot_at(deliverybot,locations[0]),True)
problem.set_initial_value(is_free(locations[0]),False)
#place packages
problem.set_initial_value(location_has_package(note,locations[3]),True)
#fuel at start
problem.set_initial_value(charge(deliverybot), (dist2chargeUse(1)))
#goal
# problem.add_timed_goal(StartTiming(10.0), location_has_package(note,locations[2]))
problem.add_goal(location_has_package(note,locations[2]))

w = PDDLWriter(problem)
with open(optic_wrapper.DOMAIN_PATH, 'w') as f:
        print(w.get_domain(), file = f)
with open(optic_wrapper.PROBLEM_PATH, 'w') as f:
        print(w.get_problem(), file = f)
print('copied pddls')
        
optic_wrapper.run_optic()
        
execution_times, actions, durations = optic_wrapper.get_plan()

print(actions)
print(execution_times)

# with OneshotPlanner(names=['tamer', 'tamer'],
#                     params=[{'heuristic': 'hadd'}, {'heuristic': 'hmax'}]) as planner:
#     result = planner.solve(problem)
# with OneshotPlanner(problem_kind=problem.kind) as planner:
#     result = planner.solve(problem)
# with OneshotPlanner(name='tamer') as planner:
#     result = planner.solve(problem)

# if result.plan is not None:
#         for action in result.plan.timed_actions:
#                 print(action[1])
# else:
#         print('unable to produce a plan')
