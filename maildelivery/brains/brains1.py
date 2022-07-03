from maildelivery.agents import move, pickup, drop, robot
from maildelivery.world import enviorment

import unified_planning as up
from unified_planning.shortcuts import UserType, BoolType,\
        Fluent, InstantaneousAction, Problem, Object, OneshotPlanner, Or, Not, Int
up.shortcuts.get_env().credits_stream = None #removes the printing planners credits 

class brain:
    '''
    multirobot, instant actions, no charging, cost to minimize
    '''
    def __init__(self) -> None:
        _location = UserType('_location')
        _robot = UserType('_robot')
        _package = UserType('package')

        #problem variables that are changed by actions on objects (no floats please, they cause problems to solvers)
        robot_at = Fluent('robot_at', BoolType(), r = _robot, l = _location)
        is_connected = Fluent('is_connected', BoolType(), l_from = _location, l_to = _location)
        is_occupied = Fluent('is_occupied', BoolType(), l = _location)
        robot_has_package = Fluent('robot_has_package', BoolType(), p = _package, r = _robot)
        location_has_package = Fluent('location_has_package', BoolType(), p = _package, l = _location)

        _move = InstantaneousAction('move',  r = _robot, l_from = _location, l_to = _location)
        r = _move.parameter('r')
        l_from = _move.parameter('l_from')
        l_to = _move.parameter('l_to')
        _move.add_precondition(Or(is_connected(l_from, l_to), \
                                            is_connected(l_to, l_from)))
        _move.add_precondition(robot_at(r, l_from))
        _move.add_precondition(Not(is_occupied(l_to))) #at end, l_to is free
        _move.add_effect(robot_at(r, l_from), False)
        _move.add_effect(is_occupied(l_from), False)
        _move.add_effect(robot_at(r, l_to), True)
        _move.add_effect(is_occupied(l_to), True)

        _pickup = InstantaneousAction('pickup', p = _package, r = _robot, l = _location)
        p = _pickup.parameter('p')
        r = _pickup.parameter('r')
        l = _pickup.parameter('l')
        _pickup.add_precondition(robot_at(r, l))
        _pickup.add_precondition(location_has_package(p, l))
        _pickup.add_effect(location_has_package(p, l), False)
        _pickup.add_effect(robot_has_package(p, r), True)

        _drop = InstantaneousAction('drop', p = _package, r = _robot, l = _location)
        p = _drop.parameter('p')
        r = _drop.parameter('r')
        l = _drop.parameter('l')
        _drop.add_precondition(robot_at(r, l))
        _drop.add_precondition(robot_has_package(p, r))
        _drop.add_effect(robot_has_package(p, r), False)
        _drop.add_effect(location_has_package(p, l), True)

        problem = Problem('maildelivery')
        problem.add_action(_move)
        problem.add_action(_pickup)
        problem.add_action(_drop)
        problem.add_fluent(robot_at, default_initial_value = False)
        problem.add_fluent(is_connected, default_initial_value = False)
        problem.add_fluent(is_occupied, default_initial_value = False)
        problem.add_fluent(robot_has_package, default_initial_value = False)
        problem.add_fluent(location_has_package, default_initial_value = False)

        # problem.add_quality_metric(metric =  up.model.metrics.MinimizeActionCosts(
        #                             {_move: Int(1), 
        #                             _pickup: Int(0), 
        #                             _drop: Int(0)
        #                             }
        #                             ))

        problem.add_quality_metric(metric = up.model.metrics.MinimizeSequentialPlanLength())
        # problem.add_quality_metric(metric=MinimizeMakespan())

        #save to self
        self.problem = problem
        #user types
        self._location = _location
        self._robot = _robot
        self._package = _package
        #fluents
        self.robot_at = robot_at
        self.is_connected = is_connected
        self.is_occupied = is_occupied
        self.robot_has_package = robot_has_package
        self.location_has_package =location_has_package

    def create_plan(self, env : enviorment, robots : list[robot]):
        _locations = [Object(f"l{id}", self._location) for id in [loc.id for loc in env.locations]]
        _robots = [Object(f"r{id}", self._robot) for id in [bot.id for bot in robots]]
        _packages = [Object(f"p{id}", self._package) for id in [p.id for p in env.packages]]
        self.problem.add_objects(_locations + _robots + _packages)

        #locations connectivity
        for c in env.connectivityList:
            self.problem.set_initial_value(self.is_connected(
                                        _locations[c[0]],
                                        _locations[c[1]]),
                                        True)
        # robot at start
        for r in robots:
            self.problem.set_initial_value(self.robot_at(
                                                    _robots[r.id],
                                                    _locations[r.last_location]),
                                                    True)
            self.problem.set_initial_value(self.is_occupied(
                                                _locations[r.last_location]),
                                                True) 
        #place packages
        for p in env.packages:
            if p.owner_type == 'location':
                self.problem.set_initial_value(self.location_has_package(
                                                            _packages[p.id],
                                                            _locations[p.owner]),
                                                            True)
            elif p.owner_type == 'robot':
                self.problem.set_initial_value(self.robot_has_package(
                                                _packages[p.id],
                                                _robots[p.owner]),
                                                True)
        #goal
        for p in env.packages:
            self.problem.add_goal(self.location_has_package(_packages[p.id],_locations[p.goal]))

        with OneshotPlanner(problem_kind = self.problem.kind) as planner:
            result = planner.solve(self.problem)
        # with OneshotPlanner(name='tamer') as planner:
        #     result = planner.solve(self.problem)
        
        return result.plan

    def parse_actions(self, actions : list[up.plans.plan.ActionInstance], env : enviorment):
        parsed_actions = []
        for a in actions:
            if a.action.name == 'move':
                parsed_actions.append(move(
                    int(str(a.actual_parameters[0])[1:]), #robot id
                    env.locations[int(str(a.actual_parameters[1])[1:])], #locations_from
                    env.locations[int(str(a.actual_parameters[2])[1:])], #locations_to
                    )) 
            elif a.action.name == 'drop':
                parsed_actions.append(drop(
                    int(str(a.actual_parameters[1])[1:]), #robot id
                    env.packages[int(str(a.actual_parameters[0])[1:])], #package
                    env.locations[int(str(a.actual_parameters[2])[1:])] #location
                    )) 
            elif a.action.name == 'pickup':
                parsed_actions.append(pickup(
                    int(str(a.actual_parameters[1])[1:]), #robot id
                    env.packages[int(str(a.actual_parameters[0])[1:])], #package
                    env.locations[int(str(a.actual_parameters[2])[1:])] #location
                    ))
        return parsed_actions
        