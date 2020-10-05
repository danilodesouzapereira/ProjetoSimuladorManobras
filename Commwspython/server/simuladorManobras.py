import graphGAModule
import switchingAssessmentModule
import requests
import networksData
import time
import os.path
import json

# ===================================================================================#
'''
Main class: SM (Simulador de Manobras)
'''


class SM(object):
	def __init__(self, dados_diretorios, dados_isolacao_defeito, dados_simulacao):

		# Get data provided through the Web Service call
		self.dados_simulacao = dados_simulacao  # Dict with settings regarding simulations
		self.dados_diretorios = dados_diretorios  # Dict with folders paths
		self.dados_isolacao_defeito = dados_isolacao_defeito  # Dict with switches to be opened necessarily in order to isolate the fault
		dss_files_folder = self.dados_diretorios['local_dss']  # Folder with DSS files
		self.sm_folder = dss_files_folder + "\\..\\"

		self.settings_graph_GA = self.get_GGA_settings()      # settings of Graph Genetic Algorithm
		self.settings_switching_GA = self.get_SSGA_settings() # settings of Seq. Switching Genetic Algorithm

		# Get configurations concerning merit index calculation
		self.merit_index_conf = self.dados_simulacao['av_conf_indice_merito']

		# Object with all networks' data
		self.networks_data = networksData.NetworksData(self.sm_folder)
		self.networks_data.initialize()

		# Results
		self.dict_results: dict = None

		# Object to assess sequential switching through load flow simulations
		self.sw_assessment = switchingAssessmentModule.AssessSSGAIndiv(dss_files_folder, self.networks_data)


	'''
	Method to update dictionary with GGA settings
	'''
	def get_GGA_settings(self):
		settings_graph_GA = {}
		dict_conf = self.dados_simulacao['conf_ag_grafo']
		settings_graph_GA.update({'num_generations': int(dict_conf['num_geracoes'])})
		settings_graph_GA.update({'num_individuals': int(dict_conf['num_individuos'])})
		settings_graph_GA.update({'pc': float(dict_conf['pc'].replace(',','.'))})
		settings_graph_GA.update({'pm': float(dict_conf['pm'].replace(',','.'))})
		return settings_graph_GA


	'''
	Method to update dictionary with SSGA settings
	'''
	def get_SSGA_settings(self):
		settings_graph_GA = {}
		dict_conf = self.dados_simulacao['conf_ag_chv_otimo']
		settings_graph_GA.update({'num_generations': int(dict_conf['num_geracoes'])})
		settings_graph_GA.update({'num_individuals': int(dict_conf['num_individuos'])})
		settings_graph_GA.update({'pc': float(dict_conf['pc'].replace(',','.'))})
		settings_graph_GA.update({'pm': float(dict_conf['pm'].replace(',','.'))})
		settings_graph_GA.update({'min_porc_fitness': float(dict_conf['min_porc_fitness'].replace(',','.'))})
		settings_graph_GA.update({'start_switch': self.dados_simulacao['chave_partida']})
		return settings_graph_GA


	''' DEBUG method '''
	def print_output(self):
		local_saida = self.dados_diretorios['local_saida'] + "\\ArquivoSaida.txt"
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
	Method to send response to end-point and persist corresponding content to log file.
	'''
	def return_response(self, path_dat, id_sm):
		acao : str
		list_actions = []

		# list_sw_sequence_plans: list with switching sequence plans
		# each plan comprises a list of switching actions
		list_sw_sequence_plans = []

		for id_task in range(len(self.dict_results['actions'])):
			dict_action = self.dict_results['actions'][id_task]
			sw_code = dict_action['code'].upper() ; action = dict_action['action']
			if action == 'cl':
				task_type = 'FECHAR'
				description = 'Fechar a chave ' + sw_code
				device_type = 'CHAVE'
				phases_info = 'ABC'
				task_grouping = 'ISOLACAO'
			else:
				task_type = 'ABRIR'
				description = 'Abrir a chave ' + sw_code
				device_type = 'CHAVE'
				phases_info = 'ABC'
				task_grouping = 'ISOLACAO'
			list_actions.append({'TASK': str(id_task+1), 'TYPE': task_type, 'DEVICE': sw_code, 'DESCRIPTION': description, 'DEVICE_TYPE': device_type, 'PHASES': phases_info, 'GROUPING': task_grouping})

		# information about the switching sequence
		list_sw_sequence_plans.append({'RANK': '1', 'CHAVEAMENTOS': list_actions})

		# detailed information about the proposed plans of switching sequence
		return_data: dict = {}
		return_data.update({'ID': str(id_sm), 'DETAILS': list_sw_sequence_plans})

		print("Fitness: " + str(self.dict_results['Fitness']))

		# Produce simple debug
		self.save_log(return_data, path_dat)

		# Send return data via web service
		# #r = requests.post('http://127.0.0.1:5011/retornosimulacao', json=return_data)
		# url_local = 'http://localhost:8082/datasnap/rest/TServerMethods1/SaidaSM/'
		# r = requests.get(url_local + str(return_data))

		# Produce return through text file
		self.return_data_to_text_file(path_dat, return_data)


	'''
	Method to return dictionary with results
	'''
	def return_data_to_text_file(self, path_dat_folder, dict_return_data):
		path_out_file = path_dat_folder + "/DMS/DadosSimulacoesManobra/bancoresultados_sm.txt"
		path_out_file = os.path.normpath(path_out_file)
		if os.path.isfile(path_out_file):
			lines = list()
			with open(path_out_file, "r") as f:
				for line in f:
					lines.append(line)
			string_json_return_data = json.dumps(dict_return_data)
			lines.insert(0, string_json_return_data + "\n")
			with open(path_out_file, "w") as f:
				f.writelines(lines)
		else:
			lines = list()
			string_json_return_data = json.dumps(dict_return_data)
			lines.insert(0, string_json_return_data + "\n")
			with open(path_out_file, "w") as f:
				f.writelines(lines)


	'''
	Method to persist logs concerning the simulation
	'''
	def save_log(self, dict_return_data : dict, path_file_dat):
		path_file_log_ss = path_file_dat + "DMS\\logs\\log_simulador_manobra.txt"
		arq = open(path_file_log_ss, "w+")
		arq.write(str(dict_return_data))
		arq.close()


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
	Method to include all initial necessary switches that need to be opened, which are necessary to isolate the faulty area.
	'''
	def add_initial_necessary_switchings(self):
		for i in range(len(self.dados_isolacao_defeito)):
			codigo_chave = (self.dados_isolacao_defeito['chave' + str(i+1)]).lower()
			dict_op = {'code': codigo_chave, 'action': 'op'}
			self.dict_results['actions'].insert(0, dict_op)


	'''
	Main method - execution of Graph GA (1st stage)
	'''
	def run_simulator(self):
		# Initialize graph GA object
		gga = graphGAModule.GraphGA(self.sm_folder, self.settings_graph_GA, self.settings_switching_GA,
		                            self.sw_assessment, self.networks_data, self.merit_index_conf)
			
		# Run GA
		gga.run_gga()
		print("\nGGA finalizado")
		
		# Obtain results
		self.dict_results = gga.get_results()

		# Insert initial switchings, which are necessary to isolate the fault.
		self.add_initial_necessary_switchings()
		
		print("\nDict de resultados:\n")
		print(self.dict_results)
		time.sleep(5)