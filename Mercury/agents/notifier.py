# import sys
# sys.path.insert(1, '..')
import simpy
import numpy as np
import pandas as pd
import datetime as dt
from .agent_base import Agent, Role
from Mercury.core.delivery_system import Letter
from Mercury.libs.uow_tool_belt.general_tools import build_col_print_func



class Notifier(Agent):
	dic_role = {'SimulationProgressTracker':'spt',
				'InformationProvider':'ip',
				}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


		# Roles
		#Create queue
		self.spt = SimulationProgressTracker(self)
		self.ip = InformationProvider(self)


		#Internal knowledge
		self.update_interval = 1
		self.min_time = self.min_time
		self.max_time = self.max_time

		self.env.process(self.spt.track_simulation())
		self.reference_dt = self.reference_dt

		self.cr = None  # Pointer to the Central Registry. To be filled when registering agent in cr in world builder
		self.cr_functions = {}

	def set_log_file(self, log_file):
		global aprint
		aprint = build_col_print_func(self.acolor, verbose=self.verbose, file=log_file)

		global mprint
		mprint = build_col_print_func(self.mcolor, verbose=self.verbose, file=log_file)


	def receive(self, msg):
		# mprint("EAMAN message")

		if msg['type']=='response':
			# print(msg)
			pass
		elif msg['type']=='request':
			self.ip.wait_for_request(msg)
		else:
			aprint ('WARNING: unrecognised message type received by', self, ':', msg['type'])

	def __repr__(self):
		return "Notifier " + str(self.uid)


class SimulationProgressTracker(Role):
	"""
	SPT

	Description: Tracks simulation time and broadcasts using external messages (should be used with rabbitmq hmi)

	"""

	def track_simulation(self):
		#print('SimulationProgressTracker-',self.agent.env.now, self.agent.min_time, self.agent.max_time)
		for i in range(round((self.agent.max_time-self.agent.min_time)/(6*60))+round((self.agent.min_time)/(6*60))):
			#print('SimulationProgressTracker+',self.agent.env.now)
			self.send_notification(self.agent.env.now)
			yield self.agent.env.timeout(6*60)

	def send_notification(self, simulation_time):
		msg = Letter()
		msg['to'] = 'request_reply_example' # 5555
		msg['type'] = 'mercury.simulation_time'
		msg['function'] = ''
		msg['body'] = [str(simulation_time)]
		self.send(msg)

class InformationProvider(Role):
	"""
	IP

	Description: Enables to query Central Registry via external messages

	"""
	def fn_caller(self,fn,arg):

		result = []
		for x in arg:
			if int(x) in self.agent.cr.flight_uids:
				result.append(fn(self.agent.cr.flight_uids[int(x)]))
			else:
				result.append('none')
		return result

	def wait_for_request(self,msg):
		# print('request', msg)
		if msg['function'] == 'get_schedules':

			info = self.agent.cr.get_schedules()
		elif msg['function'] in self.agent.cr_functions:
			fn = getattr(self.agent.cr, msg['function'])
			info = self.fn_caller(fn,msg['body'])
		else:
			info = ''
		#print(msg['function'] in self.agent.cr_functions)
		#info = self.agent.reference_dt+dt.timedelta(minutes=self.agent.cr.get_ibt(self.agent.cr.flight_uids[39136]))
		for x in info:
			x['sobt'] = self.agent.reference_dt+dt.timedelta(minutes=x['sobt'])
			x['sibt'] = self.agent.reference_dt+dt.timedelta(minutes=x['sibt'])
		self.send_notification([str(x) for x in info])


	def send_notification(self, load):
		msg = Letter()
		msg['to'] = 'request_reply_example' # 5555
		msg['type'] = 'information'
		msg['function'] = ''
		msg['body'] = load
		self.send(msg)
