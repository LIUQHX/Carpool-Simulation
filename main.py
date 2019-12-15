import pickle
import math
import numpy as np
from param import Parameters
from components import *
from initiate import add_vehicles_from_data, add_requests_from_data
from opt_ridesharing import *
import time, sys

def init_params():
    '''
    init the params.
    :return:
    '''
    Parameters.Requests = []
    Parameters.RequestIndex = {}
    Parameters.Vehicles = []
    Parameters.RequestId = 0
    Parameters.VehicleId = 0
    Parameters.Trips = {}
    Parameters.RequestDone = []
    Parameters.computation_time = 0
    Parameters.IdleVehicles = []
    Parameters.unassigned_requests = []
    Parameters.VehiclePosition = {}
    Parameters.fea_set = {}
    Parameters.fea_set_last_iteration = {}
    Parameters.current_request_id = 0

    Parameters.uber_percent = 0
    Parameters.uber_vehicles = 0
    Parameters.uberpool_vehicles = 0
    Parameters.uber_request_percent = 0
    Parameters.MaxWaiting = 0
    Parameters.MaxDelay = 0
    # Parameters.num_time_windows = 120*24
    Parameters.num_time_windows = 0


if len(sys.argv) == 6:
    n_v = int(sys.argv[1])
    wait = int(sys.argv[2])
    delay = int(sys.argv[3])
    window = int(sys.argv[4])
    date = sys.argv[5]
    print(f"args: num_vechicles:{n_v}, MaxWait:{wait}, MaxDelay:{delay}, Window:{window}, date:{date}")
else:
    ValueError("Input wrong")

init_params()
demands = pickle.load(open(f"./expdata1/demand2016{date}","rb"))

# params
Parameters.uberpool_vehicles = n_v
Parameters.MaxWaiting = wait
Parameters.MaxDelay = delay
Parameters.TimeWindow = window
Parameters.num_time_windows = int(3600/Parameters.TimeWindow)

add_vehicles_from_data(3600*0+30, demands)

rounds = 1
time_start = 0
time_now = time_start + Parameters.TimeWindow
Parameters.TimeEnd = time_now + Parameters.TimeWindow * Parameters.num_time_windows
st = time.time()
while True:
    print("\nrounds:", rounds, "time_now:", time_now)
    if time_now < Parameters.TimeEnd:
        # 取出这个时间片内的订单
        demands = add_requests_from_data((time_now - Parameters.TimeWindow, time_now), demands)

    if len(Parameters.Requests) == 0:
        finished = True
        for r in Parameters.RequestDone:
            if r.ignored:
                continue
            else:
                # 如果还有订单没有被送完就继续
                if r.DoTime == None:
                    finished = False
                    break
        if finished:
            break
    # 得到这个时间片内订单的可拼情况
    rr = combine_rr(time_now)
    # 车
    compute_RV(time_now)
    Parameters.fea_set_last_iteration = Parameters.fea_set
    Parameters.fea_set = {}

    compute_RTV(rr)
    opt_assignment(time_now)

    time_now = time_now + Parameters.TimeWindow
    rounds += 1
    Parameters.current_request_id = Parameters.RequestId
print("Wrong nums:", Parameters.wrong)
end = time.time()
# save results
result = Parameters.RequestDone
d1 = open(f"./trainingdata2/r_{date}_{n_v}_{wait}_{delay}_{window}_norb","wb")
pickle.dump(result, d1)
d1.close()

v_result = Parameters.Vehicles
v1 = open(f"./trainingdata2/v_{date}_{n_v}_{wait}_{delay}_{window}_norb","wb")
pickle.dump(v_result, v1)
v1.close()

print(f"time cost: {end-st} s")