import dss  # OpenDSS connection for power flow simulations


''' 
Class to represent optimal switching Genetic Algorithm Individuals
'''
class IndivSS:
	def __init__(self, SSGA_settings):
		# self.base_graph = base_graph
		# self.final_graph = final_graph
		# self.SSGA_settings = SSGA_settings
		# self.switching_chromosome = []
		pass



''' 
Main class, responsible for determining the SSGA (SEQUENTIAL SWITCHING GENETIC ALGORITHM) 
'''
class SSGA:
	def __init__(self, graph, initial_edges):
		self.graph = graph
		self.initial_edges = initial_edges
		self.initial_graph_data = {"vertices":[], "edges":[]}
		self.final_graph_data = {"vertices":[], "edges":[]}
		self.list_closed_switches = []  # switches closed (initially opened ==> finally closed)
		self.list_opened_switches = []  # switches opened (initially closed ==> finally opened)

		
	''' 
	Main method to run SSGA algorithm
	'''
	def run_ssga(self):
		self.determine_necessary_switchings()
		print("Abertas: " + str(self.list_opened_switches))
		print("Fechadas: " + str(self.list_closed_switches))
		
		
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
		
		
