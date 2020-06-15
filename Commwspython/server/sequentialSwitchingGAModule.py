import random
import itertools
import graphModule
import switchingAssessmentModule



#===================================================================================#
''' 
Class to represent optimal switching Genetic Algorithm Individuals
'''
class IndivSS:
	def __init__(self):
		self.switching_chromosome = []
		self.switching_chromosome_simple = []
		self.fitness_function = 0.
		self.fitness_function_components = {}
		self.list_sw_changes = []
		self.sw_seq = []                   # Sintax: [[[u_cl,v_cl,w_cl],[u_op,v_op,w_op], ...]
		self.sw_codes_dicts = []           # Sintax: [{'sw_code':[u,v,w], 'action':'op'}, ...]
		self.dicts_sw_changes = []         # Sintax: {'code':sw_code, 'action':'op'})
		self.dicts_sw_changes_simple = []  # Sintax: {'code': sw_code, 'action': sw_code_dict['action']}


#===================================================================================#

''' 
Main class, responsible for determining the SSGA (SEQUENTIAL SWITCHING GENETIC ALGORITHM) 
'''
class SSGA:
	def __init__(self, graph, initial_edges, SSGA_settings, sw_assessment, networks_data, merit_index_conf):
		# all data concerning networks
		self.networks_data = networks_data

		# get configurations concerning merit index calculation
		self.merit_index_conf = merit_index_conf

		# graph data
		list_switches = self.networks_data.get_list_switches()

		# fundamental parameters
		self.sw_assessment : switchingAssessmentModule.AssessSSGAIndiv  = sw_assessment
		self.sw_assessment.update_list_switches(list_switches)
		self.graph = graph

		# local variables
		self.initial_edges = initial_edges
		self.initial_graph_data = {"vertices":[], "edges":[]}
		self.final_graph_data = {"vertices":[], "edges":[]}
		self.list_closed_switches = []  # (1) switches closed (initially opened ==> finally closed)
		self.list_opened_switches = []  # (2) switches opened (initially closed ==> finally opened)
		self.list_cl_op_sw = []         # (1) + (2)
		self.list_ga_individuals = []   # list of GA individuals

		# Sw. Sequencing GA settings
		self.SSGA_settings = SSGA_settings
		self.num_generations = SSGA_settings.get('num_generations')
		self.num_individuals = SSGA_settings.get('num_individuals')
		self.pc = SSGA_settings.get('pc')
		self.pm = SSGA_settings.get('pm')
		self.min_porc_fitness = SSGA_settings.get('min_porc_fitness')
		self.start_switch = SSGA_settings.get('start_switch').lower()

		# overall best individual
		self.best_indiv = {'sw': None, 'sw_codes': None, 'fitness': 0.0, 'fitness_components': {}}


	'''
	Method to convert a vector of random keys into an ordered list of switches
	supposed to be closed. Ex: random_keys: [0.25, 0.15, 0.98]  ==> Sequence: 2 -> 1 -> 3
	'''
	def random_keys_to_edge(self, vector_random_keys, lisEXT):
		# copies list of
		aux_vector = []
		for i in range(len(vector_random_keys)):
			aux_vector.append(vector_random_keys[i])
			aux_vector.sort() # sort elements in ascending order

		for key in aux_vector:
			index = vector_random_keys.index(key)
			edge = self.list_closed_switches[index]
			lisEXT.append(edge)


	'''
	Debug method to print individuals
	'''
	def debug_print_individuals(self):
		# print("Individuals' chromosomes:")
		for i in range(len(self.list_ga_individuals)):
			indiv = self.list_ga_individuals[i]
			linha = ""
			for gene in indiv.switching_chromosome:
				linha += str(gene) + " "
			closing_switches = []
			self.random_keys_to_edge(indiv.switching_chromosome, closing_switches)
			# print("Indiv " + str(i) + ": " + linha + " " + str(closing_switches))


	''' 
	Main method to run SSGA algorithm. It determines the best switching sequence
	to obtain a given final graph from an initial graph.
	'''
	def run_ssga(self):
		# Determines opened switches and closed switches. This populates lists:
		#   - (1) self.list_closed_switches: list of switches that need to be closed
		#   - (2) self.list_opened_switches: list of switches that need to be opened
		#   - (3) self.list_cl_op_sw: list with (1) + (2)
		if not self.determine_necessary_switchings():
			return False

		# generates initial population of SSGA individuals
		self.initialize_individuals()

		# computes fitness function for each individual
		best_indiv = self.evaluate_individuals()

		# renew overall best individual
		if self.best_indiv['sw'] is None or best_indiv['fitness'] < self.best_indiv['fitness']:
			self.best_indiv['sw'] = best_indiv['sw'] ; self.best_indiv['fitness'] = best_indiv['fitness']
			self.best_indiv['fitness_components'] = best_indiv['fitness_components']
			self.best_indiv['sw_codes'] = best_indiv['sw_codes']

		# iterate over generations
		for i in range(self.num_generations):
			# print("   SSGA generation #" + str(i+1))
			self.mutation()
			self.crossover()		
			best_indiv = self.evaluate_individuals()

			# select best individuals
			self.ssga_selection()
			
			# renew overall best individual
			if self.best_indiv['sw'] is None or best_indiv['fitness'] < self.best_indiv['fitness']:
				self.best_indiv['sw'] = best_indiv['sw'] ; self.best_indiv['fitness'] = best_indiv['fitness']
				self.best_indiv['fitness_components'] = best_indiv['fitness_components']
				self.best_indiv['sw_codes'] = best_indiv['sw_codes']
				
			if self.converge():
			 	break

		return True


	''' 
	Method to pick generation's best SSGA individuals
	'''
	def ssga_selection(self):
		# sort list of individuals in terms of their fitness function
		self.list_ga_individuals.sort(reverse=False, key=self.f_indiv_fitness)

		# take N best individuals, where N = num_individuals
		while len(self.list_ga_individuals) > self.num_individuals:
			obj_delete = self.list_ga_individuals[len(self.list_ga_individuals) - 1]
			self.list_ga_individuals.remove(obj_delete)
			del obj_delete
		# if len(self.list_ga_individuals) > self.num_individuals:
		# 	n_delete = len(self.list_ga_individuals) - self.num_individuals
		# 	N_total = len(self.list_ga_individuals)
		# 	for i in range(n_delete):
		# 		indice = N_total - i - 1
		# 		obj_delete = self.list_ga_individuals[indice]
		# 		self.list_ga_individuals.remove(obj_delete)
		# 		del obj_delete


	''' 
	Auxiliar function to get fitness function of an SSGA individual
	'''
	def f_indiv_fitness(self, indiv):
		return indiv.fitness_function


	'''
	Method to generate initial population of SSGA individuals. Each individual has the following parameters:
	switching_chromosome, fitness_function, list_sw_changes
	'''
	def initialize_individuals(self):
		for i in range(self.num_individuals):
			indiv = IndivSS()
			self.list_ga_individuals.append(indiv)

			# It resorts of RANDOM KEYS strategy to encode switching sequence.
			# For each edge to be closed, a random number from [0,1] is appended to
			# list: "switching_chromosome"
			for j in range(len(self.list_closed_switches)):
				indiv.switching_chromosome.append(random.random())

			# Alternative way: chromosome of simple SSGA individual refers to both closing and
			# opening switching operations
			for j in range(len(self.list_cl_op_sw)):
				indiv.switching_chromosome_simple.append(random.random())


	'''
	Method to verify if GA individuals have achieved convergence by analyzing minimum and average values
	of fitness functions
	'''
	def converge(self):
		num_indiv = len(self.list_ga_individuals)
		if num_indiv == 0: return False
		average_evaluation = 0. ; min_evaluation = 0.
		for indiv in self.list_ga_individuals:
			average_evaluation += indiv.fitness_function # sum fitness funct. values
			if min_evaluation == 0. or indiv.fitness_function < min_evaluation: # updates minimum fitness function
				min_evaluation = indiv.fitness_function
		average_evaluation /= num_indiv

		# compute difference between minimum and average fitness function (percentage)
		if min_evaluation <= 0.: return False
		diff = 100. * abs(average_evaluation - min_evaluation) / min_evaluation
		return diff <= 3.0


	'''
	Method to interprete complete switching sequence, based on "SSGA simple technique"
	'''
	def complete_switching_sequence_simple_technique(self, ssga_indiv):
		random_keys: list = ssga_indiv.switching_chromosome_simple   # ex: [0.35, 0.10, 0.55, ...]
		sw_codes_dicts = list()

		tmp_list: list = random_keys.copy()
		tmp_list.sort() # ex: [0.10, 0.35, 0.55, ...]

		for value in tmp_list:
			index = random_keys.index(value)
			sw_code: list = list(self.list_cl_op_sw[index])
			sw_code.append(1)
			if index < len(self.list_closed_switches):
				sw_dict = {'sw_code': sw_code, 'action': 'cl'}
			else:
				sw_dict = {'sw_code': sw_code, 'action': 'op'}
			sw_codes_dicts.append(sw_dict)

		# Store list of switching operations. Sintax: [{'sw_code':[u,v,w], 'action':'op'}, ...]
		ssga_indiv.sw_codes_dicts = sw_codes_dicts
		return sw_codes_dicts

	'''
	Method to interprete complete switching sequence, based on "SSGA Disturbance Technique"
	'''
	def complete_switching_sequence_disturb_technique(self, ssga_indiv):
		list_pairs = []

		# if only 1 edge to be closed and 0 edges to be opened:
		if len(self.list_closed_switches) == 1 and len(self.list_opened_switches) == 0:
			edge_close = list(self.list_closed_switches[0]); edge_close.append(1) # format: [u,v,w=1]
			list_pairs.append([edge_close, []])

			# Store sequence of switching operations in individual's structure
			ssga_indiv.sw_seq = list_pairs
			return list_pairs, None

		random_keys = ssga_indiv.switching_chromosome
		list_edges_close = []  # list of edges to be closed
		list_edges_open = [] # list of edges to be opened
		self.random_keys_to_edge(random_keys, list_edges_close)

		# #debug
		# linha = ""
		# for edge_to_close in list_edges_close:
		# 	linha += str(edge_to_close) + " "
		# print("Edges to close: " + linha)

		graph_simulation = graphModule.Graph(self.graph.V) # new graph
		# inserts all possible edges
		for edge in self.graph.graph:
			graph_simulation.graph.append(edge)
		# inserts all initially closed edges
		for edge in self.initial_edges:
			u = edge[0] ; v = edge[1] ; w = edge[2]
			graph_simulation.edgesKRST.append([u, v, w])
		for edge_set in self.list_opened_switches:
			edge = list(edge_set); edge.append(1)
			list_edges_open.append(edge)

		# disturbance technique: for each closed switch, determines
		# switch to be opened to restore radiality

		# #debug
		# possible_edges = ""
		# initial_edges = ""
		# for edge in graph_simulation.graph:
		# 	possible_edges += str(edge) + " "
		# for edge in graph_simulation.edgesKRST:
		# 	initial_edges += str(edge) + " "
		# print("Vertices: " + str(graph_simulation.V) + " Possible: " + possible_edges + " Initial: " + initial_edges)

		# Randomly picks edges to be closed
		while len(list_edges_close) > 0:
			edge_index = random.randint(0, len(list_edges_close) - 1)
			edge_close_set = list_edges_close[edge_index] # format: {u,v} (set)
			edge_close = list(edge_close_set); edge_close.append(1) # format: [u,v,w=1]

			# if edge does not generate mesh, it is included into graph
			# and removed from list_edges_close
			if graph_simulation.creates_mesh(edge_close):
				graph_simulation.edgesKRST.append(edge_close)
				list_edges_close.remove(edge_close_set)  # removes from list "to be closed"
				# Opens a given edge to re-establish radiality. Format: [u, v, w]
				edge_open = graph_simulation.edge_to_open_mesh(list_edges_open)

				if edge_open is None:
					return None, "   *** PROBLEM: no edge to open"

				edge_open_1 = [edge_open[0], edge_open[1], 1]
				edge_open_2 = [edge_open[1], edge_open[0], 1]
				if edge_open_1 in list_edges_open:   edge_open = edge_open_1
				elif edge_open_2 in list_edges_open: edge_open = edge_open_2
				else:                                edge_open = None
				if edge_open is not None:
					list_edges_open.remove(edge_open)
					list_pairs.append([edge_close, edge_open])
				else:
					return None, (str(edge_open) + " not in " + str(list_edges_open))
			else:
				graph_simulation.edgesKRST.append(edge_close)
				list_edges_close.remove(edge_close_set)  # removes from list "to be closed"
				list_pairs.append([edge_close, []])
		# #debug
		# line = ""
		# for pair in list_pairs:
		# 	line += str(pair) + " "
		# print("Pairs: " + line)

		# for edge_closed_set in list_edges_close:
		# 	if graph_simulation.creates_mesh(edge_closed_set):
		# 		# determines edge to be opened to restore radiality
		# 		edge_open_set = graph_simulation.edge_to_open_mesh(self.list_opened_switches)
		# 		list_pairs.append([edge_closed_set, edge_open_set]) # pair: [sw_cl, sw_op]
		# 	else:
		# 		list_pairs.append([edge_closed_set, {}])  # pair: [sw_cl, sw_op]
      #
		# linha = ""
		# for edge_closed in list_edges_close:
		# 	linha += str(edge_closed) + " "
		# print("Edges to close: " + linha)

		# Store sequence of switching operations in individual's structure
		ssga_indiv.sw_seq = list_pairs

		return list_pairs, None


	'''
	Method to assign all necessary switching operations to SSGA individuals
	'''
	def assign_individuals_switching_operations(self):

		for ssga_indiv in self.list_ga_individuals:

			# 1 - Determine switchings (based on disturbance technique chromosome)
			# sw_seq has the sintax: [[[u_cl,v_cl,w_cl],[u_op,v_op,w_op], ...]
			sw_seq, str_details = self.complete_switching_sequence_disturb_technique(ssga_indiv)
			if sw_seq is None:
				return 1000.

			# 1 - Determine switchings (based on SSGA simple technique)
			# sw_codes_dicts has the sintax: [{'sw_code':[u,v,w], 'action':'op'}, ...]
			self.complete_switching_sequence_simple_technique(ssga_indiv)

			# 2 - Determine dictionaries with switch changes (based on disturbance technique)
			self.compute_switching_changes(ssga_indiv)

			# 2 - Determine dictionaries with switch changes (based on simple SSGA technique)
			self.compute_switching_changes_simple(ssga_indiv)



	'''
	Method to compute LF_MI (Load flow merit index), based solely on initial and final states.
	'''
	def compute_final_state_load_flow_merit_index(self):
		# # 1 - Pick one individual (the 1st one, for instante)
		# ssga_indiv = self.list_ga_individuals[0]
		#
		# # 2 - Determine switchings (based on disturbance technique chromosome)
		# # sw_seq has the sintax: [[[u_cl,v_cl,w_cl],[u_op,v_op,w_op], ...]
		# sw_seq, str_details = self.complete_switching_sequence_disturb_technique(ssga_indiv)
		# if sw_seq is None:
		# 	return 1000.
		#
		# # 2 - Determine switchings (based on SSGA simple technique)
		# # sw_codes_dicts has the sintax: [{'sw_code':[u,v,w], 'action':'op'}, ...]
		# sw_codes_dicts = self.complete_switching_sequence_simple_technique(ssga_indiv)
		#
		# # 3 - Determine dictionaries with switch changes (based on disturbance technique)
		# dicts_sw_changes = self.compute_switching_changes(ssga_indiv)
		#
		# # 3 - Determine dictionaries with switch changes (based on simple SSGA technique)
		# dicts_sw_changes_simple = self.compute_switching_changes_simple(ssga_indiv)

		# 1 - Pick one SSGA individual
		ssga_indiv = self.list_ga_individuals[0]
		dicts_sw_changes_simple = ssga_indiv.dicts_sw_changes_simple
		dicts_sw_changes = ssga_indiv.dicts_sw_changes

		# 2 - Determine initial states dictionary
		dict_sw_states = self.determine_sw_initial_states()

		if dicts_sw_changes is None or len(dicts_sw_changes) == 0:
			a = 0

		# 3 - Effectively assess LF_MI
		LF_MI = self.sw_assessment.load_flow_merit_index(dict_sw_states, dicts_sw_changes)
		return LF_MI


	'''
	Method to compute number of switching operations merit index (NS_MI). As a result, the
	following numbers are provided:
		- Number of total manual switching operations;
		- Number of total automatic switching operations;
	'''
	def compute_number_of_switchings_merit_index(self):
		# 1 - Pick one individual (the 1st one, for instante)
		ssga_indiv = self.list_ga_individuals[0]

		# 2 - Determine numbers of manual and automatic swtiching operations
		number_sw_manual = 0
		number_sw_auto = 0
		for change in ssga_indiv.dicts_sw_changes:
			sw_code = change['code']

			# Based on all switches register, search for switch's type.
			sw_register = self.networks_data.get_list_switches()
			for sw in sw_register:
				if sw['code_sw'] != sw_code: continue
				if sw['type_sw'] == 'disjuntor' or sw['type_sw'] == 'religadora':
					number_sw_auto += 1
				else:
					number_sw_manual += 1
				break

		# 3 - Compute NS_MI
		max_sw_operations = 30
		NS_MI = 1000.
		k_manual, k_auto = 1.0, 2.0  # penalty coefficients
		if number_sw_manual + number_sw_auto < max_sw_operations:
			NS_MI_manual = number_sw_manual / max_sw_operations
			NS_MI_auto = number_sw_auto / max_sw_operations
			NS_MI = k_manual * NS_MI_manual + k_auto * NS_MI_auto

		return NS_MI


	'''
	Method to compute fitness function of GA individuals. It is based on simulations
	aimed to reproduce the effects of the investigated switching steps
	'''
	def evaluate_individuals(self):
		best_indiv = {'sw': None, 'sw_codes': None, 'fitness': 0.0, 'fitness_components': {}}

		# Firstly, assign all necessary switching operations to individuals
		self.assign_individuals_switching_operations()

		# 1 - Compute load flow merit index, which depends solely on initial and final states.
		# Then, a unique load flow to assess final state loading is enough.
		LF_MI = self.compute_final_state_load_flow_merit_index()

		# 2 - Compute number of switching operations merit index
		NS_MI = self.compute_number_of_switchings_merit_index()

		for i in reversed(range(len(self.list_ga_individuals))):
			ssga_indiv = self.list_ga_individuals[i]

			# Individual's switching sequence
			# sw_seq = ssga_indiv.sw_seq
			sw_seq_dicts = ssga_indiv.sw_codes_dicts

			# In case of problems with sequencing, deletes individual
			if sw_seq_dicts is None:
				self.list_ga_individuals.remove(ssga_indiv)
				del ssga_indiv; continue

			# Determine the codes of switches that need to be closed/opened. Format: list of dictionaries.
			sw_changes = ssga_indiv.dicts_sw_changes
			# sw_changes_simple = ssga_indiv.dicts_sw_changes_simple

			# Store switch sequence in ssga individual.
			ssga_indiv.list_sw_changes.clear()
			for dict_sw_change in sw_changes:
				ssga_indiv.list_sw_changes.append(dict_sw_change)

			# # determine initial states of network's switches
			# dict_sw_states = self.determine_sw_initial_states()

			# 3 - Compute crew displacement
			CD_MI, list_displ_times = self.sw_assessment.crew_displacement_merit_index(self.start_switch, sw_changes)

			# 4 - Compute outage duration merit index (power interruption during switching procedure)
			all_available_edges, all_init_closed_edges = self.networks_data.all_edges()
			vertice_dicts = self.networks_data.list_vertices_dicts
			OD_MI = self.sw_assessment.outage_duration_merit_index(sw_changes, list_displ_times, all_available_edges, all_init_closed_edges, vertice_dicts)

			# compute individual total merit index
			ssga_indiv.fitness_function, fit_func_components = self.compute_total_merit_index(LF_MI, CD_MI, OD_MI, NS_MI)
			ssga_indiv.fitness_function_components.update({'LF_MI': round(fit_func_components[0], 5)})
			ssga_indiv.fitness_function_components.update({'CD_MI': round(fit_func_components[1], 5)})
			ssga_indiv.fitness_function_components.update({'OD_MI': round(fit_func_components[2], 5)})
			ssga_indiv.fitness_function_components.update({'NS_MI': round(fit_func_components[3], 5)})

			# update best individual
			if best_indiv['sw'] is None or best_indiv['fitness'] > ssga_indiv.fitness_function:
				best_indiv['sw'] = sw_seq_dicts; best_indiv['fitness'] = ssga_indiv.fitness_function
				best_indiv['fitness_components'] = ssga_indiv.fitness_function_components
				best_indiv['sw_codes'] = ssga_indiv.list_sw_changes


		#debug
		print("\n")
		print("     SSGA evaluation: ")
		self.list_ga_individuals.sort(reverse=False, key=self.f_indiv_fitness)
		sum_fitness = 0.0
		n_max = self.num_individuals
		for i in range(len(self.list_ga_individuals)):
			ssga_indiv = self.list_ga_individuals[i]
			if i < n_max:
				sum_fitness += ssga_indiv.fitness_function
				print("     #" + str(i + 1) + " - Fitness: " + str(round(ssga_indiv.fitness_function, 6)) + " - " + str(ssga_indiv.list_sw_changes))
			else:
				print("     #" + str(i+1) + " - Fitness: " + str(round(ssga_indiv.fitness_function, 6)))
		avg_fitness = sum_fitness / n_max
		diff = round(100. * (avg_fitness - self.list_ga_individuals[0].fitness_function) / self.list_ga_individuals[0].fitness_function, 5)
		texto  = "     MEDIA (melhores): " + str(round(avg_fitness, 4))
		texto += " - MINIMO: " + str(round(self.list_ga_individuals[0].fitness_function, 4))
		texto += " - DIFF(%): " + str(diff)
		print(texto)
		print("\n")

		return best_indiv


	'''
	Method to compute individual total merit index, which is calcalated
	based on different specific merit indexes. Parameters:
		LF_MI: load flow merit index
		CD_MI: crew displacement merit index
		OD_MI: outage duration merit index
		NS_MI: number of switching operations merit index
	'''
	def compute_total_merit_index(self, LF_MI, CD_MI, OD_MI, NS_MI):
		fit_func_components = []

		# specific weighting coefficients
		k_LF = float(self.merit_index_conf['k_load_flow'].replace(',','.'))
		k_CD = float(self.merit_index_conf['k_crew_displacement'].replace(',','.'))
		k_OD = float(self.merit_index_conf['k_outage_duration'].replace(',','.'))
		k_NS = float(self.merit_index_conf['k_number_switching'].replace(',','.'))

		# append fit_func components
		fit_func_components.append(k_LF * LF_MI)
		fit_func_components.append(k_CD * CD_MI)
		fit_func_components.append(k_OD * OD_MI)
		fit_func_components.append(k_NS * NS_MI)

		# composition of overall merit index value
		total_mi = k_LF * LF_MI + k_CD * CD_MI + k_OD * OD_MI + k_NS * NS_MI

		return total_mi, fit_func_components


	'''
	Method to determine initial states of network's switches
	'''
	def determine_sw_initial_states(self):
		all_switches = self.get_all_switches()
		closed_switches = [] ; opened_switches = []
		for edge_set in self.initial_graph_data["edges"]:
			sw = self.get_sw_code(list(edge_set))
			closed_switches.append(sw)
		for sw in all_switches:
			if sw not in closed_switches:
				opened_switches.append(sw)
		return {'closed_switches':closed_switches, 'opened_switches':opened_switches}


	'''
	Method to compute switching changes to be assessed
	'''
	def compute_switching_changes(self, ssga_indiv):
		dicts_sw_changes = []
		for pair in ssga_indiv.sw_seq:
			if len(pair[0]) > 0:
				edge_close = pair[0] ; sw_code = self.get_sw_code(edge_close)
				dicts_sw_changes.append({'code':sw_code, 'action':'cl'})
			if len(pair[1]) > 0:
				# print("pair[1]: " + str(type(pair[1])))
				edge_open = pair[1] ; sw_code = self.get_sw_code(edge_open)
				dicts_sw_changes.append({'code':sw_code, 'action':'op'})
		ssga_indiv.dicts_sw_changes = dicts_sw_changes
		return dicts_sw_changes


	'''
	Method to compute switching changes to be assessed, considering simple SSGA technique
	      'sw_codes_dicts' has dictionaries with format: {'sw_code':[u,v,w], 'action':'cl'/'op'}
	'''
	def compute_switching_changes_simple(self, ssga_indiv):
		dicts_sw_changes_simple = []
		for sw_code_dict in ssga_indiv.sw_codes_dicts:
			sw_code = self.get_sw_code(sw_code_dict['sw_code'])
			dicts_sw_changes_simple.append({'code': sw_code, 'action': sw_code_dict['action']})
		ssga_indiv.dicts_sw_changes_simple = dicts_sw_changes_simple
		return dicts_sw_changes_simple


	'''
	Method to get all switches of the current power network
	'''
	def get_all_switches(self):
		sw_codes = []
		list_edges = self.networks_data.get_list_edges()
		for edge_dict in list_edges:
			sw_codes.append(edge_dict['code_sw'])
		return sw_codes

	'''
	Get switch code corresponding to a given edge.
	The edge has the format: [u, v, w]
	'''
	def get_sw_code(self, edge):
		if edge is None: return ""

		# Gets edge's vertices 'u' and 'v'
		u = int(edge[0]) ; v = int(edge[1])

		# Searches for [u,v] in list of network's graph topology
		list_edges = self.networks_data.get_list_edges()
		for edge_dict in list_edges:
			if edge_dict['vertice_1'] == u and edge_dict['vertice_2'] == v:
				return edge_dict['code_sw']
			elif edge_dict['vertice_1'] == v and edge_dict['vertice_2'] == u:
				return edge_dict['code_sw']
		return ""



	'''
	Method to execute SSGA MUTATION operator
	'''
	def mutation(self):
		for indiv in self.list_ga_individuals:
			for i in range(len(indiv.switching_chromosome)):
				# randomly decides if the gene suffers mutation
				if random.random() < self.pm:
					indiv.switching_chromosome[i] = random.random()


	'''
	Method to execute SSGA CROSSOVER operator
	'''
	def crossover(self):
		indexes = list(range(len(self.list_ga_individuals)))
		indexes_pairs = list(itertools.combinations(indexes, 2)) # pairs of indexes
		for pair in indexes_pairs:
			if random.random() > self.pc:
				continue

			indiv1 = self.list_ga_individuals[pair[0]]
			indiv2 = self.list_ga_individuals[pair[1]]
			num_genes = len(indiv1.switching_chromosome)

			if num_genes == 1: # if one-gene-long chromosome, simply exchange
				gene_aux = indiv1.switching_chromosome[0]
				indiv1.switching_chromosome[0] = indiv2.switching_chromosome[0]
				indiv2.switching_chromosome[0] = gene_aux
			else:
				# randomly choose crossover initial position
				crossover_initial_index = random.randint(1, num_genes)
				# generate individual containing mixed characteristics
				child_indiv = self.crossover_child_indiv(indiv1, indiv2, crossover_initial_index)
				self.list_ga_individuals.append(child_indiv)

			a = 0
		b = 0

	'''
	Method to provide child indiv (of class IndivSS) resulting from crossover
	operation between indiv1 and indiv2. 
	crossover_initial_index: position index related to SSGA chromosome where crossover will take place
	'''
	def crossover_child_indiv(self, indiv1, indiv2, crossover_initial_index):
		new_indiv = IndivSS()
		for i in range(len(indiv1.switching_chromosome)):
			if i < crossover_initial_index:
				new_indiv.switching_chromosome.append(indiv1.switching_chromosome[i])
				new_indiv.switching_chromosome_simple.append(indiv1.switching_chromosome_simple[i])
			else:
				new_indiv.switching_chromosome.append(indiv2.switching_chromosome[i])
				new_indiv.switching_chromosome_simple.append(indiv2.switching_chromosome_simple[i])
		return new_indiv


	''' 
	Method to define all necessary switchings, in order to obtain final_graph from base_graph
	    - (1) self.list_closed_switches: list of switches that need to be closed
	    - (2) self.list_opened_switches: list of switches that need to be opened
	    - (3) self.list_cl_op_sw: (1)+(2)
	'''
	def determine_necessary_switchings(self):		
		# Get all initial graph vertices
		set_vertices_ini_graph = set([])
		for edge in self.initial_edges:
			set_vertices_ini_graph.add(edge[0]) ; set_vertices_ini_graph.add(edge[1])
			self.initial_graph_data["edges"].append({edge[0], edge[1]})	# appends edge as sets, to avoid duplicity
		self.initial_graph_data["vertices"] = list(set_vertices_ini_graph)

		# Get all final graph vertices
		set_vertices_final_graph = set([])
		for edge in self.graph.edgesKRST:
			set_vertices_final_graph.add(edge[0]) ; set_vertices_final_graph.add(edge[1])	
			self.final_graph_data["edges"].append({edge[0], edge[1]})		# appends edge as set to avoid duplicity	
		self.final_graph_data["vertices"] = list(set_vertices_final_graph)

		# Get closed and opened switches
		for edge in self.final_graph_data["edges"]:
			if edge not in self.initial_graph_data["edges"]:
				self.list_closed_switches.append(edge)
		for edge in self.initial_graph_data["edges"]:
			if edge not in self.final_graph_data["edges"]:
				self.list_opened_switches.append(edge)

		# Concatenate lists:
		self.list_cl_op_sw = self.list_closed_switches + self.list_opened_switches

		if len(self.list_closed_switches) == 0 and len(self.list_opened_switches) == 0:
			return False

		return True