import graphModule
import itertools
import sequentialSwitchingGAModule
import numpy as np
import time


# ===================================================================================#
'''  
Class to represent Graph Genetic Algorithm (GGA) individual
'''


class Indiv:
	def __init__(self, graph, initial_edges):
		self.initial_edges = initial_edges
		self.graph = graph
		self.f_evaluation = 0.0
		self.f_evaluation_components = {}
		self.list_sw_changes = []
		self.list_sw_changes_codes = []  # Sintax: {'code':sw_code, 'action':'op'}), following cl(reconn), [cl,op], [cl,op], ...
		self.list_sw_inv_changes_codes = []  # Sintax: {'code':sw_code, 'action':'op'}), following cl(reconn), [cl,op], [cl,op], ...
		self.list_effective_sw_inv_changes_codes = []  # Sintax: {'code':sw_code, 'action':'op'}), following cl(reconn), [cl,op], [cl,op], ...


# ===================================================================================#

'''
Class to represent GA applied to graphs 
'''


class GraphGA:
	def __init__(self, sm_folder, settings_graph_ga, settings_switching_ga, sw_assessment, networks_data, merit_index_conf):
		self.sm_folder = sm_folder

		# Configurations concerning merit index calculation
		self.merit_index_conf = merit_index_conf

		# Data concerning the power networks investigated
		self.networks_data = networks_data

		# Object for switching sequencing assessment
		self.sw_assessment = sw_assessment

		# Graph GA parameter
		self.num_geracoes = settings_graph_ga.get('num_generations')
		self.num_individuals = settings_graph_ga.get('num_individuals')
		self.pc = settings_graph_ga.get('pc')
		self.pm = settings_graph_ga.get('pm')
		self.settings_switching_ga = settings_switching_ga

		# Get data concerning networks' graph
		self.lista_arestas = []   # list with all operable switches
		self.initial_edges = []   # list with normally closed switches
		dicts_edges = networks_data.list_graph_operable_switches_dicts
		for dict_edge in dicts_edges:
			self.lista_arestas.append([dict_edge['v1'], dict_edge['v2'], 1])
			if dict_edge['initial']:
				self.initial_edges.append([dict_edge['v1'], dict_edge['v2'], 1])
		
		# List of GA individuals. Each individuals contains:
		# Initial graph, final graph, fitness value
		self.list_ga_indiv = []
		
		# Reference to Graph-based GA best individual
		self.best_indiv: Indiv = None


	def print_fitness_function(self):
		tmp_list = list()
		avg_fitness = 0.0
		for indiv in self.list_ga_indiv:
			tmp_list.append(indiv)
			avg_fitness += indiv.f_evaluation
		avg_fitness /= len(self.list_ga_indiv)
		tmp_list.sort(key=self.f_eval_ga_obj)
		best_fitness_indiv: Indiv = tmp_list[0]
		print("Individuals' fitness functions:")
		for indiv in tmp_list:
			print("Fitness: " + str(round(indiv.f_evaluation, 5)) + " (" + str(indiv.f_evaluation_components) + ") " + str(indiv.list_effective_sw_inv_changes_codes))
		print("Average individual: " + str(round(avg_fitness, 6)) + " Best individual: " + str(round(best_fitness_indiv.f_evaluation)))


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
	Method to determine if GA iterations are necessary
	'''
	def ga_iterations_necessary(self):
		max_num_switching_operations = 0
		for i in reversed(range(len(self.list_ga_indiv))):
			indiv = self.list_ga_indiv[i]
			if len(indiv.list_sw_changes) > max_num_switching_operations:
				max_num_switching_operations = len(indiv.list_sw_changes)
		return max_num_switching_operations > 1


	''' 
	Main method, which effectively runs GGA
	'''
	def run_gga(self):

		print(" ============== 1st stage - Initial generation ===============")
		self.generate_individuals()  # Fill self.list_ga_indiv
		self.run_gga_optimal_switching()  # Evaluate each indiv and update self.best_indiv

		# Print fitness function
		self.print_fitness_function()

		# If all individuals contain only one switching operation, GA iterations are unnecessary
		if not self.ga_iterations_necessary():
			return

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

			# debug
			print("     EVALUATING GGA INDIV #" + str(i+1) + ":")

			# run SSGA (Sequential Switching Genetic Algorithm)
			ssga_is_run = ssga.run_ssga()
			if not ssga_is_run:
				self.list_ga_indiv.remove(indiv); del indiv; continue
						
			# store fitness function of Graph GA individual based on SSGA best individual fitness
			indiv.f_evaluation = ssga.best_indiv['fitness']
			indiv.list_sw_changes = ssga.best_indiv['sw']
			indiv.list_sw_changes_codes = ssga.best_indiv['sw_codes']
			indiv.list_sw_inv_changes_codes = ssga.best_indiv['sw_inv_codes']
			indiv.list_effective_sw_inv_changes_codes = ssga.best_indiv['effective_dicts_sw_inv_changes']
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
		eval_best_indiv = round(self.best_indiv.f_evaluation, 6)

		# list_sw_changes = self.best_indiv.list_sw_changes_codes
		list_sw_changes = self.best_indiv.list_effective_sw_inv_changes_codes

		dict_results = {'Fitness': eval_best_indiv, 'actions': list_sw_changes}
		return dict_results

		
	''' 
	Creation of GA initial individuals 
	'''
	def generate_individuals(self):
		# determine number of vertices
		list_of_vertices = []
		for edge in self.lista_arestas:  # list with all operable switches
			if edge[0] not in list_of_vertices: list_of_vertices.append(edge[0])
			if edge[1] not in list_of_vertices:	list_of_vertices.append(edge[1])
		number_of_vertices = len(list_of_vertices)

		for i in range(round(1.3 * self.num_individuals)):
			graph = graphModule.Graph(number_of_vertices)  # graph obj
			for edge in self.lista_arestas:                # inserts all possible edges
				graph.addEdge(edge[0], edge[1], edge[2])
			# graph.KruskalRST()
			bias_probability = 99  # integer value within [0,100]
			graph.KruskalRST_biased(self.initial_edges, bias_probability)   # generate initial radial graph in a biased way: initial edges are more likely to be picked
			indiv = Indiv(graph, self.initial_edges)
			self.list_ga_indiv.append(indiv)               # stores individual in list

			
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