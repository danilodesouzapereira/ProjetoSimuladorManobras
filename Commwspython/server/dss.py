import win32com.client
from win32com.client import makepy
import sys
import gc
import numpy as np
import pythoncom

'''
	Class aimed to provide load flow calculation for 
	a given power distribution network.
'''
class DSS(object):
	def __init__(self, dss_folder):
	
		pythoncom.CoInitialize()
	
		self.dss_folder = dss_folder	
		self.dssObj = win32com.client.Dispatch("OpenDSSEngine.DSS")				
		if not self.dssObj.Start(0):
			print("opendss nao inicializado")			
		self.dssText = self.dssObj.Text
		self.dssCircuit = self.dssObj.ActiveCircuit
		self.dssSolution = self.dssCircuit.Solution

		# list of switches' dictionaries
		self.list_sw_dicts = []


	'''
	Set initial settings
	'''
	def initialize(self, feeders_info):
		self.dssObj.ClearAll()
		self.dssText.Command = "set datapath=(" + self.dss_folder + ")"
		self.dssText.Command = "compile " + self.dss_folder + "\\master.dss"

		# list "list_sw_dicts" with dictionaries containing switches information
		for fd_info in feeders_info:
			dict_sw = {'name':fd_info['prot_switch'], 'currents': [0.0, 0.0, 0.0]}
			self.list_sw_dicts.append(dict_sw)

		# gets phases strings for each switch
		self.get_sections_phases()


	'''
	Method to get all sections' phases strings
	'''
	def get_sections_phases(self):
		DSSLines = self.dssCircuit.Lines
		DSSActiveElement = self.dssCircuit.ActiveCktElement ; iLine = DSSLines.First

		while iLine > 0:
			# gets section's name
			linename = str(DSSActiveElement.Name)
			linename = linename[5:len(linename)]

			# try to find switch dictionary related to the section
			i = -1
			for i in range(len(self.list_sw_dicts)):
				dict_sw = self.list_sw_dicts[i]
				if dict_sw['name'] != linename: i = -1
				else: break

			# didn't find switch dictionary related to the section
			if i == -1:
				iLine = DSSLines.Next ; continue

			# gets switch dictionary
			dict_sw = self.list_sw_dicts[i]

			# gets buses' information
			bus1 = DSSLines.Bus1 ; bus2 = DSSLines.Bus2
			bus1_code = bus1[:bus1.find(".")] ; bus2_code = bus2[:bus2.find(".")]

			# moves sections' iterator
			iLine = DSSLines.Next

			# gets the section's phase indication and phases strings
			phase_indication = bus1[bus1.find(".") + 1:]
			if phase_indication == "1.2.3": dict_sw.update({'str_phases':'abc'})
			elif phase_indication == "1":   dict_sw.update({'str_phases':'a'})
			elif phase_indication == "2":   dict_sw.update({'str_phases':'b'})
			elif phase_indication == "3":   dict_sw.update({'str_phases':'c'})
			elif phase_indication == "1.2": dict_sw.update({'str_phases':'ab'})
			elif phase_indication == "1.3": dict_sw.update({'str_phases':'ac'})
			elif phase_indication == "2.3": dict_sw.update({'str_phases':'bc'})


	'''
	Commands to open/close switches
	'''
	def change_sw_states(self, sw_changes):
		for change in sw_changes:
			command = "edit line." + change['code'] + " enabled="
			if change['action'] == 'cl': command += "true"
			else: command += "false"
			self.dssText.Command = command


	'''
	Commands to restore switches initial states
	'''
	def restore_sw_states(self, sw_changes):
		for change in sw_changes:
			command = "edit line." + change['code'] + " enabled="
			if change['action'] == 'cl':
				command += "false" # reverse command
			else:
				command += "true" # reverse command
			self.dssText.Command = command


	'''
	Command to execute power flow (OPENDSS SOLVE COMMAND)
	'''
	def solve_power_flow(self, show_results = False, plot_circuit = False):
		self.dssSolution.Solve()
		if show_results:
			self.dssText.Command = "show voltage ln nodes"
			self.dssText.Command = "show current elements"
		if plot_circuit:
			self.dssText.Command = "plot circuit Power max=1000 dots=n labels=n C1=$00FF0000"


	'''
	Gets absolute values of all 3-phase computed currents
	'''
	def get_currents_abs(self):
		currents = []
		self.get_computed_currents()
		for sw_dict in self.list_sw_dicts:
			sw_currents = sw_dict.get('currents')
			if sw_currents is None:
				currents.append([0.0, 0.0, 0.0])
			else:
				ia = round(abs(sw_currents[0]), 3)
				ib = round(abs(sw_currents[1]), 3)
				ic = round(abs(sw_currents[2]), 3)
				currents.append([ia, ib, ic])
		return currents


	'''
	Sets initially closed switches
	'''
	def set_initial_sw_states(self, dict_sw_states):
		DSSLines = self.dssCircuit.Lines
		# DSSActiveElement = self.dssCircuit.ActiveCktElement
		iLine = DSSLines.First
		while iLine > 0:
			sw_code = DSSLines.Name
			if sw_code in dict_sw_states['closed_switches']:
				self.dssText.Command = "edit line." + sw_code + " enabled=true"
			elif sw_code in dict_sw_states['opened_switches']:
				self.dssText.Command = "edit line." + sw_code + " enabled=false"
			iLine = DSSLines.Next

	'''
	Method to get computed load flow currents, which are stored in switches dictionaries
	'''
	def get_computed_currents(self):
		DSSLines = self.dssCircuit.Lines
		DSSActiveElement = self.dssCircuit.ActiveCktElement
		iLine = DSSLines.First

		while iLine > 0:
			linename = DSSLines.Name

			# try to find dictionary associated with the switch
			i = -1
			for i in range(len(self.list_sw_dicts)):
				sw_dict = self.list_sw_dicts[i]
				if sw_dict['name'] != linename: i = -1
				else: break

			# didn't find switch dictionary related with the switch
			if i == -1:
				iLine = DSSLines.Next
				continue

			# gets sw dict
			sw_dict = self.list_sw_dicts[i] ; str_phases = sw_dict['str_phases']
			list_currents = DSSActiveElement.Currents

			if  str_phases == "abc":
				ia = complex(list_currents[0], list_currents[1]) ; ib = complex(list_currents[2], list_currents[3]) ; ic = complex(list_currents[4], list_currents[5])
			elif  str_phases == "a":
				ia = complex(list_currents[0], list_currents[1]) ; ib = complex(0.0, 0.0) ; ic = complex(0.0, 0.0)
			elif  str_phases == "b":
				ia = complex(0.0, 0.0); ib = complex(list_currents[0], list_currents[1]) ; ic = complex(0.0, 0.0)
			elif  str_phases == "c":
				ia = complex(0.0, 0.0) ; ib = complex(0.0, 0.0) ; ic = complex(list_currents[0], list_currents[1])
			elif str_phases == "ab":
				ia = complex(list_currents[0], list_currents[1]) ; ib = complex(list_currents[2], list_currents[3]) ; ic = complex(0.0, 0.0)
			elif str_phases == "ac" or str_phases == "ca":
				ia = complex(list_currents[0], list_currents[1]) ; ib = complex(0.0, 0.0); ic = complex(list_currents[2], list_currents[3])
			elif str_phases == "bc":
				ia = complex(0.0, 0.0) ; ib = complex(list_currents[0], list_currents[1]) ; ic = complex(list_currents[2], list_currents[3])

			sw_dict.update({'currents':[ia, ib, ic]})
			iLine = DSSLines.Next

		for sw_dict in self.list_sw_dicts:
			print("dict: " + str(sw_dict))