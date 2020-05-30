import graphGAModule
import switchingAssessmentModule
import requests
import networksData

# ===================================================================================#
'''
Main class: SM (Simulador de Manobras)
'''


class SM(object):
	def __init__(self, dados_simulacao):

		# get data provided through the Web Service call
		self.dados_simulacao = dados_simulacao  # contains data and settings
		dss_files_folder = self.dados_simulacao['local_dss']  # folder with DSS files
		self.sm_folder = dss_files_folder + "\\..\\"

		self.settings_graph_GA = self.get_GGA_settings()      # settings of Graph Genetic Algorithm
		self.settings_switching_GA = self.get_SSGA_settings() # settings of Seq. Switching Genetic Algorithm

		# get configurations concerning merit index calculation
		self.merit_index_conf = self.dados_simulacao['av_conf_indice_merito']

		# object with all networks' data
		self.networks_data = networksData.NetworksData(self.sm_folder)
		self.networks_data.initialize()

		# results
		self.dict_results: dict = None

		# object to assess sequential switching through load flow simulations
		self.sw_assessment = switchingAssessmentModule.AssessSSGAIndiv(dss_files_folder, self.networks_data)


	'''
	Method to update dictionary with GGA settings
	'''
	def get_GGA_settings(self):
		settings_graph_GA = {}
		dict_conf = self.dados_simulacao['conf_ag_grafo']
		settings_graph_GA.update({'num_generations':dict_conf['num_geracoes']})
		settings_graph_GA.update({'num_individuals': dict_conf['num_individuos']})
		settings_graph_GA.update({'pc': dict_conf['pc']})
		settings_graph_GA.update({'pm': dict_conf['pm']})
		return settings_graph_GA


	'''
	Method to update dictionary with SSGA settings
	'''
	def get_SSGA_settings(self):
		settings_graph_GA = {}
		dict_conf = self.dados_simulacao['conf_ag_chv_otimo']
		settings_graph_GA.update({'num_generations':dict_conf['num_geracoes']})
		settings_graph_GA.update({'num_individuals': dict_conf['num_individuos']})
		settings_graph_GA.update({'pc': dict_conf['pc']})
		settings_graph_GA.update({'pm': dict_conf['pm']})
		settings_graph_GA.update({'min_porc_fitness': dict_conf['min_porc_fitness']})
		settings_graph_GA.update({'start_switch': self.dados_simulacao['chave_partida']})
		return settings_graph_GA


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
	

	def return_response(self):
		#list_actions = [] ; acao : str
		#for dict_action in self.dict_results['actions']:
		#	sw_code = dict_action['code'] ; action = dict_action['action']
		#	if action == 'cl': acao = 'fechar'
		#	else: acao = 'abrir'
		#	list_actions.append({'chave':sw_code, 'acao':acao})
		#return_data = {'chaveamentos':list_actions}
		#
		#print("Fitness: " + str(self.dict_results['Fitness']))
		#
		#r = requests.post('http://127.0.0.1:5011/retornosimulacao', json=return_data)
		
		
		#DEBUG - TESTE DO RETORNO
		return_data = {'par1':'valor_par1', 'par2':'valor_par2'}
		r = requests.post('http://127.0.0.1:8082/SaidaSM', json=return_data)		


	# '''
	# Method to get definitions and settings.
	# P.S.: can be taken from INI file
	# '''
	# def definitions_and_settings(self):
	# 	# settings related to Graph Genetic Algorithm (GGA)
	# 	self.settings_graph_GA = {'num_generations': 20, 'num_individuals': 20, 'pc': 0.90, 'pm': 0.2}
	#
	# 	# settings related to Sequential Switching Genetic Algorithm (SSGA)
	# 	self.settings_switching_GA = {'num_generations': 2, 'num_individuals': 3, 'pc': 0.9, 'pm': 0.1,
	# 	                              'min_porc_fitness': 5.0}


	'''
	Main method - execution of Graph GA (1st stage)
	'''
	def run_simulator(self):
		# Initialize graph GA object
		gga = graphGAModule.GraphGA(self.sm_folder, self.settings_graph_GA, self.settings_switching_GA,
		                            self.sw_assessment, self.networks_data, self.merit_index_conf)
		
		# Runs GA
		gga.run_gga()
		
		# Obtains results
		self.dict_results = gga.get_results()
