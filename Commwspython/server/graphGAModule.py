import graphModule
import itertools


''' Classe para representar um indivíduo de AG '''
class Indiv:
	def __init__(self, graph):
		self.graph = graph
		self.f_evaluation = 100.0


''' Classe para representar AG aplicado a grafos '''
class GraphGA: 
	def __init__(self, descricao_grafo, descricao_ag): 
		# Parâmetros do AG
		self.num_geracoes = descricao_ag.get('num_geracoes')
		self.num_individuals = descricao_ag.get('num_individuos')
		self.pc = descricao_ag.get('pc')
		self.pm = descricao_ag.get('pm')
		self.num_vertices = descricao_grafo.get('num_vertices')
		self.lista_arestas = descricao_grafo.get('arestas')
		
		# Grafo inicial
		self.graph_initial = graphModule.Graph(self.num_vertices)	
		for edge in self.lista_arestas:
			self.graph_initial.addEdge(edge[0], edge[1], edge[2])
		self.graph_initial.KruskalRST() 
		
		# Lista de indivíduos de AG (cada indivíduo contem um grafo e sua avaliação)
		self.list_ga_indiv = []
		
		
	''' Método principal, que efetivamente executa o AG '''
	def run_gga(self):
		print("\n\n\n==========Execucao efetiva do AG============")
		print("\n\n-------Geracao de individuos iniciais-------")
		
		# Indivíduos iniciais do AG do 1o estágio
		self.generate_individuals()
		self.run_gga_optimal_switching() # executa o AG do 2o estágio
		
		# Executa gerações do AG do 1o estágio:
		for i in range(self.num_geracoes):						
			self.graph_mutation() # executa operação de mutação			
			self.graph_crossover() # executa operação de cruzamento		
			self.run_gga_optimal_switching() # executa o AG do 2o estágio
			self.graph_selection() # executa seleção dos melhores indivíduos
			print("\n\n-------Nova geracao-------")
			
			
		# debug
		for indiv in self.list_ga_indiv:
			graph = indiv.graph
			graph.plot_graph()
			
		
	''' 
		Executa o AG do 2o estágio, que consiste em:
		DETERMINAR O CHAVEAMENTO ÓTIMO PARA 
        CADA ALTERNATIVA FINAL DE CONFIGURAÇÃO	
	'''
	def run_gga_optimal_switching(self):
		print("\nOptimal switching algorithm")
		# Insere avaliação para cada indivíduo de AG
		for indiv in self.list_ga_indiv:
			graph = indiv.graph
			for edge in graph.edgesKRST:
				u = edge[0] ; v = edge[1]
				if (u == 2 and v == 5) or (u == 5 and v == 2):
					indiv.f_evaluation = indiv.f_evaluation - 20.	
				if (u == 2 and v == 7) or (u == 7 and v == 2):
					indiv.f_evaluation = indiv.f_evaluation - 20.					
				if (u == 3 and v == 5) or (u == 5 and v == 3):
					indiv.f_evaluation = indiv.f_evaluation - 8.
				if (u == 3 and v == 7) or (u == 7 and v == 3):
					indiv.f_evaluation = indiv.f_evaluation - 8.
				if (u == 6 and v == 7) or (u == 7 and v == 6):
					indiv.f_evaluation = indiv.f_evaluation - 4.
				if (u == 4 and v == 5) or (u == 5 and v == 4):
					indiv.f_evaluation = indiv.f_evaluation - 3.	
				if (u == 2 and v == 3) or (u == 3 and v == 2):
					indiv.f_evaluation = indiv.f_evaluation - 2.						
				if (u == 1 and v == 2) or (u == 2 and v == 1):
					indiv.f_evaluation = indiv.f_evaluation - 1.
					
		# debug
		linha = ""
		for indiv in self.list_ga_indiv:
			graph = indiv.graph
			linha = linha + " " + str(indiv.f_evaluation)
		print("Avaliacoes dos individuos: " + linha)
					
	
	''' Função auxiliar para retornar a função de avaliação de um indivíduo'''	
	def f_eval_ga_obj(self, indiv):
		return indiv.f_evaluation
					
					
	''' 
		Método de seleção dos melhores indivíduos da geração
	'''
	def graph_selection(self):
		print("\nSelection")	
		
		# ordena a lista de indivíduos em termos de sua função de avaliação
		self.list_ga_indiv.sort(reverse=True, key = self.f_eval_ga_obj)
		
		# pega os N melhores indivíduos, em que N = num_individuals
		if len(self.list_ga_indiv)  > self.num_individuals:
			n_apagar = len(self.list_ga_indiv) - self.num_individuals
			N_total = len(self.list_ga_indiv)
			for i in range(n_apagar):
				indice = N_total - i - 1
				obj_apagar = self.list_ga_indiv[indice]
				self.list_ga_indiv.remove(obj_apagar)
				del obj_apagar
				
		# debug
		linha = ""
		for indiv in self.list_ga_indiv:
			graph = indiv.graph
			linha = linha + " " + str(indiv.f_evaluation)
		print("Avaliacoes dos individuos: " + linha)
		
		
		
	''' Método para extração dos resultados '''
	def get_results(self):
		print("Extracao dos resultados")
		
		
	''' Criação de indivíduos iniciais do AG '''
	def generate_individuals(self):
		# Gera indivíduos iniciais
		for i in range(self.num_individuals):
			graph = graphModule.Graph(self.num_vertices)  # obj de grafo		
			for edge in self.lista_arestas:               # insere arestas
				graph.addEdge(edge[0], edge[1], edge[2])
			graph.KruskalRST()                            # gera grafo radial				
			indiv = Indiv(graph)			
			self.list_ga_indiv.append(indiv)              # guarda indivíduo em lista
			
		# debug
		linha = ""
		for ind in self.list_ga_indiv:
			linha = linha + " " + str(ind.f_evaluation)
		print("\nGeracao de individuos")
		print("Avaliacoes dos individuos iniciais: " + linha)
			
			
	''' Operador MUTAÇÃO '''
	def graph_mutation(self):
		print("\Mutation: ")
		for indiv in self.list_ga_indiv:
			graph = indiv.graph
			#print("Graph before mutation: ") ; graph.print_graph()
			graph.mutation()
			#print("Graph after mutation: ") ; graph.print_graph()
			
		# debug
		linha = ""
		for indiv in self.list_ga_indiv:
			graph = indiv.graph
			linha = linha + " " + str(indiv.f_evaluation)
		print("Avaliacoes dos individuos: " + linha)
	
	
	''' Operador UNIÃO '''
	def unite_graphs(self, lista_arestas1, lista_arestas2):
		final_edges = []
		for edge in lista_arestas1:
			final_edges.append(edge)
		for edge in lista_arestas2:
			if edge not in final_edges:
				final_edges.append(edge)
		return final_edges
	
	
	''' Operador CRUZAMENTO '''
	def graph_crossover(self):
		print("\nCrossover: ")
		
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
			indiv = Indiv(new_graph)
			self.list_ga_indiv.append(indiv)
			
		# debug
		linha = ""
		for indiv in self.list_ga_indiv:
			graph = indiv.graph
			linha = linha + " " + str(indiv.f_evaluation)
		print("Avaliacoes dos individuos: " + linha)