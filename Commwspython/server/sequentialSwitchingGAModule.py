import dss  # OpenDSS connection for power flow simulations
import random
import itertools
import graphModule


''' 
Class to represent optimal switching Genetic Algorithm Individuals
'''
class IndivSS:
	def __init__(self):
		# self.base_graph = base_graph
		# self.final_graph = final_graph
		# self.SSGA_settings = SSGA_settings
		self.switching_chromosome = []
		self.fitness_function = 0.
		pass


''' 
Main class, responsible for determining the SSGA (SEQUENTIAL SWITCHING GENETIC ALGORITHM) 
'''
class SSGA:
	def __init__(self, graph, initial_edges, SSGA_settings):
		self.graph = graph
		self.initial_edges = initial_edges
		self.initial_graph_data = {"vertices":[], "edges":[]}
		self.final_graph_data = {"vertices":[], "edges":[]}
		self.list_closed_switches = []  # switches closed (initially opened ==> finally closed)
		self.list_opened_switches = []  # switches opened (initially closed ==> finally opened)
		self.list_ga_individuals = []  # list of GA individuals

		# Genetic algorithm settings
		self.SSGA_settings = SSGA_settings
		self.num_generations = SSGA_settings.get('num_geracoes')
		self.num_individuals = SSGA_settings.get('num_individuos')
		self.pc = SSGA_settings.get('pc')
		self.pm = SSGA_settings.get('pm')
		self.min_porc_fitness = SSGA_settings.get('min_porc_fitness')


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
		print("Individuals' chromosomes:")
		for i in range(len(self.list_ga_individuals)):
			indiv = self.list_ga_individuals[i]
			linha = ""
			for gene in indiv.switching_chromosome:
				linha += str(gene) + " "
			closing_switches = []
			self.random_keys_to_edge(indiv.switching_chromosome, closing_switches)
			print("Indiv " + str(i) + ": " + linha + " " + str(closing_switches))


	''' 
	Main method to run SSGA algorithm
	'''
	def run_ssga(self):
		# determine opened switches and closed switches
		self.determine_necessary_switchings()

		# generate initial individuals, along with their GA chromosome
		self.initialize_individuals()

		# computes fitness function for each individual
		self.evaluate_individuals()

		# iterates over generations
		for i in range(self.num_generations):
			self.mutation()
			self.crossover()
			self.evaluate_individuals()
			if self.has_convergence():
				break


	'''
	Method to generate initial individuals
	'''
	def initialize_individuals(self):
		print("num_individuals: " + str(self.num_individuals))
		for i in range(self.num_individuals):
			indiv = IndivSS()
			self.list_ga_individuals.append(indiv)
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

		# computes difference between maximum and average fitness function (percentage)
		if average_evaluation <= 0.: return False
		diff = 100. * abs(average_evaluation - max_evaluation) / average_evaluation
		return diff <= self.min_porc_fitness


	'''
	Method to interprete complete switching sequence
	'''
	def complete_switching_sequence(self, ssga_indiv):
		random_keys = ssga_indiv.switching_chromosome
		list_edges_close = []  # list of edges to be closed
		list_edges_open = [] # list of edges to be opened
		self.random_keys_to_edge(random_keys, list_edges_close)
		list_pairs = []

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
				# Opens a given edge to re-establish radiality. Format: {u,v}.
				edge_open = graph_simulation.edge_to_open_mesh(list_edges_open)
				list_edges_open.remove(edge_open)
				list_pairs.append([edge_close, edge_open])
			else:
				graph_simulation.edgesKRST.append(edge_close)
				list_edges_close.remove(edge_close_set)  # removes from list "to be closed"
				list_pairs.append([edge_close, []])

		#debug
		line = ""
		for pair in list_pairs:
			line += str(pair) + " "
		print("Pairs: " + line)


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


	'''
	Method to compute fitness function of GA individuals
	'''
	def evaluate_individuals(self):
		for ssga_indiv in self.list_ga_individuals:
			# determines individual's switching sequence
			self.complete_switching_sequence(ssga_indiv)


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
			self.initial_graph_data["edges"].append({edge[0], edge[1]})	# appends edge as set to avoid duplicity
		self.initial_graph_data["vertices"] = list(set_vertices_ini_graph)					
		print("\n\nGrafo inicial:")
		print(self.initial_graph_data)
			
		# gets all final graph vertices
		set_vertices_final_graph = set([])
		for edge in self.graph.edgesKRST:
			set_vertices_final_graph.add(edge[0]) ; set_vertices_final_graph.add(edge[1])	
			self.final_graph_data["edges"].append({edge[0], edge[1]})		# appends edge as set to avoid duplicity	
		self.final_graph_data["vertices"] = list(set_vertices_final_graph)
		print("Grafo final:")
		print(self.final_graph_data)
		
		# gets closed and opened switches
		for edge in self.final_graph_data["edges"]:
			if edge not in self.initial_graph_data["edges"]:
				self.list_closed_switches.append(edge)
		for edge in self.initial_graph_data["edges"]:
			if edge not in self.final_graph_data["edges"]:
				self.list_opened_switches.append(edge)

		#debug
		print("Abertas: " + str(self.list_opened_switches))
		print("Fechadas: " + str(self.list_closed_switches))