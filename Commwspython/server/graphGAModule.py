import graphModule
import itertools
import sequentialSwitchingGAModule


'''  
Class to represent Graph GA individual
'''
class Indiv:
	def __init__(self, graph, initial_edges):
		self.initial_edges = initial_edges
		self.graph = graph
		self.f_evaluation = 100.0

#===================================================================================#

'''
Class to represent GA applied to graphs 
'''
class GraphGA: 
	def __init__(self, graph_descr, settings_graph_ga, settings_switching_ga):
		# Parâmetros do AG
		self.num_geracoes = settings_graph_ga.get('num_generations')
		self.num_individuals = settings_graph_ga.get('num_individuals')
		self.pc = settings_graph_ga.get('pc')
		self.pm = settings_graph_ga.get('pm')
		self.lista_arestas = graph_descr.get('edges')
		self.initial_edges = graph_descr.get('initial_edges')
		self.settings_switching_ga = settings_switching_ga

		# List of GA individuals. Each individuals contains:
		# Initial graph, final graph, fitness value
		self.list_ga_indiv = []

		
	''' 
	Main method, which effectively runs GA
	'''
	def run_gga(self):
		print(" ============== 1st stage - Initial generation ===============")
		self.generate_individuals()
		self.run_gga_optimal_switching()
		
		# 1st stage GA generations
		for i in range(self.num_geracoes):
			print("=== GGA generation #" + str(i+1) + " ===")
			self.graph_mutation()
			self.graph_crossover()
			self.run_gga_optimal_switching()
			self.graph_selection()
		# debug
		# for indiv in self.list_ga_indiv:
			# graph = indiv.graph
			# graph.plot_graph()
			
		
	''' 
   Runs GA 2nd stage, which consists of determining an
   optimal switching sequence for a given alternative
	'''
	def run_gga_optimal_switching(self):
		print("\n================ 2nd stage - SSGA =======================")
		
		# runs Seq. Switching GA for each individual
		for i in range(len(self.list_ga_indiv)):
			print("\n=== SSGA for G_ini => G_" + str(i+1) + " ====")
			indiv = self.list_ga_indiv[i]
			# print("   Final graph: " + str(indiv.graph.edgesKRST) + "\n")
			ssga = sequentialSwitchingGAModule.SSGA(indiv.graph,
																 indiv.initial_edges,
																 self.settings_switching_ga)
			ssga.run_ssga()

		# Debug: inserts individuals' GA assessment (fitness)
		for indiv in self.list_ga_indiv:
			graph = indiv.graph
			for edge in graph.edgesKRST:
				edge_set = {edge[0], edge[1]}
				if edge_set == {0, 3} or edge_set == {0, 5}:
					indiv.f_evaluation -= 1.
				elif edge_set == {3, 4} or edge_set == {5, 6}:
					indiv.f_evaluation -= 2.
				elif edge_set == {1, 2}:
					indiv.f_evaluation -= 4.
				elif edge_set == {1, 4} or edge_set == {1, 6}:
					indiv.f_evaluation -= 8.
				elif edge_set == {2, 4} or edge_set == {2, 6}:
					indiv.f_evaluation -= 15.
		# debug
		# linha = ""
		# for indiv in self.list_ga_indiv:
			# graph = indiv.graph
			# linha = linha + " " + str(indiv.f_evaluation)
		# print("Avaliacoes dos individuos: " + linha)
					
	
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
		self.list_ga_indiv.sort(reverse=True, key = self.f_eval_ga_obj)

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
		# print("Extracao dos resultados")
		pass
		
		
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

		for i in range(self.num_individuals):
			graph = graphModule.Graph(number_of_vertices) # graph obj
			for edge in self.lista_arestas:               # inserts all possible edges
				graph.addEdge(edge[0], edge[1], edge[2])
			graph.KruskalRST()                            # generate initial radial graph
			indiv = Indiv(graph, self.initial_edges)
			self.list_ga_indiv.append(indiv)              # stores individual in list
		# #debug
		# for indiv in self.list_ga_indiv:
		# 	print(indiv.graph.edgesKRST)

			
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