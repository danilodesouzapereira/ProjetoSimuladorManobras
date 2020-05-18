import dss
import networksData

#===================================================================================#
'''
Class to assess fitness function of an individual of SSGA (Sequential Switching GA) 
'''
class AssessSSGAIndiv(object):
	def __init__(self, path_folder, networks_data):
		self.networks_data : networksData.NetworksData = networks_data
		self.feeders_info = networks_data.feeder_protections()

		self.dss = dss.DSS(path_folder) # DSS object for load flow simulations
		self.dss.initialize(self.feeders_info)
		self.list_switches = None


	def update_list_switches(self, list_switches):
		self.list_switches = list_switches

	''' 
	Method to assess load flow-based merit index
	'''
	def load_flow_merit_index(self, dict_sw_states, sw_changes):
		# set initial conditions (right after fault clearing)
		self.dss.set_initial_sw_states(dict_sw_states)

		# initial load flow
		self.dss.solve_power_flow(show_results=False, plot_circuit=False)

		# gets all 3-phase currents
		list_dict_curr_initial = self.dss.get_currents_abs()

		# closes or opens switches
		self.dss.change_sw_states(sw_changes)

		# load flow after switchings
		self.dss.solve_power_flow(show_results=False, plot_circuit=False)

		# reverts switching
		self.dss.restore_sw_states(sw_changes)

		# gets all 3-phase currents. Format: [[ia_1, ib_1, ic_1] , [ia_2, ib_2, ic_2] , ... ]
		list_dict_curr_final = self.dss.get_currents_abs()

		# mod_curr_max = [40., 50., 50.]
		# mod_curr_max = [25., 35., 15., 40., 15.]
		LF_MI = self.compute_load_flow_merit_index(list_dict_curr_initial, list_dict_curr_final)
		return LF_MI


	'''
	Method to compute MI (merit index) related to crew displacement time
	to fulfill all necessary switching operations.
	'''

	def crew_displacement_merit_index(self, st_switch, sw_changes):
		if len(sw_changes) < 2:
			return 0., []

		list_pairs = []
		list_displ_times = []

		# 1st displacement: between start switch and sw_changes' 1st switch
		sw_code1 = st_switch
		sw_code2 = sw_changes[0]['code']
		list_pairs.append([sw_code1, sw_code2])

		# determine pairs of displacement
		for i in range(len(sw_changes) - 1):
			sw_code1 = sw_changes[i]['code']
			sw_code2 = sw_changes[i+1]['code']
			list_pairs.append([sw_code1, sw_code2])

		# for each displacement, determine total time
		tot_time_minutes = 0.
		for displ in list_pairs:
			sw1 = displ[0] ; sw2 = displ[1]
			delta_t = self.displacement_time(sw1, sw2)
			list_displ_times.append(delta_t)
			tot_time_minutes += delta_t

		# calculate crew displacement merit index (cd_mi),
		# based on total time and maximum allowable time (max_time_minutes)
		max_time_minutes = 120. ; tot_time_pu = 1000.
		if tot_time_minutes < max_time_minutes:
			tot_time_pu = tot_time_minutes / max_time_minutes

		return tot_time_pu, list_displ_times


	'''
	Method to compute outage duration merit index (OD_MI), which is based on outage times
	among switching operations. Parameters:
		- dict_sw_states:   dictionary with initial switch states
		- sw_changes:       list of switching operations
		- list_displ_times: list of crew displacement times for switching operations
	'''

	def outage_duration_merit_index(self, dict_sw_states, sw_changes, list_displ_times):
		interr_cust = [] # list with number of interrupted customers
		avg_tot_duration = 0.

		# number of interr. customers at initial condition
		self.dss.set_initial_sw_states(dict_sw_states) # switches' states right after fault clearing
		self.dss.solve_power_flow(show_results=False, plot_circuit=False)
		num_interr_cust = self.dss.interrupted_customers()
		interr_cust.append(num_interr_cust)

		# for each switching operation, evaluate number of interrupted customers
		for i in range(len(sw_changes)):
			change = sw_changes[i]
			self.dss.change_single_sw_state(change) # single switching (open or close)
			self.dss.solve_power_flow(show_results=False, plot_circuit=False)
			num_interr_cust = self.dss.interrupted_customers()
			interr_cust.append(num_interr_cust)

		# compute average total interruptions durations
		avg_tot_duration = 0.0
		sum_cust_interr = 0
		for i in range(len(list_displ_times)):
			displ_time = list_displ_times[i]
			num_interr_cust = interr_cust[i]
			avg_tot_duration += num_interr_cust * displ_time
			if num_interr_cust > 0:
				sum_cust_interr += num_interr_cust
		if sum_cust_interr > 0:
			avg_tot_duration /= sum_cust_interr

		# reverts all previous switching operations
		self.dss.restore_sw_states(sw_changes)

		RT_MI = 1.

		return RT_MI

	'''
	Method to determine crew displacement time between two switches: sw1, sw2.
	If sw2 is automatic, displacement time is considered zero.
	'''
	def displacement_time(self, sw1, sw2):
		# displacement time is zero if sw2 is automatic (circuit break or recloser)
		for sw in self.list_switches:
			if sw['code_sw'] == sw2:
				if sw['type_sw'] == "disjuntor" or sw['type_sw'] == "religadora":
					return 0.

		# determine switches' index, regarding the incidence matrix
		sw1_index, sw2_index = -1, -1
		for sw in self.list_switches:
			if sw['code_sw'] == sw1:
				sw1_index = int(sw['id_sw'])
			elif sw['code_sw'] == sw2:
				sw2_index = int(sw['id_sw'])
		if sw1_index == -1 or sw2_index == -1:
			return 0.

		# get displacement time from incidence matrix
		displ_time = 0.
		mtx = self.networks_data.crew_displ_times_mtx

		if sw1_index < sw2_index:
			mtx_line = mtx[sw1_index]
			displ_time = mtx_line[sw2_index]
		elif sw2_index < sw1_index:
			mtx_line = mtx[sw2_index]
			displ_time = mtx_line[sw1_index]

		return displ_time



	'''
	Method to compute MI (merit index) related to load flow
	'''

	def compute_load_flow_merit_index(self, list_dict_curr_initial, list_dict_curr_final):
		# margin related to base condition (mod_curr_initial)
		M_b = 0.0; w_b_tot = 0.0
		for i in range(len(list_dict_curr_initial)):
			currents_data = list_dict_curr_initial[i]
			sw_name = currents_data['sw_name']
			currents = currents_data['currents']

			I_capacity = 0.
			for cap_data in self.feeders_info:
				if cap_data['prot_switch'] == sw_name:
					I_capacity = cap_data['max_curr']
					break
			if I_capacity == 0.:
				continue

			for ph in range(len(currents)):
				if currents[ph] == 0.0: continue
				diff = I_capacity - currents[ph]
				if diff >= 0.:
					M_b += 1.0 * diff; w_b_tot += 1.0
				else:
					M_b += 5.0 * diff; w_b_tot += 5.0
		if w_b_tot > 0:
			M_b /= w_b_tot
		else:
			M_b = 0.0

		# margin related to final condition (mod_curr_final)
		M = 0.0; w_tot = 0.0
		for i in range(len(list_dict_curr_final)):
			currents_data = list_dict_curr_final[i]
			sw_name = currents_data['sw_name']
			currents = currents_data['currents']

			I_capacity = 0.
			for cap_data in self.feeders_info:
				if cap_data['prot_switch'] == sw_name:
					I_capacity = cap_data['max_curr']
					break
			if I_capacity == 0.:
				continue

			for ph in range(len(currents)):
				if currents[ph] == 0.0: continue
				diff = I_capacity - currents[ph]
				if diff >= 0.:
					M += 1.0 * diff; w_tot += 1.0
				else:
					M += 5.0 * diff; w_tot += 5.0
		if w_tot > 0:
			M /= w_tot
		else:
			M = 0.0

		# compute margin difference in pu (related to base case)
		# Obs: low margin reduction means better solution
		dM_pu = (M_b - M) / M_b

		return dM_pu