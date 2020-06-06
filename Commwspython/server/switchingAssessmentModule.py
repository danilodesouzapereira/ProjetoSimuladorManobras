import dss
import networksData
import math


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
	Method to identify all isolated vertices, from edges [u,v,w]
	'''
	def isolated_vertices(self, all_closed_edges):

		list_edges = []
		for edge_dict in all_closed_edges:
			edge = [edge_dict['v1'], edge_dict['v2'], 1]
			list_edges.append(edge)

		repeat = True
		vertices_set = {0}
		while repeat:
			repeat = False
			for i in reversed(range(len(list_edges))):
				edge = list_edges[i]
				if edge[0] in vertices_set or edge[1] in vertices_set:
					vertices_set.add(edge[0])
					vertices_set.add(edge[1])
					list_edges.remove(edge)
					repeat = True

		isol_vertices = set()
		for edge in list_edges:
			isol_vertices.add(edge[0])
			isol_vertices.add(edge[1])
		return(list(isol_vertices))


	'''
	Method to determine the number of isolated customers, based on list of isolated vertices
	'''
	def isolated_customers(self, vertice_dicts, list_isol_vertices):
		isol_cust = 0
		for vert in list_isol_vertices:
			for dict in vertice_dicts:
				if dict['id'] == int(vert):
					isol_cust += dict['customers']
					break
		return isol_cust


	'''
	Method to compute outage duration merit index (OD_MI), which is based on outage times
	among switching operations. Parameters:
		- sw_changes:       list of switching operations, containing: switch code and action (op/cl)
		- list_displ_times: list of crew displacement times for all switching operations		
		- all_available_edges: dicts with information regarding all available edges
		- all_closed_edges: dicts with information regarding closed edges
		- vertice_dicts: list of dicts with vertice_dicts' info (id and number of customers)
	'''
	def outage_duration_merit_index(self, sw_changes, list_displ_times, all_available_edges, all_closed_edges, vertice_dicts):

		interr_cust = []        # list with number of interrupted customers
		avg_tot_duration = 0.0  # average total duration
		sum_cust_interr = 0     # summation of total customers' interruptions

		# 1 - Interr. customers at initial condition
		list_isol_vertices = self.isolated_vertices(all_closed_edges)
		num_interr_cust = self.isolated_customers(vertice_dicts, list_isol_vertices)
		interr_cust.append(num_interr_cust)

		# 2 - For each switching operation, evaluate number of interrupted customers
		for i in range(len(sw_changes)):
			change = sw_changes[i]
			if change['action'] == 'cl':
				for edge_dict in all_available_edges:
					if edge_dict['switch'] == change['code']:
						all_closed_edges.append(edge_dict)
						break
			elif change['action'] == 'op':
				for edge_dict in all_available_edges:
					if edge_dict['switch'] == change['code']:
						all_closed_edges.remove(edge_dict)

			list_isol_vertices = self.isolated_vertices(all_closed_edges)
			num_interr_cust = self.isolated_customers(vertice_dicts, list_isol_vertices)
			interr_cust.append(num_interr_cust)

		# 3 - Compute average total interruptions durations
		for i in range(len(list_displ_times)):
			displ_time = list_displ_times[i]
			num_interr_cust = interr_cust[i]
			avg_tot_duration += num_interr_cust * displ_time
			if num_interr_cust > 0:
				sum_cust_interr += num_interr_cust
		if sum_cust_interr > 0:
			avg_tot_duration /= sum_cust_interr

		# compute Outage Duration Merit Index, based on a maximum OD value
		MAX_OD = 30 ; 1000.0
		if avg_tot_duration < MAX_OD:
			OD_MI = avg_tot_duration / MAX_OD

		return OD_MI


	'''
	Method to determine crew displacement time between two switches: sw1, sw2.
	If sw2 is automatic, displacement time is considered zero.
	'''

	def displacement_time(self, sw1, sw2):
		# displacement time is zero if sw2 is automatic (circuit breaker or recloser)
		for sw in self.list_switches:
			if sw['code_sw'] == sw2:
				if sw['type_sw'].lower() == "disjuntor" or sw['type_sw'].lower() == "religadora":
					return 0.

		# get switches' geographic positions
		x1 = 0 ; x2 = 0 ; y1 = 0 ; y2 = 0
		for sw in self.networks_data.list_switches_dicts:
			if sw1.lower() == sw['code'].lower():
				x1 = int(sw['coord_x_m'])
				y1 = int(sw['coord_y_m'])
				break
		for sw in self.networks_data.list_switches_dicts:
			if sw2.lower() == sw['code'].lower():
				x2 = int(sw['coord_x_m'])
				y2 = int(sw['coord_y_m'])
				break

		# verifies if one the keys was not found
		if (x1 == 0 and y1 == 0) or (x2 == 0 and y2 == 0):
			return 0.0

		# compute geographic distance between sw1 and sw2
		dist_m = math.sqrt(math.pow(x1-x2, 2) + math.pow(y1-y2, 2))
		# average displacement speed
		avg_spd_km_h = 50.
		avg_spd_m_s = avg_spd_km_h / 3.6
		# compute displacement time, in minutes
		displ_time_min = (dist_m / avg_spd_m_s) / 60.

		# # determine switches' index, regarding the incidence matrix
		# sw1_index, sw2_index = -1, -1
		# for sw in self.list_switches:
		# 	if sw['code_sw'] == sw1:
		# 		sw1_index = int(sw['id_sw'])
		# 	elif sw['code_sw'] == sw2:
		# 		sw2_index = int(sw['id_sw'])
		# if sw1_index == -1 or sw2_index == -1:
		# 	return 0.
		#
		# # get displacement time from incidence matrix
		# displ_time = 0.
		# mtx = self.networks_data.crew_displ_times_mtx
		#
		# if sw1_index < sw2_index:
		# 	mtx_line = mtx[sw1_index]
		# 	displ_time = mtx_line[sw2_index]
		# elif sw2_index < sw1_index:
		# 	mtx_line = mtx[sw2_index]
		# 	displ_time = mtx_line[sw1_index]

		return displ_time_min



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