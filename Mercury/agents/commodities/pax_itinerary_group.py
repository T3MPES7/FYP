from copy import copy
import numpy as np

from Mercury.libs.other_tools import distance_func

# #Used for logging data for datamining purposes
# import logging
# logger = logging.getLogger(__name__)

def func(x, k, k_p, a, b, c):
	return 1./(k*(1.+np.exp(a-b*x**c)))-k_p


class PaxItineraryGroup:
	def __init__(self, n_pax=None, pax_type=None, idd=None, origin_uid=None,
		destination_uid=None, origin_airport_terminal_uid=None,
		destination_airport_terminal_uid=None, origin_airport_icao=None, destination_airport_icao=None, fare=None, dic_soft_cost=None, rs=None, rail=None, origin1=None, destination1=None, origin2=None, destination2=None):
		self.id = idd
		self.original_id = idd
		self.n_pax = n_pax
		self.original_n_pax = n_pax
		self.pax_type = pax_type
		self.fare = fare
		self.rail = rail
		self.origin1 = origin1
		self.origin2 = origin2
		self.destination1 = destination1
		self.destination2 = destination2

		self.idx_last_flight = -1
		self.itinerary = None
		self.multimodal_itinerary = None
		self.old_multimodal_itineraries = {}
		self.initial_sobt = None
		self.final_sibt = None
		self.sobts = []
		self.sibts = []
		self.origin_airport_icao = origin_airport_icao
		self.destination_airport_icao = destination_airport_icao
		self.origin_airport = None
		self.destination_airport = None
		self.distance = None
		self.previous_flight_international = False
		self.sobt_next_flight = None

		self.connecting_pax = False
		self.status = 'at_airport'
		self.in_transit_to = None
		# self.active_flight = None
		self.on_board = None
		self.active_airport = None
		self.time_at_gate = -10  # to be sure first pax are at gate when flight departs.
		self.time_at_platform = -10  # to be sure first pax are at gate when flight departs.
		self.origin_uid = origin_uid
		self.destination_uid = destination_uid
		self.origin_airport_terminal_uid = origin_airport_terminal_uid
		self.destination_airport_terminal_uid = destination_airport_terminal_uid
		self.old_itineraries = []
		self.compensation = 0.
		self.duty_of_care = 0.
		# self.reac_delay = 0.
		self.entitled = False
		self.reac_entitled = False
		self.force_entitled = False
		self.blame_soft_cost_on = None
		self.blame_transfer_cost_on = None
		self.blame_compensation_on = None
		self.modified_itinerary = False
		self.missed_flights = []
		self.aobts = []
		self.aibts = []
		self.multimodal = False
		self.ct = -10
		self.mct = -10
		self.split_pax = []
		#multimodal kpis
		self.ground_mobility_time = 0
		self.gate2kerb_time = 0
		self.kerb2gate_time = 0
		self.rail_aobts = []
		self.rail_aibts = []
		self.rail_sobts = []
		self.rail_sibts = []
		
		self.rs = rs

		self.soft_cost_funcs = {typ: lambda x: func(x, *dic_soft_cost[typ]) for typ in dic_soft_cost.keys()}
		
		# The following is to cut computational time. Instead of computing the above function,
		# we use the following arrays. This cuts the computation by a factor 4.
		xx = np.linspace(0., 120., 120)
		self.soft_cost_values = np.vectorize(self.soft_cost_funcs[self.pax_type])(xx)
		self.soft_cost_funcs_quick = lambda x: 0. if x < 0. else self.soft_cost_values[min(119, int(x))]
		
		self.own_cost_func = self.soft_cost_funcs[self.pax_type]

	def board_next_flight(self, aobt):
		self.in_transit_to = None
		self.idx_last_flight += 1
		self.on_board = self.get_last_flight()
		self.aobts.append(aobt)
		self.active_airport = None

	def unboard_from_flight(self, aibt):
		self.aibts.append(aibt)
		self.on_board = None
		
	def board_next_train(self, aobt):

		self.rail_aobts.append(aobt)


	def unboard_from_train(self, aibt):
		self.rail_aibts.append(aibt)
		self.on_board = None

	def give_itinerary(self, itinerary):
		"""
		itinerary must be a list of flight_uids
		"""
		self.itinerary = itinerary
		self.connecting_pax = len(itinerary) > 1

		# #Logging the grouping event with key details.
		# #used for datamining purposes
		# logger.info(
		# 	"Set itinerary for PaxItineraryGroup %s.",
		# 	self.id,
		# 	extra={
		# 		"env_time": self.env.now,
		# 		"event_type": "ItineraryAssignment",
		# 		"details": {
		# 			"group_id": self.id,
		# 			"itinerary": self.itinerary,
		# 			"connecting_pax": self.connecting_pax,
		# 			"action": "Give Itinerary"
		# 		}
		# 	}
    	# )

	def give_new_itinerary(self, itinerary):
		self.modified_itinerary = True
		self.old_itineraries.append(copy(self.itinerary))

		self.itinerary = itinerary
		# #Logging the itinerary modification event.
		# #used for datamining purposes
		# logger.info(
		# 	"Updated itinerary for PaxItineraryGroup %s.",
		# 	self.id,
		# 	extra={
		# 		"env_time": self.env.now,
		# 		"event_type": "ItineraryModification",
		# 		"details": {
		# 			"group_id": self.id,
		# 			"old_itinerary": self.old_itineraries[-1],
		# 			"new_itinerary": self.itinerary,
		# 			"action": "Give New Itinerary"
		# 		}
		# 	}
		# )
		

	def give_new_train(self, new_train, where='rail_post'):
		if where not in self.old_multimodal_itineraries:
			self.old_multimodal_itineraries[where] = []
		self.old_multimodal_itineraries[where].append(self.rail[where].uid)

		self.rail[where] = new_train
		self.modified_itinerary = True

	def get_original_itinerary(self):
		if len(self.old_itineraries) > 0:
			return self.old_itineraries[0]
		else:
			return self.itinerary

	def get_itinerary(self):
		return self.itinerary

	def get_rail(self):
		return self.rail

	def get_itinerary_so_far(self):
		"""
		Unsafe to use when a passenger is still in a plane.
		"""

		return self.itinerary[:self.idx_last_flight+1]

	def get_last_flight(self):
		return self.itinerary[self.idx_last_flight]

	def get_next_flight(self):
		if self.idx_last_flight < len(self.itinerary)-1:
			return self.itinerary[self.idx_last_flight+1]

	def get_next_flights(self):
		return self.itinerary[self.idx_last_flight+1:]

	def is_last_flight(self, flight_uid):
		return self.itinerary[-1] == flight_uid

	def get_flight_after(self, flight_uid):
		if (flight_uid in self.itinerary) and (not self.is_last_flight(flight_uid)):
			idx = self.itinerary.index(flight_uid)
			return self.itinerary[idx+1]

	def give_new_itinerary_from_last_flight(self, flights):
		"""
		This includes the last flight
		"""
		
		itinerary = list(self.itinerary[:self.idx_last_flight+1]) + list(flights)

		self.give_itinerary(itinerary)

	def prepare_for_simulation(self, airports, flights):
		first_flight = flights[self.itinerary[0]]
		last_flight = flights[self.itinerary[-1]]

		self.active_airport = first_flight.origin_airport_uid
		self.initial_sobt = first_flight.sobt

		self.final_sibt = last_flight.sibt

		self.sobts = [flights[flight].sobt for flight in self.itinerary]
		self.sibts = [flights[flight].sibt for flight in self.itinerary]

		if self.rail['rail_pre'] is None:
			self.in_transit_to = self.itinerary[0]
		else:
			self.in_transit_to = None#self.itinerary[0]#self.rail['rail_pre'].uid
			self.initial_sobt = self.rail['rail_pre'].times[self.origin1]['departure_time']
			self.multimodal = True
			self.time_at_gate = 9999999
			self.rail_sobts.append(self.rail['rail_pre'].times[self.origin1]['departure_time'])
			self.rail_sibts.append(self.rail['rail_pre'].times[self.destination1]['arrival_time'])
		
		if self.rail['rail_post'] is None:
			self.final_sibt = last_flight.sibt
		else:
			self.final_sibt = self.rail['rail_post'].times[self.destination2]['arrival_time']
			self.multimodal = True
			self.rail_sobts.append(self.rail['rail_post'].times[self.origin2]['departure_time'])
			self.rail_sibts.append(self.rail['rail_post'].times[self.destination2]['arrival_time'])

		self.origin_airport = first_flight.origin_airport_uid
		self.destination_airport = last_flight.destination_airport_uid
		self.distance = distance_func(airports[self.origin_airport].coords,
								airports[self.destination_airport].coords)

		self.previous_flight_international = first_flight.international
		self.sobt_next_flight = first_flight.sobt

	def soft_cost_func(self, tt):
		if tt > 0.:
			# return self.n_pax * self.soft_cost_funcs[self.pax_type](tt)
			return self.n_pax * self.own_cost_func(tt)
		else:
			return 0.
		
	def __repr__(self):
		return "Pax group " + str(self.id) + " with " + str(self.n_pax) + ' pax'
