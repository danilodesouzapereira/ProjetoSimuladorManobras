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
		self.fitness_function = 0.
		self.fitness_function_components = {}
		self.list_sw_changes = []

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
		self.list_closed_switches = []  # switches closed (initially opened ==> finally closed)
		self.list_opened_switches = []  # switches opened (initially closed ==> finally opened)
		self.list_ga_individuals = []  # list of GA individuals

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
		# Determines opened switches and closed switches. It populates lists:
		# self.list_closed_switches and self.list_opened_switches
		self.determine_necessary_switchings()

		# generates initial population of SSGA individuals
		self.initialize_individuals()

		# computes fitness function for each individual
		best_indiv = self.evaluate_individuals()

		# renew overall best individual
		if self.best_indiv['sw'] is None or best_indiv['fitness'] < self.best_indiv['fitness']:
			self.best_indiv['sw'] = best_indiv['sw'] ; self.best_indiv['fitness'] = best_indiv['fitness']
			self.best_indiv['fitness_components'] = best_indiv['fitness_components']
			self.best_indiv['sw_codes'] = best_indiv['sw_codes']

		# iterates over generations
		for i in range(self.num_generations):
			# print("   SSGA generation #" + str(i+1))
			self.mutation()
			self.crossover()		
			best_indiv = self.evaluate_individuals()
			
			# renew overall best individual
			if self.best_indiv['sw'] is None or best_indiv['fitness'] < self.best_indiv['fitness']:
				self.best_indiv['sw'] = best_indiv['sw'] ; self.best_indiv['fitness'] = best_indiv['fitness']
				self.best_indiv['fitness_components'] = best_indiv['fitness_components']
				self.best_indiv['sw_codes'] = best_indiv['sw_codes']
				
			if self.has_convergence():
				break


	'''
	Method to generate initial population of SSGA individuals. Each individual has the following parameters:
	switching_chromosome, fitness_function, list_sw_changes
	'''
	def initialize_individuals(self):
		for i in range(self.num_individuals):
			indiv = IndivSS() ; self.list_ga_individuals.append(indiv)

			# It resorts of RANDOM KEYS strategy to encode switching sequence.
			# For each edge to be closed, a random number from [0,1] is appended to
			# list: "switching_chromosome"
			for j in range(len(self.list_closed_switches)):
				indiv.switching_chromosome.append(round(random.random(), 4))


	'''
	Method to verify if GA individuals have achieved convergence by analyzing
	maximum and average values of fitness functions
	'''
	def has_convergence(self):
		num_indiv = len(self.list_ga_individuals)
		if num_indiv == 0: return False
		average_evaluation = 0. ; max_evaluation = 0.
		for indiv in self.list_ga_individuals:
			average_evaluation += indiv.fitness_function # sum fitness funct. values
			if indiv.fitness_function > max_evaluation: # updates maximum fitness function
				max_evaluation = indiv.fitness_function
		average_evaluation /= num_indiv

		# compute difference between maximum and average fitness function (percentage)
		if average_evaluation <= 0.: return False
		diff = 100. * abs(average_evaluation - max_evaluation) / average_evaluation
		return diff <= self.min_porc_fitness


	'''
	Method to interprete complete switching sequence
	'''
	def complete_switching_sequence(self, ssga_indiv):
		list_pairs = []

		# if only 1 edge to be closed and 0 edges to be opened:
		if len(self.list_closed_switches) == 1 and len(self.list_opened_switches) == 0:
			edge_close = list(self.list_closed_switches[0]); edge_close.append(1) # format: [u,v,w=1]
			list_pairs.append([edge_close, []])
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
		return list_pairs, None


	'''
	Method to compute LF_MI (Load flow merit index), based solely on initial and final states.
	'''
	def compute_final_state_load_flow_merit_index(self):
		# pick one individual (the 1st one, for instante)
		ssga_indiv = self.list_ga_individuals[0]

		# determine switchings
		sw_seq, str_details = self.complete_switching_sequence(ssga_indiv)
		if sw_seq is None:
			return 1000.

		sw_changes = self.compute_switching_changes(sw_seq)

		# determine initial states dictionary
		dict_sw_states = self.determine_sw_initial_states()

		# effectively assess LF_MI
		LF_MI = self.sw_assessment.load_flow_merit_index(dict_sw_states, sw_changes)
		return LF_MI


	'''
	Method to compute number of switching operations merit index (NS_MI). As results, the
	following numbers are provided:
		- Number of total manual switching operations;
		- Number of total automatic switching operations;
	'''
	def compute_number_of_switchings_merit_index(self):
		# pick one individual (the 1st one, for instante)
		ssga_indiv = self.list_ga_individuals[0]

		# determine switchings
		sw_seq, str_details = self.complete_switching_sequence(ssga_indiv)
		if sw_seq is None:
			return 1000.

		sw_changes = self.compute_switching_changes(sw_seq)

		# determine numbers of manual and automatic swtiching operations
		number_sw_manual = 0
		number_sw_auto = 0
		for change in sw_changes:
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

		# compute NS_MI
		max_sw_operations = 30
		NS_MI = 1000.
		k_manual, k_auto = 1.0, 1.0
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

		# Compute load flow merit index, which depends solely on initial and final states.
		# Then, a unique load flow to assess final state loading is enough.
		LF_MI = self.compute_final_state_load_flow_merit_index()

		# Compute number of switchings merit index
		NS_MI = self.compute_number_of_switchings_merit_index()

		for i in reversed(range(len(self.list_ga_individuals))):
			ssga_indiv = self.list_ga_individuals[i]

			# determines individual's switching sequence
			sw_seq, str_details = self.complete_switching_sequence(ssga_indiv)

			# in case of problems with sequencing, deletes individual
			if sw_seq is None:
				self.list_ga_individuals.remove(ssga_indiv)
				del ssga_indiv ; continue

			# Determines the codes of switches that need to be closed/opened. Format: list of dictionaries.
			sw_changes = self.compute_switching_changes(sw_seq)

			# Stores switch sequence in ssga individual.
			ssga_indiv.list_sw_changes.clear()
			for dict_sw_change in sw_changes:
				ssga_indiv.list_sw_changes.append(dict_sw_change)

			# # determine initial states of network's switches
			# dict_sw_states = self.determine_sw_initial_states()

			# compute crew displacement
			CD_MI, list_displ_times = self.sw_assessment.crew_displacement_merit_index(self.start_switch, sw_changes)

			# compute outage duration merit index (power interruption during switching procedure)
			all_available_edges, all_init_closed_edges = self.networks_data.all_edges()
			vertice_dicts = self.networks_data.list_vertices_dicts
			OD_MI = self.sw_assessment.outage_duration_merit_index(sw_changes, list_displ_times, all_available_edges, all_init_closed_edges, vertice_dicts)

			# computes individual total merit index
			ssga_indiv.fitness_function = self.compute_total_merit_index(LF_MI, CD_MI, OD_MI, NS_MI)
			ssga_indiv.fitness_function_components.update({'LF_MI': round(LF_MI, 5)})
			ssga_indiv.fitness_function_components.update({'CD_MI': round(CD_MI, 5)})
			ssga_indiv.fitness_function_components.update({'OD_MI': round(OD_MI, 5)})
			ssga_indiv.fitness_function_components.update({'NS_MI': round(NS_MI, 5)})

			# updates best individual
			if best_indiv['sw'] is None or best_indiv['fitness'] > ssga_indiv.fitness_function:
				best_indiv['sw'] = sw_seq ; best_indiv['fitness'] = ssga_indiv.fitness_function
				best_indiv['fitness_components'] = ssga_indiv.fitness_function_components
				best_indiv['sw_codes'] = ssga_indiv.list_sw_changes
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
		# specific weighting coefficients
		k_LF = float(self.merit_index_conf['k_load_flow'].replace(',','.'))
		k_CD = float(self.merit_index_conf['k_crew_displacement'].replace(',','.'))
		k_OD = float(self.merit_index_conf['k_outage_duration'].replace(',','.'))
		k_NS = float(self.merit_index_conf['k_number_switching'].replace(',','.'))

		# composition of overall merit index value
		total_mi = k_LF * LF_MI + k_CD * CD_MI + k_OD * OD_MI + k_NS * NS_MI

		return total_mi


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


	''' Method to compute switching changes to be assessed '''
	def compute_switching_changes(self, sw_seq):
		list_actions = []
		for pair in sw_seq:
			if len(pair[0]) > 0:
				edge_close = pair[0] ; sw_code = self.get_sw_code(edge_close)
				list_actions.append({'code':sw_code, 'action':'cl'})

			if len(pair[1]) > 0:
				# print("pair[1]: " + str(type(pair[1])))
				edge_open = pair[1] ; sw_code = self.get_sw_code(edge_open)
				list_actions.append({'code':sw_code, 'action':'op'})
		return list_actions


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
	Method to execute GA MUTATION operator
	'''
	def mutation(self):
		for indiv in self.list_ga_individuals:
			for i in range(len(indiv.switching_chromosome)):
				# randomly decides if the gene suffers mutation
				if random.random() < self.pm:
					indiv.switching_chromosome[i] = random.random()


	'''
	Method to execute GA CROSSOVER operator
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
				# randomly chooses crossover initial point
				crossover_initial_index = random.randint(1, num_genes)
				for i in range(len(indiv1.switching_chromosome)):
					if i < crossover_initial_index:
						continue
					gene = indiv1.switching_chromosome[0]
					indiv1.switching_chromosome[0] = indiv2.switching_chromosome[0]
					indiv2.switching_chromosome[0] = gene


	''' 
	Method to define all necessary switchings, in order to obtain final_graph from base_graph
	'''
	def determine_necessary_switchings(self):		
		# gets all initial graph vertices 
		set_vertices_ini_graph = set([])
		for edge in self.initial_edges:
			set_vertices_ini_graph.add(edge[0]) ; set_vertices_ini_graph.add(edge[1])
			self.initial_graph_data["edges"].append({edge[0], edge[1]})	# appends edge as sets, to avoid duplicity
		self.initial_graph_data["vertices"] = list(set_vertices_ini_graph)
		#debug
		# linha = "\nInitial graph - " + str(self.initial_graph_data["edges"])

		# gets all final graph vertices
		set_vertices_final_graph = set([])
		for edge in self.graph.edgesKRST:
			set_vertices_final_graph.add(edge[0]) ; set_vertices_final_graph.add(edge[1])	
			self.final_graph_data["edges"].append({edge[0], edge[1]})		# appends edge as set to avoid duplicity	
		self.final_graph_data["vertices"] = list(set_vertices_final_graph)
		#debug
		# linha += " Final graph - " + str(self.final_graph_data["edges"])
		# print(linha)
		
		# gets closed and opened switches
		for edge in self.final_graph_data["edges"]:
			if edge not in self.initial_graph_data["edges"]:
				self.list_closed_switches.append(edge)
		for edge in self.initial_graph_data["edges"]:
			if edge not in self.final_graph_data["edges"]:
				self.list_opened_switches.append(edge)
		#debug
		# linha = "Op: " + str(self.list_opened_switches)
		# linha += " Cl: " + str(self.list_closed_switches)
		# print("SWITCHINGS - " + linha)

		a = 0