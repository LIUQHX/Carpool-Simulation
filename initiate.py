import numpy as np
import components
import math
import pandas as pd
from scipy import optimize
from param import Parameters

def travle_time_gps(ori_lon,ori_lat, dest_lon,dest_lat):
    '''
    Compute the travel time just according to the coordinates.
    :param ori_gps:
    :param dest_gps:
    :return:
    '''
    lat1 = ori_lat
    lon1 = ori_lon
    lat2 = dest_lat
    lon2 = dest_lon
    speed_km_s =  Parameters.Speed
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    dist_km = 6367 * c
    return dist_km / speed_km_s


def add_requests_from_data(time_interval, demands):
    '''
    add requests for specific time windows
    :param time_interval: the specific time interval we are interested in. (start, end)
    :param demands: requests
    :return:
    '''
    #1367337600, 1367344500

    for ind, i in enumerate(demands):
        if time_interval[0] <= i[0] < time_interval[1]:
            if i[1] != i[5]:        #ori != dest
                #this request is in the specific time interval, init value to request.
                #id, pu_location = None, do_location = None, r_time = 0, max_waiting = 0, max_delay = 0, pu_station = None, do_station = None):
                # 随机生成拼车或是快车订单
                if np.random.random() > Parameters.uber_request_percent:     #uberpool
                    request = components.request(Parameters.RequestId, i[0], Parameters.MaxWaiting, Parameters.MaxDelay, int(i[1]), int(i[5]), False)      #pu_location = None, do_location = None, r_time = 0, max_waiting = 0
                else:
                    request = components.request(Parameters.RequestId, i[0], Parameters.MaxWaiting, Parameters.MaxDelay, int(i[1]), int(i[5]), True)      #pu_location = None, do_location = None, r_time = 0, max_waiting = 0

                Parameters.Requests.append(request)
                Parameters.RequestIndex[Parameters.RequestId] = request
                Parameters.RequestId += 1
            else:
                continue
        elif i[0] >= time_interval[1]:
            # 扔掉之前的订单
            demands = demands[ind:]
            break
    return demands



def add_vehicles_from_data(time_now, demands):
    '''
    Add vehicles to the simulation.
    :param time_now:
    :param n_vehicles:
    :param demands: start time, start station, end time, start longi, start lati, end station, end longi, end lati
    :return:
    '''
    #draw samples from the demands
    length = len(demands)
    # 随机选择快车数个订单
    uber_index = np.random.choice(length, Parameters.uber_vehicles, replace=False)
    uber_chosen = demands[uber_index, :]
    # 随机选择拼车数个订单
    uberpool_index = np.random.choice(length, Parameters.uberpool_vehicles, replace=False)
    uberpool_chosen = demands[uberpool_index, :]

    for i in range(Parameters.uber_vehicles):
        temp_vehicle = components.vehicle(Parameters.VehicleId, 1, time_now, int(uber_chosen[i][1]), int(uber_chosen[i][1]), True)
        Parameters.Vehicles.append(temp_vehicle)
        Parameters.VehicleId += 1

    # 模拟车的起点和订单起点相同
    for i in range(Parameters.uberpool_vehicles):
        temp_vehicle = components.vehicle(Parameters.VehicleId, Parameters.Capacity, time_now, int(uberpool_chosen[i][1]),
                                          int(uberpool_chosen[i][1]), False)
        Parameters.Vehicles.append(temp_vehicle)
        Parameters.VehicleId += 1


def add_requests_from_data_ml(time_interval, demands,wt):
    '''
    add requests for specific time windows
    :param time_interval: the specific time interval we are interested in. (start, end)
    :param demands: requests
    :return:
    '''
    #1367337600, 1367344500

    for ind, i in enumerate(demands):
        if time_interval[0] <= i[0] < time_interval[1]:
            if i[1] != i[5]:        #ori != dest
                #this request is in the specific time interval, init value to request.
                #id, pu_location = None, do_location = None, r_time = 0, max_waiting = 0, max_delay = 0, pu_station = None, do_station = None):
                timetype = time_classify(wt,i[0])
                try:
                    putype = Parameters.puhub_type_dict[int(i[1])]
                except:
                    putype = 0
                try:
                    dotype = Parameters.dohub_type_dict[int(i[5])]
                except:
                    dotype = 0
                dt_dis = Parameters.DistanceDict[int(i[1])][int(i[5])]
                lr_dis = get_dis(dt_dis)
                sratio = share_dis_est(dt_dis)
                dratio = total_dis_est(dt_dis)

                lt = opt_discount(i[0],dt_dis,i[2],i[3],i[6],i[7],dt_dis,lr_dis,sratio,dratio,timetype,putype,dotype)

                profit = lt[0]
                cost = lt[1]
                discount = lt[2]
                probability = lt[3]

                if np.random.random() > Parameters.uber_request_percent:     #uberpool
                    request = components.request(Parameters.RequestId, i[0], Parameters.MaxWaiting, Parameters.MaxDelay, int(i[1]), int(i[5]), False,profit,cost,discount,probability)      #pu_location = None, do_location = None, r_time = 0, max_waiting = 0
                else:
                    request = components.request(Parameters.RequestId, i[0], Parameters.MaxWaiting, Parameters.MaxDelay, int(i[1]), int(i[5]), True,profit,cost,discount,probability)      #pu_location = None, do_location = None, r_time = 0, max_waiting = 0

                Parameters.Requests.append(request)
                Parameters.RequestIndex[Parameters.RequestId] = request
                Parameters.RequestId += 1
            else:
                continue
        elif i[0] >= time_interval[1]:
            demands = demands[ind:]
            break
    return demands


def time_classify(w, time):
    if w == 0:
        if time < 7200:
            return 2
        elif time < 4 * 3600:
            return 1
        elif time < 8 * 3600:
            return 0
        elif time < 12 * 3600:
            return 1
        else:
            return 2
    else:
        if time < 6 * 3600:
            return 0
        elif time < 8 * 3600:
            return 1
        elif time < 10 * 3600:
            return 2
        elif time < 17 * 3600:
            return 1
        elif time < 21 * 3600:
            return 2
        else:
            return 1

def get_dis(dis):
    if dis<14000:
        return (dis/14000)
    else:
        return 1

def share_dis_est(dis):
    if dis < 2000:
        return 0.795
    elif dis < 4000:
        return 0.7
    elif dis < 10000:
        return 0.68
    elif dis < 12000:
        return 0.66
    elif dis < 14000:
        return 0.64
    else:
        return 0.63

def total_dis_est(dis):
    if dis<2000:
        return 1.07
    elif dis < 4000:
        return 1.16
    elif dis < 6000:
        return 1.14
    elif dis < 8000:
        return 1.12
    elif dis < 10000:
        return 1.11
    elif dis < 12000:
        return 1.10
    elif dis<14000:
        return 1.09
    else:
        return 1.08

def opt_discount(t,dis,pulog,pulat,dolog,dolat,dtdis,lrdis,sratio,dratio,t_type,pu_type,do_type):
    price = get_price(dis)
    ratio = get_costpct(t, pulog, pulat, dolog, dolat, dtdis, sratio, dratio)
    estcost = 1.544 * (dis / 1000) * ratio
    c = Parameters.LR.coef_[0][0] * t_type + Parameters.LR.coef_[0][1] * pu_type + Parameters.LR.coef_[0][2] * do_type + Parameters.LR.coef_[0][3] * lrdis

    def f(x):
        return -(price * x - estcost) / (1 + math.exp(-(Parameters.LR.coef_[0][4] * x + c + Parameters.LR.intercept_)))

    dis_temp = optimize.fminbound(f, 0.608, 1)
    profit_temp = -f(optimize.fminbound(f, 0.608, 1))
    cost_temp = estcost
    pro = 1/(1 + math.exp(-(Parameters.LR.coef_[0][4] * dis_temp + c + Parameters.LR.intercept_)))
    return (profit_temp,cost_temp,dis_temp,pro)




def get_costpct(t, pu_lon, pu_lat, do_lon, do_lat, dis, share_pct, share_ratio):
    tt = [t]
    plon = [pu_lon]
    plat = [pu_lat]
    dlon = [do_lon]
    dlat = [do_lat]
    dist = [dis]

    d_tmp = {'time': tt, 'PickupLon': plon, 'PickupLat': plat, 'DropoffLon': dlon, 'DropoffLat': dlat, 'Distance': dist}
    df_tmp = pd.DataFrame(d_tmp, columns=['time', 'PickupLon', 'PickupLat', 'DropoffLon', 'DropoffLat', 'Distance'])
    X_predict = df_tmp.values[:, 0:6]
    pro = Parameters.DT.predict_proba(X_predict)
    p = pro[0][1]
    cost_pct = p * (0.5 * share_ratio * share_pct + share_ratio * (1 - share_pct)) + (1 - p)

    if cost_pct > 1:
        cost_pct = 1
    return cost_pct

def get_price(dis):
    base = Parameters.uber_base_fare
    cost = 2.05867*dis/1000
    price = base + cost
    if price <= Parameters.uber_minimum_fare:
        return Parameters.uber_minimum_fare
    else:
        return price


def add_requests_from_data_ml2(time_interval, demands,wt):
    '''
    add requests for specific time windows
    :param time_interval: the specific time interval we are interested in. (start, end)
    :param demands: requests
    :return:
    '''
    #1367337600, 1367344500

    for ind, i in enumerate(demands):
        print(ind)
        if time_interval[0] <= i[0] < time_interval[1]:
            if i[1] != i[5]:        #ori != dest
                #this request is in the specific time interval, init value to request.
                #id, pu_location = None, do_location = None, r_time = 0, max_waiting = 0, max_delay = 0, pu_station = None, do_station = None):
                timetype = time_classify(wt,i[0])
                try:
                    putype = Parameters.puhub_type_dict[int(i[1])]
                except:
                    putype = 0
                try:
                    dotype = Parameters.dohub_type_dict[int(i[5])]
                except:
                    dotype = 0
                dt_dis = Parameters.DistanceDict[int(i[1])][int(i[5])]
                lr_dis = get_dis(dt_dis)
                sratio = share_dis_est(dt_dis)
                dratio = total_dis_est(dt_dis)

                lt = ori_discount(i[0],dt_dis,i[2],i[3],i[6],i[7],dt_dis,lr_dis,sratio,dratio,timetype,putype,dotype)

                profit = lt[0]
                cost = lt[1]

                probability = lt[2]

                if np.random.random() > Parameters.uber_request_percent:     #uberpool
                    request = components.request(Parameters.RequestId, i[0], Parameters.MaxWaiting, Parameters.MaxDelay, int(i[1]), int(i[5]), False,profit,cost,1,probability)      #pu_location = None, do_location = None, r_time = 0, max_waiting = 0
                else:
                    request = components.request(Parameters.RequestId, i[0], Parameters.MaxWaiting, Parameters.MaxDelay, int(i[1]), int(i[5]), True,profit,cost,1,probability)      #pu_location = None, do_location = None, r_time = 0, max_waiting = 0

                Parameters.Requests.append(request)
                Parameters.RequestIndex[Parameters.RequestId] = request
                Parameters.RequestId += 1
            else:
                continue
        elif i[0] >= time_interval[1]:
            demands = demands[ind:]
            break
    return demands


def ori_discount(t,dis,pulog,pulat,dolog,dolat,dtdis,lrdis,sratio,dratio,t_type,pu_type,do_type):
    price = get_price(dis)
    ratio = get_costpct(t, pulog, pulat, dolog, dolat, dtdis, sratio, dratio)
    estcost = 1.544 * (dis / 1000) * ratio
    c = Parameters.LR.coef_[0][0] * t_type + Parameters.LR.coef_[0][1] * pu_type + Parameters.LR.coef_[0][2] * do_type + Parameters.LR.coef_[0][3] * lrdis

    pro = 1/(1 + math.exp(-(Parameters.LR.coef_[0][4] * 0.78 + c + Parameters.LR.intercept_)))
    cost_temp = estcost
    profit_temp = (price*0.78 - estcost)*pro
    return (profit_temp,cost_temp,pro)