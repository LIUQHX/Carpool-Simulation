from param import Parameters


def travel_time_hubs(h1, h2):
    '''
    get distance between two stations.
    :param station1: ID1
    :param station2: ID2
    :return: travel time(s)
    '''
    temp = Parameters.DistanceDict[h1, h2]/(Parameters.Speed*1000)
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


class request():
    '''
    define the class for each request.
    '''
    def __init__(self, id, RequestTime = 0, MaxWaiting = 0, MaxDelay = 0, PuHub = None, DoHub = None, IsUber = False, profit = None, estcost = None, discount = None,pro = None):
        self.id = id
        self.PuHub = PuHub
        self.DoHub = DoHub
        self.assigned = False
        self.share_distance = {i:0 for i in range(1, Parameters.Capacity + 1)}
        self.IsUber = IsUber      #True if the request is uber, False if it is uberpool.
        self.RequestTime = RequestTime      #request time
        self.shared = False     #if it is satisfied by a shared ride.
        self.DoTime = None
        self.PuTime = None
        self.LatestPuTime = self.RequestTime + MaxWaiting      #latest pick up time, which should be r_time + maximum waiting time.
        self.DijTravelTime = self.DijPathTime()     #the travel time between pickup station and drop off station.
        self.EarliestDoTime = self.RequestTime + self.DijTravelTime        #earliest possible drop off time. If picked up immediately and follow the shortest path when request.
        self.ExpectedDoTime = None        #expected drop off time after assigned vehicle to it.
        self.LatestDoTime = self.EarliestDoTime + MaxDelay      #latest drop off time, which should be earliest drop off time + max delay.
        self.ignored = False        #is it ignored in the maximum waiting time.
        self.trips = []     #possible trips that contains this request.
        self.PossibleVehicles = []     #possible vehicles that is able to pick up the request.
        self.Distance = 0
        self.onboard = False
        self.LatestRspTime = self.RequestTime + 420
        self.AssignTime = 0
        self.price = 0
        self.profit = profit
        self.estcost = estcost
        self.discount = discount
        self.probability = pro


    def DijPathTime(self):
        distance = Parameters.DistanceDict[self.PuHub][self.DoHub]
        speed = Parameters.Speed * 1000
        time = (distance / speed)
        return time

    def update_rv(self,trips):
        self.trips = trips



class vehicle():
    '''
    define the class for each vehicle.
    '''
    def __init__(self,id, Capacity, CurrentTime, ini, fin, IsUber):
        self.id = id
        self.CurrentTime = CurrentTime      #current time
        #(ini, fin, reach) defines the position of the vehicle. if the vehicle is at one station, then ini is the station ID, and fin is the destination ID with reach equals 1.
        #if the vehicle is on the way. Then fin is the destination, and ini the origination, reach will be the percentage that the vehicle has completed.
        self.ini = ini
        self.fin = fin
        self.reach = 1
        self.IsUber = IsUber      #True if the vehicle is a uber vehicle, False if it is uberpool.
        self.Capacity = Capacity     #the capacity of the vehicle.
        self.passengers = []     #the set of the passengers in the vehicle.
        self.assigned_trips = []
        self.assigned_requests = None#the trips that the vehicle is assigned to after a time windows's optimization.
        self.num_passenger_time = {i:0 for i in range(0, self.Capacity + 1)}      #the record of how much time that the vehicle is taking i passengers in the whole simulation.
        self.occupied = False      # determine whether there is a passenger in the vehicle in the taxi problem
        self.PuTotalTime = 0        #the total time that used to pick up a passenger in the whole simulation.
        self.DoTotalTime = 0
        self.TimeRemain = 0        #remained time budget in the time window, used in updating the vehicle after fleet assigning.
        self.IsRebalancing = False
        self.RebalanceDest = None
        self.IdleTotalTime = 0
        self.RbTotalTime = 0
        self.num_passengers = 0        #number of passengers in the vehicle.
        self.TravelTime = 0        #total travel distance in the whole simulation.
        self.TravelDistance = 0        #total travel distance in the whole simulation.
        self.total_passengers = 0       #total number of passengers picked up.
        self.assigned_task = False      #if it is assigned to a trip.
        self.possible_requests = []     #list of requests that the vehicle can pick up.


class trip():
    '''
    define the class for each trip.
    '''
    def __init__(self,id, request_list):
        self.id = id
        self.request_list = request_list
        self.vehicle_list = []
        self.penalty = self.get_penalty()


    def get_penalty(self):
        penalty = 0
        for r in self.request_list:
            if r.assigned is True:
                penalty += Parameters.PenaltyAssigned
            else:
                penalty += Parameters.Penalty
        return penalty

    def isequal(self, request_list):
        '''
        check if two trips is the same.
        :param request_list:
        :return:
        '''
        if self.request_list == request_list:
            return True
        else:
            return False


