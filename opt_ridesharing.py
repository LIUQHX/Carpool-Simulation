from gurobipy import *
import math
import numpy as np
from param import Parameters
from components import *
from initiate import add_vehicles_from_data, add_requests_from_data
import time


def travel_time_hubs(h1, h2):
    '''
    get distance between two stations.
    :param station1: ID1
    :param station2: ID2
    :return: travel time(s)
    '''
    temp = Parameters.DistanceDict[h1][h2]/(Parameters.Speed*1000)
    return temp

def travel_time_p2h(p_list, h):
    '''
    get the distance between a position and a station
    :param posi_list: [v.ini, v.fin, v.reach], v is on the way to fin from ini. reach is the percentage that the vehicle has completed.
    :param station: station ID.
    :return: travel time(s)
    '''
    if p_list[2] == 0:
        return travel_time_hubs(p_list[0], h)
    else:
        return (1 - p_list[2]) * travel_time_hubs(p_list[0], p_list[1]) + travel_time_hubs(p_list[1], h)

def compute_intermediate_reach(tmp_location, dest, budget):
    '''
    Compute the intermediate station in the path if the vehicle cannot get to the destination directly.
    :param tmp_location:
    :param dest:
    :param budget:
    :return:
    '''
    if tmp_location[2] != 0:
        tmp_tt = travel_time_p2h(tmp_location, tmp_location[1])
        if budget >= tmp_tt:        #can reach fin
            tmp_station = tmp_location[1]
            budget -= tmp_tt
        else:       #cannot reach fin
            return tmp_location[0], tmp_location[1], tmp_location[2] + budget/travel_time_hubs(tmp_location[0], tmp_location[1])
    else:
        tmp_station = tmp_location[0]

    while (True):
        if budget >= travel_time_hubs(tmp_station, Parameters.PredecessorDict[tmp_station][dest][0]):
            return Parameters.PredecessorDict[tmp_station][dest][0], dest, (budget -
            travel_time_hubs(tmp_station, Parameters.PredecessorDict[tmp_station][dest][0]))/travel_time_hubs(Parameters.PredecessorDict[tmp_station][dest][0], dest)
        else:
            dest = Parameters.PredecessorDict[tmp_station][dest][0]



def combine_rr(time_now):
    '''
    try to enumerate each two requests to see if they are able to share a ride.
    :param time_now: current time.
    :return: rr_graph, which is a dict. key: request ID. value: all the requests that can connect to key.
            {1: [2, 3, 4], 2: [3, 4], 3: [4]}
    '''
    rr = {}
    for i in itertools.combinations(Parameters.Requests, 2):       #get all of possible combinations of length 2.
        if i[0].IsUber is True or i[1].IsUber is True:      #if is uber, does not need to check connection with other requests.
            continue
        o1 = i[0].PuHub
        o2 = i[1].PuHub
        d1 = i[0].DoHub
        d2 = i[1].DoHub
        if check_combine(time_now, travel_time_hubs(o1,o2), travel_time_hubs(o1,d1), travel_time_hubs(o1,d2), travel_time_hubs(o2,d1),
                         travel_time_hubs(o2,d2), travel_time_hubs(d1,d2), travel_time_hubs(o2,o1), travel_time_hubs(d1,o1),
                         travel_time_hubs(d2,o1), travel_time_hubs(d1,o2), travel_time_hubs(d2,o2), travel_time_hubs(d2,d1),
                         i[0].LatestPuTime, i[0].LatestDoTime, i[1].LatestPuTime, i[1].LatestDoTime):
            if rr.__contains__(i[0].id):
                rr[i[0].id].append(i[1])
            else:
                rr[i[0].id] = [i[1]]
    return rr

def check_valid(PuTime, DoTime, LatestPuTime, LatestDoTime):
    return (PuTime <= LatestPuTime and DoTime <= LatestDoTime)

def check_combine(time_now, o1o2, o1d1, o1d2, o2d1, o2d2, d1d2, o2o1, d1o1, d2o1, d1o2, d2o2, d2d1, r1putime, r1dotime, r2putime, r2dotime):
    temp_p1 = time_now
    temp_p2 = temp_p1 + o1o2
    temp_d1 = temp_p2 + o2d1
    temp_d2 = temp_d1 + d1d2
    if check_valid(temp_p1, temp_d1, r1putime, r1dotime) and check_valid(temp_p2, temp_d2, r2putime, r2dotime):
        return True

    temp_p1 = time_now
    temp_p2 = temp_p1 + o1o2
    temp_d2 = temp_p2 + o2d2
    temp_d1 = temp_d2 + d2d1
    if check_valid(temp_p1, temp_d1, r1putime, r1dotime) and check_valid(temp_p2, temp_d2, r2putime, r2dotime):
        return True

    # temp_p1 = time_now
    # temp_d1 = temp_p1 + o1d1
    # temp_p2 = temp_d1 + d1o2
    # temp_d2 = temp_p2 + o2d2
    # if check_valid(temp_p1, temp_d1, r1putime, r1dotime) and check_valid(temp_p2, temp_d2, r2putime, r2dotime):
    #     return True

    temp_p2 = time_now
    temp_p1 = temp_p2 + o2o1
    temp_d1 = temp_p1 + o1d1
    temp_d2 = temp_d1 + d1d2
    if check_valid(temp_p1, temp_d1, r1putime, r1dotime) and check_valid(temp_p2, temp_d2, r2putime, r2dotime):
        return True

    temp_p2 = time_now
    temp_p1 = temp_p2 + o2o1
    temp_d2 = temp_p1 + o1d2
    temp_d1 = temp_d2 + d2d1
    if check_valid(temp_p1, temp_d1, r1putime, r1dotime) and check_valid(temp_p2, temp_d2, r2putime, r2dotime):
        return True

    # temp_p2 = time_now
    # temp_d2 = temp_p2 + o2d2
    # temp_p1 = temp_d2 + d2o1
    # temp_d1 = temp_p1 + o1d1
    # if check_valid(temp_p1, temp_d1, r1putime, r1dotime) and check_valid(temp_p2, temp_d2, r2putime, r2dotime):
    #     return True

    return False

def get_fea_sets(Req):
    """
    来了最新的订单，先看一遍之前可行的RV组合；
    如果前面的订单还在请求列中，就取出这些请求列，不用重新算？
    """
    temp_fea_set = {}
    for r in Req:
        try:
            temp_fea_set[r.id] = Parameters.fea_set_last_iteration[r.id]
        except:
            pass
    return temp_fea_set

def check_fea(list, type, time):
    for ind, r in enumerate(list):
        if type[ind] == 2:
            if time > r.LatestPuTime:
                return False
        else:
            if time > r.LatestDoTime:
                return False
    return True

def connect_RV(requests, vehicles, fea_set, current_id):
    """
    requests: 当前的轮次的订单
    vehicles: 与当前轮次订单有关的车
    fea_set: 前一轮可行的RV组合 r.id: {v.id: True}
    currend_id: 当前最新订单的id
    """
    results = []
    for r in requests:
        temp_trip = None
        temp_id = str(r.id) + ''

        if r.id < current_id:
            if r.IsUber is True:
                for v in vehicles:
                    # 如果车在前一轮的订单组合，并且这个车还没接人，那么还是这个组合
                    if v.id in fea_set[r.id] and v.num_passengers == 0:
                        list = [r]
                        type = [2]
                        [opt_sequence, total_cost, total_dis] = compute_travel_RV(list,type,[v.ini, v.fin, v.reach],v.CurrentTime,
                                                                       0, 0, v.num_passengers,v.Capacity)
                        if total_cost is not math.inf:
                            # 如果cost满足要求，这个车就可以和这个单建边
                            r.PossibleVehicles.append([v.id, total_cost, total_dis])
                            # 一单形成trip
                            try:
                                temp_trip.vehicle_list.append((v.id, opt_sequence, total_cost, total_dis))
                            except:
                                temp_trip = trip(temp_id, [r])
                                temp_trip.vehicle_list.append((v.id, opt_sequence, total_cost, total_dis))

            else:
                for v in vehicles:
                    # 如果v在r的可行车里面，并且车容量够
                    if v.id in fea_set[r.id] and v.num_passengers < v.Capacity:
                        list = [r] + v.passengers
                        type = [2] + [1]*len(v.passengers)
                        [opt_sequence, total_cost, total_dis] = compute_travel_RV(list, type, [v.ini, v.fin, v.reach],
                                                                       v.CurrentTime,
                                                                       0, 0, v.num_passengers, v.Capacity)
                        if total_cost is not math.inf:
                            r.PossibleVehicles.append([v.id, total_cost, total_dis])
                            try:
                                temp_trip.vehicle_list.append((v.id, opt_sequence, total_cost, total_dis))
                            except:
                                temp_trip = trip(temp_id, [r])
                                temp_trip.vehicle_list.append((v.id, opt_sequence, total_cost, total_dis))

        else:
            if r.IsUber is True:
                for v in vehicles:
                    if v.IsUber is True and v.num_passengers == 0:
                        list = [r]
                        type = [2]
                        [opt_sequence, total_cost, total_dis] = compute_travel_RV(list,type,[v.ini, v.fin, v.reach],v.CurrentTime,
                                                                       0, 0, v.num_passengers,v.Capacity)
                        if total_cost is not math.inf:
                            r.PossibleVehicles.append([v.id, total_cost, total_dis])
                            try:
                                temp_trip.vehicle_list.append((v.id, opt_sequence, total_cost, total_dis))
                            except:
                                temp_trip = trip(temp_id, [r])
                                temp_trip.vehicle_list.append((v.id, opt_sequence, total_cost, total_dis))

            else:
                for v in vehicles:
                    if v.IsUber is False and v.num_passengers < v.Capacity:
                        list = [r] + v.passengers
                        type = [2] + [1] * len(v.passengers)
                        # TODO:
                        [opt_sequence, total_cost, total_dis] = compute_travel_RV(list, type, [v.ini, v.fin, v.reach],
                                                                       v.CurrentTime,
                                                                       0, 0, v.num_passengers, v.Capacity)
                        if total_cost is not math.inf:
                            r.PossibleVehicles.append([v.id, total_cost, total_dis])
                            try:
                                temp_trip.vehicle_list.append((v.id, opt_sequence, total_cost, total_dis))
                            except:
                                temp_trip = trip(temp_id, [r])
                                temp_trip.vehicle_list.append((v.id, opt_sequence, total_cost, total_dis))

        # 如果能接他的车太多了，取前20
        if len(r.PossibleVehicles) > Parameters.max_link_vehicles:
            r.PossibleVehicles.sort(key=lambda x: x[1])
            r.PossibleVehicles = r.PossibleVehicles[:Parameters.max_link_vehicles]
            temp_trip.vehicle_list.sort(key=lambda x: x[2])
            temp_trip.vehicle_list = temp_trip.vehicle_list[:Parameters.max_link_vehicles]
        elif r.PossibleVehicles == []:
            results.append([False, r.id])
            continue
        # 和这个订单有关的trip记录
        r.trips.append(temp_id)
        # v.id: True ? why use?
        tmp_trip_vehicle_list = {i[0]: True for i in temp_trip.vehicle_list}
        # [当前订单，[当前trip id，当前trip，可以接这个trip的车]，订单id]
        results.append([r, [temp_id, temp_trip, tmp_trip_vehicle_list], r.id])
    return results


def compute_travel_RV(list, type, current_position, current_time, cost, dis, num_passengers, capacity):
    """
    list: 载人车当前的订单和新订单的组合，看能否拼
    type:
    current_position: three point to represent
    current_time:
    cost: 0
    dis: 0
    num_passengers, capacity: v.num, v.capacity
    """
    opt_cost = math.inf
    opt_dis = math.inf
    opt_sequence = []
    length = len(list)
    num_passenger_temp = num_passengers

    if length == 0:
        return [], cost, dis

    if length == 1:
        if type[0] == 2:       # 这单被空车接，need pick up and drop off
            c_time2 = current_time + travel_time_p2h(current_position, list[0].PuHub)
            temp_dis2 = travel_time_p2h(current_position, list[0].PuHub)*Parameters.Speed*1000
            if c_time2 <= list[0].LatestPuTime and (num_passenger_temp + 1) <= capacity:        #can pick up
                c_time3 = c_time2 + list[0].DijTravelTime
                temp_dis3 = temp_dis2 + list[0].DijTravelTime*Parameters.Speed*1000
                if c_time3 <= list[0].LatestDoTime:      #can drop off
                    return [[list[0], 'p'], [list[0], 'd']], cost + c_time3 - list[0].EarliestDoTime, dis + temp_dis3

        else:       #need only drop off
            c_time2 = current_time + travel_time_p2h(current_position, list[0].DoHub)
            temp_dis2 = travel_time_p2h(current_position, list[0].DoHub)*Parameters.Speed*1000
            if c_time2 <= list[0].LatestDoTime:      #can drop off
                return [[list[0], 'd']], cost + c_time2 - list[0].EarliestDoTime, dis + temp_dis2
        return [], math.inf, math.inf

    for i in range(length):
        list_remain = list.copy()
        type_remain = type.copy()

        type_remain[i] -= 1
        if type_remain[i] == 0:
            del list_remain[i]
            del type_remain[i]

        if type[i] == 2:
            c_time2 = current_time + travel_time_p2h(current_position, list[i].PuHub)
            temp_dis2 = travel_time_p2h(current_position, list[i].PuHub)*Parameters.Speed*1000
            if c_time2 <= list[i].LatestPuTime and (num_passenger_temp + 1) <= capacity:
                if check_fea(list_remain,type_remain,c_time2):
                    temp_sequence, temp_cost, temp_dis = compute_travel_RV(list_remain, type_remain, [list[i].PuHub, list[i].PuHub, 1],
                                                                 c_time2, cost, dis+temp_dis2, num_passenger_temp + 1, capacity)
                    if temp_cost < opt_cost:
                        temp_sequence = [[list[i], 'p']] + temp_sequence
                        opt_cost = temp_cost
                        opt_sequence = temp_sequence
                        opt_dis = temp_dis
        else:
            c_time2 = current_time + travel_time_p2h(current_position, list[i].DoHub)
            temp_dis2 = travel_time_p2h(current_position, list[i].DoHub)*Parameters.Speed*1000
            if c_time2 <= list[i].LatestDoTime :
                if check_fea(list_remain, type_remain, c_time2):
                    temp_sequence, temp_cost, temp_dis = compute_travel_RV(list_remain, type_remain,
                                                                 [list[i].DoHub, list[i].DoHub, 1],
                                                                 c_time2, cost + c_time2 - list[i].EarliestDoTime, dis+temp_dis2, num_passenger_temp - 1, capacity)
                    if temp_cost < opt_cost:
                        temp_sequence = [[list[i], 'd']] + temp_sequence
                        opt_cost = temp_cost
                        opt_sequence = temp_sequence
                        opt_dis = temp_dis
    return opt_sequence, opt_cost, opt_dis

def get_related_vehicles(requests, feasible_sets):
    '''
    check feasibility according to the distance.
    :param cluster: a list of requests that will be fit into a processor.
    :requests: 本轮全部订单
    :param feasible_sets: feasible vehicle set for the cluster
    :return: 和这些request有关的所有车，也就是能接其中任何request就满足条件
    '''
    temp_vehicles = []
    for v in Parameters.Vehicles:
        for r in requests:
            # TODO: 之前轮次的订单，而且这个车不能接，直接跳过不用判断了
            if r.id < Parameters.current_request_id and v.id not in feasible_sets[r.id]:
                continue
            # 如果司机能在接驾时延内接单就可以，这一步主要是为了把沾边的车都选出来
            # TODO: 为什么不直接确定哪个订单可以被哪个车接？
            if v.CurrentTime + travel_time_p2h([v.ini, v.fin, v.reach], r.PuHub) <= r.LatestPuTime and r.IsUber == v.IsUber:
                temp_vehicles.append(v)
                break
    return temp_vehicles


def compute_RV(time_now):
    fea_sets = get_fea_sets(Parameters.Requests)
    results = connect_RV(Parameters.Requests, get_related_vehicles(Parameters.Requests, fea_sets), fea_sets, Parameters.current_request_id)
    results.sort(key=lambda x: x[-1])

    for i in results:
        if i[0] is False:
            Parameters.RequestIndex[i[1]].ignored = True
            continue

        #Parameters.RequestIndex[i[0].id].update_rv(i[0].trips)
        #i[1][1].update_address()
        # vehicles: trip
        Parameters.Trips[i[1][0]] = i[1][1]
        for v in i[0].PossibleVehicles:
            Parameters.Vehicles[v[0]].possible_requests.append([Parameters.RequestIndex[i[0].id]])
        # {5: True, 254: True, 427: True,... 这到底是什么东西
        # r.id: {v.id: True} ??? why use
        Parameters.fea_set[i[0].id] = i[1][2]


def connect_RTV(vehicles, rr):
    results = []
    for v in vehicles:
        VT_list = []
        temp_T = {}
        temp_T[1] = v.possible_requests
        # 对这个v所有可接的请求
        for i in temp_T[1]:
            rr_ind = 0
            trip_ind = 0
            try:
                while (trip_ind < len(temp_T[1])) and (rr_ind < len(rr[i[0].id])):
                    # trip的订单id = rr的订单id
                    if temp_T[1][trip_ind][0].id == rr[i[0].id][rr_ind].id:
                        temp_trip = i + temp_T[1][trip_ind]
                        temp_T, VT_list = combine_rv(v, temp_trip, temp_T, VT_list)
                        trip_ind += 1
                        rr_ind += 1
                    elif temp_T[1][trip_ind][0].id < rr[i[0].id][rr_ind].id:
                        trip_ind += 1
                    else:
                        rr_ind += 1
            except:
                pass

        if len(VT_list) != 0:
            results.append(VT_list)
    return results

def combine_rv(v, T, temp_T, VT_list):
    length = len(T)
    list = T + v.passengers
    type = [2]*length + [1]*len(v.passengers)
    [opt_sequence, total_cost, total_dis] = compute_travel_RTV(list, type, [v.ini, v.fin, v.reach], v.CurrentTime, 0, 0, v.num_passengers, v.Capacity)

    if total_cost is math.inf:
        pass
    else:
        try:
            temp_T[length].append(T)
        except:
            temp_T[length] = [T]

        temp_id = ''
        req_list = []
        for req in T:
            temp_id += str(req.id) + ' '
            req_list.append(req)

        VT_list.append([temp_id, req_list, (v.id, opt_sequence, total_cost, total_dis)])

    return temp_T, VT_list

def compute_travel_RTV(list, type, current_position, current_time, cost, dis, num_passengers, capacity):
    opt_cost = math.inf
    opt_dis = math.inf
    opt_sequence = []
    length = len(list)
    num_passenger_temp = num_passengers

    if length == 0:
        return [], cost, dis

    if length == 1:
        if type[0] == 2:  # need pick up and drop off
            c_time2 = current_time + travel_time_p2h(current_position, list[0].PuHub)
            temp_dis2 = travel_time_p2h(current_position, list[0].PuHub)*Parameters.Speed*1000
            if c_time2 <= list[0].LatestPuTime and (num_passenger_temp + 1) <= capacity:  # can pick up
                c_time3 = c_time2 + list[0].DijTravelTime
                temp_dis3 = temp_dis2 + list[0].DijTravelTime * Parameters.Speed * 1000
                if c_time3 <= list[0].LatestDoTime:  # can drop off
                    return [[list[0], 'p'], [list[0], 'd']], cost + c_time3 - list[0].EarliestDoTime, dis + temp_dis3

        else:  # need only drop off
            c_time2 = current_time + travel_time_p2h(current_position, list[0].DoHub)
            temp_dis2 = travel_time_p2h(current_position, list[0].DoHub)*Parameters.Speed*1000
            if c_time2 <= list[0].LatestDoTime:  # can drop off
                return [[list[0], 'd']], cost + c_time2 - list[0].EarliestDoTime, dis + temp_dis2
        return [], math.inf, math.inf

    for i in range(length):
        list_remain = list.copy()
        type_remain = type.copy()

        type_remain[i] -= 1
        if type_remain[i] == 0:
            del list_remain[i]
            del type_remain[i]

        if type[i] == 2:
            c_time2 = current_time + travel_time_p2h(current_position, list[i].PuHub)
            temp_dis2 = travel_time_p2h(current_position, list[i].PuHub)*Parameters.Speed*1000
            if c_time2 <= list[i].LatestPuTime and (num_passenger_temp + 1) <= capacity:
                if check_fea(list_remain, type_remain, c_time2):
                    temp_sequence, temp_cost, temp_dis = compute_travel_RTV(list_remain, type_remain,[list[i].PuHub, list[i].PuHub, 1], c_time2, cost, dis + temp_dis2, num_passenger_temp + 1, capacity)
                    if temp_cost < opt_cost:
                        temp_sequence = [[list[i], 'p']] + temp_sequence
                        opt_cost = temp_cost
                        opt_sequence = temp_sequence
                        opt_dis = temp_dis
        else:
            c_time2 = current_time + travel_time_p2h(current_position, list[i].DoHub)
            temp_dis2 = travel_time_p2h(current_position, list[i].DoHub)*Parameters.Speed*1000
            if c_time2 <= list[i].LatestDoTime:
                if check_fea(list_remain, type_remain, c_time2):
                    temp_sequence, temp_cost, temp_dis = compute_travel_RTV(list_remain, type_remain,[list[i].DoHub, list[i].DoHub, 1], c_time2, cost + c_time2 - list[i].EarliestDoTime, dis + temp_dis2, num_passenger_temp - 1, capacity)
                    if temp_cost < opt_cost:
                        temp_sequence = [[list[i], 'd']] + temp_sequence
                        opt_cost = temp_cost
                        opt_sequence = temp_sequence
                        opt_dis = temp_dis
    return opt_sequence, opt_cost, opt_dis

def compute_RTV(rr):
    # 莫非是判断两拼和车
    results = connect_RTV(Parameters.Vehicles, rr)

    for i in results:
        for j in i:
            try:
                Parameters.Trips[j[0]].vehicle_list.append(j[2])
            except:
                T = trip(j[0], j[1])
                T.vehicle_list.append(j[2])
                Parameters.Trips[j[0]] = T
                for k in j[1]:
                    Parameters.RequestIndex[k.id].trips.append(j[0])

    for v in Parameters.Vehicles:
        v.assigned_task = False


def trip_price(req):
    base = Parameters.uber_base_fare
    dis =  Parameters.uber_per_km_rates*(Parameters.DistanceDict[req.PuHub][req.DoHub]/1000)
    time = Parameters.uber_per_second_rates*travel_time_hubs(req.PuHub,req.DoHub)
    price = base + dis + time
    if price <= Parameters.uber_minimum_fare:
        return Parameters.uber_minimum_fare
    else:
        return price

def pu_cost(p_list,h):
    distance = (1 - p_list[2]) * Parameters.DistanceDict[p_list[0]][p_list[1]] + Parameters.DistanceDict[p_list[1]][h]/1000
    cost = 0.75 * Parameters.uber_per_km_rates * distance
    return cost

def sum_v(var, i, vr):
    temp = 0
    for j in vr[i].keys():
        temp += var[(j[0],j[1])]
    return temp

def sum_r(var,r):
    temp = 0
    for t in r.trips:
        for v in Parameters.Trips[t].vehicle_list:
            temp += var[(v[0],t)]
    return temp

def sum_obj(var,vr,var_list):
    obj = 0
    for i in var_list:
        cost = vr[i[0]][(i[0],i[1])][1]*Parameters.uber_per_km_rates*0.75/1000
        income = 0
        t_index = str(i[1]) + ''
        for r in Parameters.Trips[t_index].request_list:
            income += trip_price(r)
        revenue = (income - cost)*var[i]
        obj += revenue
    return obj

def sum_obj2(var,vr,var_list, time_now):
    obj = 0
    for i in var_list:
        veh = Parameters.Vehicles[i[0]]
        if veh.num_passengers == 0:
            cost = vr[i[0]][(i[0], i[1])][1] * Parameters.uber_per_km_rates * 0.75 / 1000
            income = 0
            t_index = str(i[1]) + ''
            for r in Parameters.Trips[t_index].request_list:
                income += trip_price(r)
            revenue = (income - cost) * var[i]
            obj += revenue
        else:
            if veh.num_passengers > 1 :
                print(veh.num_passengers, vr[veh.id][(veh.id,i[1])][2],vr[veh.id][(veh.id,i[1])][0])
            pre_cost = 0
            pre_income = 0
            for req in veh.passengers:
                pre_cost = (time_now - req.AssignTime)* Parameters.Speed * Parameters.uber_per_km_rates * 0.75
                pre_income += 0.8*trip_price(req)
            cost = vr[i[0]][(i[0], i[1])][1] * Parameters.uber_per_km_rates * 0.75 / 1000 + pre_cost
            income = pre_income
            t_index = str(i[1]) + ''
            for r in Parameters.Trips[t_index].request_list:
                income += trip_price(r)
            revenue = (income - cost) * var[i]
            obj += revenue
    return obj

def sum_obj3(var,vr,var_list):
    obj = 0
    for i in var_list:
        veh = Parameters.Vehicles[i[0]]
        if veh.num_passengers == 0:
            cost = vr[i[0]][(i[0], i[1])][1] * Parameters.uber_per_km_rates * 0.75 / 1000
            income = 0
            t_index = str(i[1]) + ''
            for r in Parameters.Trips[t_index].request_list:
                income += trip_price(r)
            revenue = (income - cost) * var[i]
            obj += revenue
        else:
            travel_list = (vr[veh.id][(veh.id,i[1])][2])
            distance = vr[i[0]][(i[0],i[1])][1]
            cost = est_cost2(travel_list,distance,veh)
            income = 0
            t_index = str(i[1]) + ''
            for r in Parameters.Trips[t_index].request_list:
                income += trip_price(r)
            revenue = (income - cost) * var[i]
            obj += revenue
    return obj

def est_cost(travel_list,distance,v):
    if len(v.passengers) != 1:
        print('bug')
    req = v.passengers[0]

    if travel_list[0][1] == 'd':
        est_dis = distance - travel_time_p2h((v.ini,v.fin,v.reach),travel_list[0][0].DoHub)*Parameters.Speed*1000
        cost = est_dis * Parameters.uber_per_km_rates * 0.75 / 1000
        return cost
    else:
        if len(travel_list)==3:
            if travel_list[1][0] == req:
                est_dis = (2*travel_time_p2h((v.ini,v.fin,v.reach), travel_list[0][0].PuHub) + travel_time_hubs(travel_list[1][0].DoHub,travel_list[2][0].DoHub))*Parameters.Speed*1000
                cost = est_dis * Parameters.uber_per_km_rates * 0.75 / 1000
                return cost
            if travel_list[1][0] != req:
                est_dis = 2 * travel_time_p2h((v.ini,v.fin,v.reach), travel_list[0][0].PuHub)*Parameters.Speed*1000
                cost = est_dis * Parameters.uber_per_km_rates * 0.75 / 1000
                return cost
        else:
            cost = distance * Parameters.uber_per_km_rates * 0.75 / 1000
            return cost

def est_cost2(travel_list,distance,v):
    if len(v.passengers) != 1:
        print('bug')
    req = v.passengers[0]

    if travel_list[0][1] == 'd':
        est_dis = distance - travel_time_p2h((v.ini, v.fin, v.reach), travel_list[0][0].DoHub) * Parameters.Speed * 1000
        cost = est_dis * Parameters.uber_per_km_rates * 0.75 / 1000
        return cost
    else:
        est_dis = distance - travel_time_p2h((v.ini, v.fin, v.reach), req.DoHub) * Parameters.Speed * 1000
        cost = est_dis * Parameters.uber_per_km_rates * 0.75 / 1000
        return cost


def sum_obj_ml(var,vr,var_list):
    obj = 0
    for i in var_list:
        veh = Parameters.Vehicles[i[0]]
        if veh.num_passengers == 0:
            cost = vr[i[0]][(i[0], i[1])][1] * Parameters.uber_per_km_rates * 0.75 / 1000
            income = 0
            t_index = str(i[1]) + ''
            for r in Parameters.Trips[t_index].request_list:
                income += trip_price(r)
            revenue = (income - cost) * var[i]
            obj += revenue
        else:
            travel_list = (vr[veh.id][(veh.id,i[1])][2])
            distance = vr[i[0]][(i[0],i[1])][1]
            cost = est_cost2(travel_list,distance,veh)
            income = 0
            t_index = str(i[1]) + ''
            for r in Parameters.Trips[t_index].request_list:
                income += trip_price(r)
            revenue = (income - cost) * var[i]
            obj += revenue
    return obj




def opt_assignment(time_now):
    undo_requests = {r.id: r for r in Parameters.Requests}
    vehicles = {v.id: v for v in Parameters.Vehicles}
    Trips = Parameters.Trips
    vr = {v.id:{} for v in Parameters.Vehicles}

    var_list = []

    for t in Trips:
        for v_list in Trips[t].vehicle_list:
            vr[v_list[0]][(v_list[0],t)] = [v_list[2],v_list[3],v_list[1]]
            var_list.append((v_list[0],t))

    model = Model('assignment_rs')
    model.setParam('OutputFlag', 0)
    var = model.addVars(var_list, vtype=GRB.BINARY, name='var')

    model.addConstrs((sum_v(var, i, vr) <= 1 for i in vehicles if vr[i] != {}), "vehicle")
    model.addConstrs((sum_r(var, r) <= 1 for r in Parameters.Requests if r.trips != []), "requests")
    obj = sum_obj_ml(var, vr, var_list)
    model.setObjective(obj, GRB.MAXIMIZE)
    model.params.timeLimit = 15
    model.params.MIPGap = 0.0001
    model.optimize()

    for v in model.getVars():
        if v.X != 0:
            match = v.Varname[4:-1].split(',')
            veh_match = vehicles[int(match[0])]

            veh_match.assigned_task = True
            veh_match.IsRebalancing = False
            veh_match.RebalanceDest = None
            veh_match.assigned_trips = vr[int(match[0])][(int(match[0]),match[1])][2]

            for r in Trips[match[1]].request_list:
                Parameters.RequestIndex[r.id].assigned = True
                r.AssignTime = time_now
                r.price = trip_price(r)
                # del undo_requests[r.id]
                try:
                    del undo_requests[r.id]
                except:
                    Parameters.wrong += 1
                    print("del undo_request[r.id] error")
                #Parameters.Requests.remove(r)
                #Parameters.RequestDone.append(r)
                Parameters.Assign += 1

    # 计算分单完毕，这一轮trip清空
    Parameters.Trips = {}

    idle_vehicles = update_vehicles(time_now)

    # rebalance(vehicles, undo_requests, idle_vehicles)

    update_requests(time_now)



def compute_travel(list, type, current_position, time_now, cost):

    opt_cost = math.inf
    opt_sequence = []
    length = len(list)

    if length == 0:
        return [], cost

    if length == 1:
        time_now2 = time_now + travel_time_p2h(current_position, list[0].DoHub)
        if time_now2 <= list[0].LatestDoTime + 1:
            return [[list[0], 'd']], cost + time_now2 - list[0].EarliestDoTime
        return [], math.inf

    for i in range(length):
        list_remain = list.copy()
        type_remain = type.copy()
        del list_remain[i]
        del type_remain[i]

        time_now2 = time_now + travel_time_p2h(current_position, list[i].DoHub)
        if time_now2 <= list[i].LatestDoTime + 1:
            tmp_sequence, tmp_cost = compute_travel(list_remain, type_remain, [list[i].DoHub, list[i].DoHub, 1], time_now2, cost + time_now2 - list[i].EarliestDoTime)
            if tmp_cost < opt_cost:
                tmp_sequence = [[list[i], 'd']] + tmp_sequence
                opt_sequence = tmp_sequence
                opt_cost = tmp_cost
    return opt_sequence, opt_cost



def update_vehicles(time_now):
    idle_vehicles = []
    for v in Parameters.Vehicles:

        v.possible_requests = []
        v.TimeRemain = Parameters.TimeWindow

        if v.assigned_task is False:

            if v.num_passengers > 0:
                list = v.passengers
                type = [1]*len(v.passengers)
                v.assigned_trips = compute_travel(list, type, [v.ini, v.fin, v.reach], time_now, 0)[0]
                v.assigned_task = True

            else:
                #rb
                v.assigned_trips = []
                if v.IsRebalancing is True:
                    tmp_tt = travel_time_p2h((v.ini, v.fin, v.reach), v.RebalanceDest)
                    if tmp_tt <= v.TimeRemain:  # finish rebalancing
                        v.TimeRemain -= travel_time_p2h((v.ini, v.fin, v.reach), v.RebalanceDest)
                        if v.reach == 0:
                            v.TravelDistance += Parameters.DistanceDict[v.ini][v.RebalanceDest]

                        else:
                            v.TravelDistance += (
                                Parameters.DistanceDict[v.ini][v.fin] + Parameters.DistanceDict[v.fin][v.RebalanceDest])
                        v.ini = v.RebalanceDest
                        v.fin = v.RebalanceDest
                        v.reach = 1
                        v.RbTotalTime += tmp_tt
                        v.IsRebalancing = False
                        v.RebalanceDest = None

                    else:
                        tmp_ini, tmp_fin, tmp_reach = compute_intermediate_reach((v.ini, v.fin, v.reach),
                                                                                 v.RebalanceDest,
                                                                                 v.TimeRemain)
                        v.RbTotalTime += v.TimeRemain
                        v.TimeRemain = 0
                        if v.ini != tmp_ini:
                            if v.reach == 0:
                                v.TravelDistance += Parameters.DistanceDict[v.ini][tmp_ini]
                            else:
                                v.TravelDistance += (
                                    Parameters.DistanceDict[v.ini][v.fin] + Parameters.DistanceDict[v.fin][tmp_ini])
                        v.ini, v.fin, v.reach = tmp_ini, tmp_fin, tmp_reach

                else:
                    if v.reach < 1 and v.reach > 0:
                        tmp_tt = travel_time_p2h([v.ini, v.fin, v.reach], v.fin)
                        if tmp_tt >= v.TimeRemain:  # cannot reach fin
                            v.reach += v.TimeRemain / travel_time_hubs(v.ini, v.fin)
                            v.IdleTotalTime += v.TimeRemain
                            v.TravelTime += v.TimeRemain
                            v.num_passenger_time[0] += v.TimeRemain
                            v.TimeRemain = 0
                        else:
                            v.IdleTotalTime += tmp_tt
                            v.TimeRemain -= tmp_tt
                            v.num_passenger_time[0] += tmp_tt

                            v.TravelTime += tmp_tt
                            v.TravelDistance += Parameters.DistanceDict[v.ini][v.fin]
                            v.ini = v.fin
                            v.reach = 1

        for i in v.assigned_trips:
            Req = i[0]
            if i[1] == 'p':
                tmp_tt = travel_time_p2h([v.ini, v.fin, v.reach], Req.PuHub)

                if tmp_tt <= v.TimeRemain:
                    # continue travel
                    if v.reach == 0:
                        v.TravelDistance += Parameters.DistanceDict[v.ini][Req.PuHub]
                        for r in v.passengers:
                            r.share_distance[v.num_passengers] += Parameters.DistanceDict[v.ini][Req.PuHub]

                    else:
                        v.TravelDistance += (
                            Parameters.DistanceDict[v.ini][v.fin] + Parameters.DistanceDict[v.fin][Req.PuHub])
                        for r in v.passengers:
                            r.share_distance[v.num_passengers] += (
                                Parameters.DistanceDict[v.ini][v.fin] + Parameters.DistanceDict[v.fin][Req.PuHub])

                    v.reach = 1
                    v.ini = Req.PuHub
                    v.fin = Req.PuHub
                    v.TimeRemain -= tmp_tt
                    v.num_passengers += 1
                    v.passengers.append(Req)

                    v.num_passenger_time[v.num_passengers] += tmp_tt

                    if v.num_passengers == 2:
                        dropoff = False
                        for temp_req in v.passengers:
                            if temp_req.DoHub == v.fin:
                                dropoff = True
                        if dropoff is False:
                            for tep_req in v.passengers:
                                tep_req.shared = True
                    Req.PuTime = time_now + Parameters.TimeWindow - v.TimeRemain

                    Parameters.PU += 1
                    v.PuTotalTime += tmp_tt
                    v.TravelTime += tmp_tt
                    try:
                        Parameters.Requests.remove(Req)
                    except:
                        Parameters.wrong += 1
                        print("Parameters.Requests.remove(Req) error")
                    Parameters.RequestDone.append(Req)

                else:
                    if v.TimeRemain >= 0:
                        # cannot finish the trip to i in this time window.
                        tmp_ini, tmp_fin, tmp_reach = compute_intermediate_reach((v.ini, v.fin, v.reach), Req.PuHub,
                                                                                 v.TimeRemain)
                        v.TravelTime += v.TimeRemain
                        if v.ini != tmp_ini:
                            if v.reach == 0:
                                v.TravelDistance += Parameters.DistanceDict[v.ini][tmp_ini]
                                for r in v.passengers:
                                    r.share_distance[v.num_passengers] += Parameters.DistanceDict[v.ini][tmp_ini]

                            else:
                                v.TravelDistance += (
                                    Parameters.DistanceDict[v.ini][v.fin] + Parameters.DistanceDict[v.fin][tmp_ini])
                                for r in v.passengers:
                                    r.share_distance[v.num_passengers] += (
                                        Parameters.DistanceDict[v.ini][v.fin] + Parameters.DistanceDict[v.fin][tmp_ini])

                        v.ini, v.fin, v.reach = tmp_ini, tmp_fin, tmp_reach

                        v.PuTotalTime += v.TimeRemain
                        v.num_passenger_time[v.num_passengers] += v.TimeRemain
                        v.TimeRemain -= tmp_tt

            else:
                tmp_tt = travel_time_p2h([v.ini, v.fin, v.reach], Req.DoHub)
                if tmp_tt <= v.TimeRemain:
                    # continue travel
                    if v.reach == 0:
                        v.TravelDistance += Parameters.DistanceDict[v.ini][Req.DoHub]
                        for r in v.passengers:
                            r.share_distance[v.num_passengers] += Parameters.DistanceDict[v.ini][Req.DoHub]

                    else:
                        v.TravelDistance += (
                            Parameters.DistanceDict[v.ini][v.fin] + Parameters.DistanceDict[v.fin][Req.DoHub])
                        for r in v.passengers:
                            r.share_distance[v.num_passengers] += (
                                Parameters.DistanceDict[v.ini][v.fin] + Parameters.DistanceDict[v.fin][Req.DoHub])

                    v.reach = 1
                    v.ini = Req.DoHub
                    v.fin = Req.DoHub
                    v.TimeRemain -= tmp_tt
                    Req.DoTime = time_now + Parameters.TimeWindow - v.TimeRemain
                    Parameters.TotalDistance += Parameters.DistanceDict[Req.PuHub][Req.DoHub]
                    v.passengers.remove(Req)
                    try:
                        del Parameters.RequestIndex[Req.id]
                    except:
                        Parameters.wrong += 1
                        print("del Parameters.RequestIndex[Req.id] error")

                    v.total_passengers += 1
                    v.num_passenger_time[v.num_passengers] += tmp_tt
                    v.num_passengers -= 1

                    v.DoTotalTime += tmp_tt
                    v.TravelTime += tmp_tt


                else:
                    if v.TimeRemain >= 0:
                        tmp_ini, tmp_fin, tmp_reach = compute_intermediate_reach((v.ini, v.fin, v.reach), Req.DoHub,
                                                                                 v.TimeRemain)
                        v.TravelTime += v.TimeRemain
                        if v.ini != tmp_ini:
                            if v.reach == 0:
                                v.TravelDistance += Parameters.DistanceDict[v.ini][tmp_ini]
                                for r in v.passengers:
                                    r.share_distance[v.num_passengers] += Parameters.DistanceDict[v.ini][tmp_ini]

                            else:
                                v.TravelDistance += (
                                    Parameters.DistanceDict[v.ini][v.fin] + Parameters.DistanceDict[v.fin][tmp_ini])
                                for r in v.passengers:
                                    r.share_distance[v.num_passengers] += (
                                        Parameters.DistanceDict[v.ini][v.fin] + Parameters.DistanceDict[v.fin][tmp_ini])

                        v.ini, v.fin, v.reach = tmp_ini, tmp_fin, tmp_reach

                        v.DoTotalTime += v.TimeRemain
                        v.num_passenger_time[v.num_passengers] += v.TimeRemain
                        v.TimeRemain -= tmp_tt

        if v.TimeRemain > 0:
            v.num_passenger_time[0] += v.TimeRemain
            v.IdleTotalTime += v.TimeRemain
            v.TravelTime += v.TimeRemain
            if v.assigned_task is False and v.IsRebalancing is False:
                idle_vehicles.append(v.id)
        v.CurrentTime = time_now + Parameters.TimeWindow
    return idle_vehicles


def rebalance(vehicles, request_todo, idling_vehicles):
    rb_vars = min(len(request_todo),len(idling_vehicles))
    print('reblance_requests', len(request_todo))
    print('idling_vehicles', len(idling_vehicles))
    if rb_vars != 0:
        model = Model('Rebalance')
        model.setParam('OutputFlag', 0)

        r_index = list(request_todo.keys())

        var = model.addVars(idling_vehicles,r_index,lb = 0, ub = 1, name='var')


        model.addConstr(var.sum() == rb_vars)
        model.addConstrs((rb_vsum(var,v_id,r_index) <= 1 for v_id in idling_vehicles), 'vehicle')
        model.addConstrs((rb_rsum(var,idling_vehicles,r_id) <= 1 for r_id in r_index), 'request')

        obj = obj_rb(var,vehicles,request_todo,idling_vehicles)

        model.setObjective(obj)
        model.optimize()

        for v in model.getVars():
            if v.X != 0:
                match = v.Varname[4:-1].split(',')
                request_match = Parameters.RequestIndex[int(match[1])]
                vehicle_match = vehicles[int(match[0])]
                tmp_tt = travel_time_p2h((vehicle_match.ini, vehicle_match.fin, vehicle_match.reach),request_match.PuHub)
                if vehicle_match.TimeRemain >= tmp_tt:
                    Parameters.BugCount += 1

                    if vehicle_match.reach == 0:
                        vehicle_match.TravelDistance += Parameters.DistanceDict[vehicle_match.ini][request_match.PuHub]
                    else:
                        vehicle_match.TravelDistance += (Parameters.DistanceDict[vehicle_match.ini][vehicle_match.fin] + Parameters.DistanceDict[vehicle_match.fin][request_match.PuHub])
                    vehicle_match.ini = request_match.PuHub
                    vehicle_match.fin = request_match.PuHub
                    vehicle_match.reach = 1
                    vehicle_match.RbTotalTime += tmp_tt
                    vehicle_match.TimeRemain -= tmp_tt

                else:
                    vehicle_match.IsRebalancing = True
                    vehicle_match.RebalanceDest = request_match.PuHub
                    tmp_ini, tmp_fin, tmp_reach = compute_intermediate_reach((vehicle_match.ini, vehicle_match.fin, vehicle_match.reach),request_match.PuHub,vehicle_match.TimeRemain)
                    vehicle_match.RbTotalTime += vehicle_match.TimeRemain
                    vehicle_match.TimeRemain = 0
                    if vehicle_match.ini != tmp_ini:
                        if vehicle_match.reach == 0:
                            vehicle_match.TravelDistance += Parameters.DistanceDict[vehicle_match.ini][tmp_ini]
                        else:
                            vehicle_match.TravelDistance += (Parameters.DistanceDict[vehicle_match.ini][vehicle_match.fin] + Parameters.DistanceDict[vehicle_match.fin][tmp_ini])
                    vehicle_match.ini, vehicle_match.fin, vehicle_match.reach = tmp_ini, tmp_fin, tmp_reach


def rb_vsum(var, v_id, r_index):
    sum = 0
    for rd in r_index:
        sum += var[(v_id,rd)]
    return sum

def rb_rsum(var, idling_vehicles, r_id):
    sum = 0
    for v in idling_vehicles:
        sum += var[(v,r_id)]
    return sum

def obj_rb(var, vehicles, request_todo, idling_vehicles):
    sum = 0
    for v_id in idling_vehicles:
        for r_id in request_todo:
            sum += travel_time_p2h((vehicles[v_id].ini, vehicles[v_id].fin, vehicles[v_id].reach),request_todo[r_id].PuHub)*var[(v_id,r_id)]
    return sum


def update_requests(time_now):
    finished_index = []
    ignored_index = []
    for ind,r in enumerate(Parameters.Requests):
        r.trips = []
        r.PossibleVehicles = []
        if time_now + Parameters.TimeWindow > r.LatestPuTime and r.assigned is False:
            r.ignored = True
        if r.ignored is True:
            Parameters.RequestDone.append(r)
            finished_index.append(ind)
            del Parameters.RequestIndex[r.id]
            ignored_index.append(r.id)

    arr = np.array(Parameters.Requests)
    Parameters.Requests = list(np.delete(arr,finished_index))










