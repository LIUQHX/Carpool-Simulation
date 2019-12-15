import pickle
# from sklearn.externals import joblib

class Parameters(object):
    DistanceDict = pickle.load(open("./DijShortestPathLength", "rb"))
    PredecessorDict = pickle.load(open("./DijPredecessorDict", "rb"))
#     puhub_type_dict = pickle.load(open("./pu_type_dict","rb"))
#     dohub_type_dict = pickle.load(open("./do_type_dict","rb"))
#     DT = joblib.load("./model/dt_test")
#     LR = joblib.load("./model/lr")

    MaxWaiting = 301  # 最长等待时间
    MaxWaitingRsp = 301  # ？
    MaxDelay = 0  # 最长绕路时间？
    Speed = 0.006  # 行车速度

    Penalty = 0
    PenaltyAssigned = 0
    Capacity = 2
    num_vehicles = 3000
    uber_percent = 1  # percent of uber vehicles.
    uber_request_percent = 1
    uber_vehicles = int(num_vehicles * uber_percent)
    uberpool_vehicles = num_vehicles - uber_vehicles
    # 定价相关
    uber_base_fare = 2.55
    uber_per_second_rates = 0.00583
    uber_per_km_rates = 1.087
    uber_minimum_fare = 8

    Discount = 1
    max_link_vehicles = 20

    TimeWindow = 30
    num_time_windows = 0
    TimeEnd = 0

    Requests = []
    Vehicles = []
    RequestIndex = {}
    RequestId = 0
    VehicleId = 0
    VehiclePosition = {}

    Trips = {}
    RequestDone = []

    computation_time = 0
    time_last = 0
    rr_graph_time = 0
    rv_time = 0
    rtv_time = 0
    rb_time = 0

    TotalDistance = 0

    IdleVehicles = []
    unassigned_requests = []

    PU = 0
    DO = 0
    Assign = 0

    BugCount = 0

    fea_set_last_iteration = {}
    fea_set = {}
    current_request_id = 0

    vehicle_timelimit = 0.5

    wrong = 0





















