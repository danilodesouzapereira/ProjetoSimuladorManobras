import graphGAModule
import switchingAssessmentModule


#===================================================================================#	
'''
Main class: SM (Simulador de Manobras)
'''
class SM(object):
	def __init__(self, dados_simulacao):
		self.dados_simulacao = dados_simulacao # contains data and settings
		dss_files_folder = self.dados_simulacao['local_dss'] # folder with DSS files

		# object to assess sequential switching through load flow simulations
		self.sm_folder = dss_files_folder + "\\..\\"
		self.sw_assessment = switchingAssessmentModule.AssessSSGAIndiv(dss_files_folder)

		# definitions of settings dictionaries
		self.graph_descr = {}
		self.settings_graph_GA = {}
		self.settings_switching_GA = {}


	''' DEBUG method '''
	def print_output(self):
		local_saida = self.dados_simulacao['local_saida'] + "\\ArquivoSaida.txt"
		f = open(local_saida, "w+")
		f.write('Este e o arquivo de saida do processo\n')
		f.write('Local do defeito: ' + str(self.dados_simulacao['vertice_falta']) + '\n')
		f.write('Numero de vertices: ' + str(self.dados_simulacao['num_vertices']) + '\n')
		arestas = self.dados_simulacao['arestas']
		f.write('\nDados das arestas:\n')
		for aresta in arestas:
			u = aresta['u']
			v = aresta['v']
			w = aresta['w']
			f.write('Vertice 1: ' + str(u) + ', Vertice 2: ' + str(v) + ', Peso: ' + str(w) + '\n')
		f.close()


	''' 
	Method to get definitions and settings.
	P.S.: can be taken from INI file 
	'''
	def definitions_and_settings(self):
		num_generations, num_individuals, pc, pm = 2, 5, 0.9, 0.1
		edges = [] ; initial_edges = []
		for aresta_json in self.dados_simulacao['arestas']:
			edges.append([aresta_json['u'], aresta_json['v'], aresta_json['w']])
		for aresta_inicial in self.dados_simulacao['arestas_iniciais']:
			initial_edges.append([aresta_inicial['u'], aresta_inicial['v'], aresta_inicial['w']])
		self.graph_descr = {'edges': edges, 'initial_edges': initial_edges}
		self.settings_graph_GA = {'num_generations': num_generations, 'num_individuals': num_individuals, 'pc': pc, 'pm': pm}
		self.settings_switching_GA = {'num_geracoes': 5, 'num_individuos': 5, 'pc': 0.9, 'pm': 0.1, 'min_porc_fitness': 5.0}


	'''  
	Main method - execution of Graph GA (1st stage)
	'''
	def run_simulator(self):
		# Initialize definitions and settings
		self.definitions_and_settings()

		# Initialize graph GA object
		gga = graphGAModule.GraphGA(self.sm_folder,
											 self.graph_descr,
											 self.settings_graph_GA,
											 self.settings_switching_GA,
											 self.sw_assessment)

		# Runs GA
		gga.run_gga()

		# Obtains results
		gga.get_results()
		
		
		
		
		
		
		
		
		
		
		
		
		
		