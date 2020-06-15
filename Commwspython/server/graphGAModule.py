import graphModule
import itertools
import sequentialSwitchingGAModule
import numpy as np


#===================================================================================#
'''  
Class to represent Graph GA individual
'''
class Indiv:
	def __init__(self, graph, initial_edges):
		self.initial_edges = initial_edges
		self.graph = graph
		self.f_evaluation = 0.0
		self.f_evaluation_components = {}
		self.list_sw_changes = []
		self.list_sw_changes_codes = []

#===================================================================================#

'''
Class to represent GA applied to graphs 
'''
class GraphGA:
	def __init__(self, sm_folder, settings_graph_ga, settings_switching_ga, sw_assessment, networks_data, merit_index_conf):
		self.sm_folder = sm_folder

		# configurations concerning merit index calculation
		self.merit_index_conf = merit_index_conf

		# data concerning the power networks investigated
		self.networks_data = networks_data

		# object for switching sequencing assessment
		self.sw_assessment = sw_assessment

		# graph GA parameter
		self.num_geracoes = settings_graph_ga.get('num_generations')
		self.num_individuals = settings_graph_ga.get('num_individuals')
		self.pc = settings_graph_ga.get('pc')
		self.pm = settings_graph_ga.get('pm')
		self.settings_switching_ga = settings_switching_ga

		# Get data concerning networks' graph
		self.lista_arestas = []
		self.initial_edges = []
		dicts_edges = networks_data.list_graph_operable_switches_dicts
		for dict_edge in dicts_edges:
			self.lista_arestas.append([dict_edge['v1'], dict_edge['v2'], 1])
			if dict_edge['initial']:
				self.initial_edges.append([dict_edge['v1'], dict_edge['v2'], 1])
		
		# List of GA individuals. Each individuals contains:
		# Initial graph, final graph, fitness value
		self.list_ga_indiv = []
		
		# Reference to Graph-based GA best individual
		self.best_indiv : Indiv = None


	def print_fitness_function(self):
		# debug - get all fitness functions
		list_fitness = []
		list_fitness_components = []
		list_sw_operations = []
		for indiv in self.list_ga_indiv:
			f_aval = indiv.f_evaluation
			list_fitness.append(round(f_aval,6))
			list_fitness_components.append(indiv.f_evaluation_components)
			list_sw_operations.append(indiv.list_sw_changes_codes)

		list_fitness.sort()

		best_fitness = list_fitness[0]
		avg_fitness = np.average(list_fitness)

		print("Fitness functions:")
		for i in range(len(list_fitness)):
			fitness = list_fitness[i]
			fitness_comp = list_fitness_components[i]
			operations = list_sw_operations[i]

			print("fitness: " + str(round(fitness, 5)) + " (" + str(fitness_comp) + ") " + str(operations))
		print("Avg: " + str(round(avg_fitness, 6)) + " Best: " + str(round(best_fitness, 6)))

	'''
	Method to verify if GA individuals have achieved convergence by analyzing
	maximum and average values of fitness functions
	'''

	def converge(self):
		num_indiv = len(self.list_ga_indiv)
		if num_indiv == 0: return False
		average_evaluation = 0. ; min_evaluation = -1.
		for indiv in self.list_ga_indiv:
			average_evaluation += indiv.f_evaluation # sum fitness funct. values
			if min_evaluation == -1. or indiv.f_evaluation < min_evaluation: # updates maximum fitness function
				min_evaluation = indiv.f_evaluation
		average_evaluation /= num_indiv

		# computes difference between maximum and average fitness function (percentage)
		if average_evaluation <= 0.: return False
		diff = 100. * abs(average_evaluation - min_evaluation) / average_evaluation
		return diff <= 0.01


	''' 
	Main method, which effectively runs GA
	'''
	def run_gga(self):
		print(" ============== 1st stage - Initial generation ===============")
		self.generate_individuals()
		self.run_gga_optimal_switching()

		# Print fitness function
		self.print_fitness_function()
				
		# 1st stage GA generations
		for i in range(self.num_geracoes):
			print("=== GGA generation #" + str(i+1) + " ===")
			self.graph_mutation()
			self.graph_crossover()
			self.run_gga_optimal_switching()
			self.graph_selection()

			# Print fitness function
			self.print_fitness_function()

			if self.converge():
				break


	''' 
	Run GA 2nd stage, which consists of determining an
	optimal switching sequence for a given alternative
	'''
	def run_gga_optimal_switching(self):
		print("\n================ 2nd stage - SSGA =======================")
				
		# LIST OF GGA INDIVIDUALS:
		for i in reversed(range(len(self.list_ga_indiv))):
		
			# print("\nIndividuo GGA: " + str(i+1) + " de " + str(len(self.list_ga_indiv)))
		
			# print("\n=== SSGA for G_ini => G_" + str(i+1) + " ====")			
			indiv = self.list_ga_indiv[i]
						
			# print("   Final graph: " + str(indiv.graph.edgesKRST) + "\n")
			ssga = sequentialSwitchingGAModule.SSGA(indiv.graph,
																indiv.initial_edges,
																self.settings_switching_ga,
																self.sw_assessment,
																self.networks_data,
																self.merit_index_conf)

			#debug
			print("     EVALUATING GGA INDIV #" + str(i+1) + ":")

			# run SSGA (Sequential Switching Genetic Algorithm)
			ssga_is_run = ssga.run_ssga()
			if not ssga_is_run:
				self.list_ga_indiv.remove(indiv); del indiv; continue
						
			# store fitness function of Graph GA individual based on SSGA best individual fitness
			indiv.f_evaluation = ssga.best_indiv['fitness']
			indiv.list_sw_changes = ssga.best_indiv['sw']
			indiv.list_sw_changes_codes = ssga.best_indiv['sw_codes']
			indiv.f_evaluation_components = ssga.best_indiv['fitness_components']
									
			# renew Graphic GA best individual
			if self.best_indiv is None or indiv.f_evaluation < self.best_indiv.f_evaluation:
				self.best_indiv = indiv


	
	''' 
	Auxiliar function to get an individual's fitness function
	'''
	def f_eval_ga_obj(self, indiv):
		return indiv.f_evaluation


	'''  
	Method to determine edges connected to a given vertice
	'''
	def edges_to_vertice(self, faulty_vertice):
		edges_to_remove = []
		for edge in self.lista_arestas:
			if edge[0] == faulty_vertice or edge[1] == faulty_vertice:
				edges_to_remove.append({edge[0], edge[1]})
		return edges_to_remove


	''' 
	Method to pick generation's best individuals
	'''
	def graph_selection(self):
		# print("\nSelection")

		# sort list of individuals in terms of their fitness
		self.list_ga_indiv.sort(reverse=False, key = self.f_eval_ga_obj)

		# take N best individuals, where N = num_individuals
		if len(self.list_ga_indiv)  > self.num_individuals:
			n_delete = len(self.list_ga_indiv) - self.num_individuals
			N_total = len(self.list_ga_indiv)
			for i in range(n_delete):
				indice = N_total - i - 1
				obj_delete = self.list_ga_indiv[indice]
				self.list_ga_indiv.remove(obj_delete)
				del obj_delete
		# # debug
		# linha = ""
		# for indiv in self.list_ga_indiv:
		# 	graph = indiv.graph
		# 	linha = linha + " " + str(indiv.f_evaluation)
		# print("Avaliacoes dos individuos: " + linha)
		
		
	''' 
	Method to extract results
	'''
	def get_results(self):
		eval_best_indiv = round(self.best_indiv.f_evaluation,6)
		list_sw_changes = self.best_indiv.list_sw_changes_codes
		dict_results = {'Fitness':eval_best_indiv, 'actions':list_sw_changes}
		return dict_results

		
	''' 
	Creation of GA initial individuals 
	'''
	def generate_individuals(self):
		# determine number of vertices
		list_of_vertices = []
		for edge in self.lista_arestas:
			if edge[0] not in list_of_vertices: list_of_vertices.append(edge[0])
			if edge[1] not in list_of_vertices:	list_of_vertices.append(edge[1])
		number_of_vertices = len(list_of_vertices)

		for i in range(round(1.3 * self.num_individuals)):
			graph = graphModule.Graph(number_of_vertices) # graph obj
			for edge in self.lista_arestas:               # inserts all possible edges
				graph.addEdge(edge[0], edge[1], edge[2])
			graph.KruskalRST()                            # generate initial radial graph
			indiv = Indiv(graph, self.initial_edges)
			self.list_ga_indiv.append(indiv)              # stores individual in list

			
	''' 
	MUTATION operator for graphs
	'''
	def graph_mutation(self):
		# print("\nMutation: ")
		for indiv in self.list_ga_indiv:
			graph = indiv.graph
			# print("Graph before mutation: ") ; graph.print_graph()
			graph.mutation()
			# print("Graph after mutation: ") ; graph.print_graph()
		# # debug
		# linha = ""
		# for indiv in self.list_ga_indiv:
		# 	graph = indiv.graph
		# 	linha = linha + " " + str(indiv.f_evaluation)
		# print("Avaliacoes dos individuos: " + linha)
	
	
	''' 
	UNION operator for graphs 
	'''
	def unite_graphs(self, lista_edges1, lista_edges2):
		final_edges = []
		for edge in lista_edges1:
			final_edges.append(edge)
		for edge in lista_edges2:
			if edge not in final_edges:
				final_edges.append(edge)
		return final_edges
	
	
	'''
	CROSSOVER OPERATOR for graphs
	'''
	def graph_crossover(self):
		# Generates pairs of indexes
		indexes = list(range(len(self.list_ga_indiv)))
		indexes_combinations = itertools.combinations(indexes, 2)
		for i_comb in indexes_combinations:
			indiv1 = self.list_ga_indiv[i_comb[0]] ; graph1 = indiv1.graph
			indiv2 = self.list_ga_indiv[i_comb[1]] ; graph2 = indiv2.graph
			#print("Graphs before crossover: ")
			#print("Graph 1:") ; graph1.print_graph()
			#print("Graph 2:") ; graph2.print_graph()			
			
			# Generates offspring graph
			nVertices = graph1.V
			lista_arestas = self.unite_graphs(graph1.edgesKRST, graph2.edgesKRST)
			new_graph = graphModule.Graph(nVertices)
			for edge in lista_arestas:
				new_graph.addEdge(edge[0], edge[1], edge[2])
			new_graph.KruskalRST() 		
			#print ("Final graph:") ; new_graph.print_graph()
			
			# Appends new graph individual into list of individuals
			indiv = Indiv(new_graph, self.initial_edges)
			self.list_ga_indiv.append(indiv)
		# # debug
		# for indiv in self.list_ga_indiv:
		# 	print(indiv.graph.edgesKRST)