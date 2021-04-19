import graphGAModule
import switchingAssessmentModule
import requests
import networksData
import time
import datetime
import os.path
import json

# ===================================================================================#
'''
Main class: SM (Simulador de Manobras)
'''

class SM(object):
	def __init__(self, dados_diretorios, dados_isolacao_defeito, dados_simulacao, path_chv_sem_manobra_anel):
		# Get data provided through the Web Service call
		self.dados_simulacao = dados_simulacao  # Dict with settings regarding simulations
		self.dados_diretorios = dados_diretorios  # Dict with folders paths
		self.dados_isolacao_defeito = dados_isolacao_defeito  # Dict with switches to be opened necessarily in order to isolate the fault
		self.lista_chaves_excecoes = self.generate_sw_list_exceptions(path_chv_sem_manobra_anel)  # List of switches that cannot be operated (exception rules)
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
		settings_graph_GA.update({'aux_switching': (self.dados_simulacao['chav_auxiliar'].upper() == "TRUE")})
		dict_conf = self.dados_simulacao['conf_ag_chv_otimo']
		settings_graph_GA.update({'num_generations': int(dict_conf['num_geracoes'])})
		settings_graph_GA.update({'num_individuals': int(dict_conf['num_individuos'])})
		settings_graph_GA.update({'pc': float(dict_conf['pc'].replace(',','.'))})
		settings_graph_GA.update({'pm': float(dict_conf['pm'].replace(',','.'))})
		settings_graph_GA.update({'min_porc_fitness': float(dict_conf['min_porc_fitness'].replace(',','.'))})
		settings_graph_GA.update({'start_switch': self.dados_simulacao['chave_partida']})
		return settings_graph_GA


	''' Method to generate list of switches that cannot be operated (exception rules) '''
	def generate_sw_list_exceptions(self, path_chv_sem_manobra_anel):
		if not os.path.isfile(path_chv_sem_manobra_anel):
			return []
		arquivo_chaves_excecoes = open(path_chv_sem_manobra_anel, "r")
		sw_list_exceptions = []
		for line in arquivo_chaves_excecoes:
			code_sw = line.rstrip()
			sw_list_exceptions.append(code_sw.lower())
		return sw_list_exceptions


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
	def return_response(self, path_dat, id_sm, id_plano, self_healing):
		acao: str
		list_actions = []

		for id_task in range(len(self.dict_results['actions'])):
			dict_action = self.dict_results['actions'][id_task]
			sw_code = dict_action['code'].upper(); action = dict_action['action']; task_grouping: str = dict_action['grouping'].upper()
			device_type = 'CHAVE'; phases_info = 'ABC'
			if action == 'cl':
				task_type = 'FECHAR'
				description = 'Fechar a chave ' + sw_code
			else:
				task_type = 'ABRIR'
				description = 'Abrir a chave ' + sw_code
			list_actions.append({'TASK': id_task+1, 'TYPE': task_type, 'DEVICE': sw_code, 'DESCRIPTION': description, 'DEVICE_TYPE': device_type, 'PHASES': phases_info, 'GROUPING': task_grouping})

		# information about the switching sequence
		sw_seq_details : dict = {'RANK': 1, 'CHAVEAMENTOS': list_actions}

		# detailed information about the proposed plans of switching sequence
		return_data: dict = {}
		return_data.update({'ID': id_sm})
		return_data.update({'ID_PLANO': id_plano})
		return_data.update({'STATUS': 'OK'})
		return_data.update({'COMMENT': '0'})
		return_data.update({'DETAILS': sw_seq_details})

		print("Fitness: " + str(self.dict_results['Fitness']))

		# Produce simple debug
		self.save_log(return_data, path_dat)

		# Send return data via web service
		# #r = requests.post('http://127.0.0.1:5011/retornosimulacao', json=return_data)
		# url_local = 'http://localhost:8082/datasnap/rest/TServerMethods1/SaidaSM/'
		# r = requests.get(url_local + str(return_data))

		# Produce return through text file
		self.return_data_to_text_file(path_dat, return_data, self_healing)


	'''
	Method to provide a formatted datetime regarding the simulation_end
	'''
	def time_now(self):
		now = datetime.datetime.now()
		formatted_datetime = now.strftime("%d/%m/%Y %H:%M")
		return formatted_datetime


	'''
	Method to return dictionary with results
	'''
	def return_data_to_text_file(self, path_dat_folder, dict_return_data, self_healing):
		if self_healing == 0:
			path_out_file = path_dat_folder + "/DMS/DadosSimulacoesManobra/bancoresultados_sm.txt"
		elif self_healing == 1:
			path_out_file = path_dat_folder + "/DMS/DadosSimulacoesManobraSH/bancoresultados_smsh.txt"
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
	Method to compose the final sequence of switching operations. Two situations are considered:
		1) Emergency simulations: in this case, some blocks are initially de-energized. Then, the sequence is:
			a) Completely de-energize the reference blocks;
			b) Reconnect the sound downstream blocks;
		2) Scheduled simulations: in this case, all blocks are initially energized. The required sequence is:
			a) Close normally opened switches downstream the reference blocks;
			b) Completely de-energize the reference blocks;
	'''
	def compose_final_sw_operations(self, self_healing):
		# 1. Adjust dictionaries' elements, including 'grouping' key
		for dict_op in self.dict_results['actions']:
			dict_op.update({'grouping': 'remanejamento'})

		# 2. Insert other operations
		if self_healing == 0:
			if self.dados_simulacao['tipo_simulacao'].lower() == 'e':
				# isolate and then reconnect sound equipment
				self.compose_final_sw_operations_emergency_simulation()
			else:
				# if meshed allowed, reconnect downstream blocks and then isolate reference area
				self.compose_final_sw_operations_scheduled_simulation()
		elif self_healing == 1:
			self.compose_final_sw_operations_sh()

		# mirror actions of isolation and reconnection
		self.mirror_sw_operations()


	'''
	Method to mirror isolation and reconnection sw operations
	'''
	def mirror_sw_operations(self):
		if len(self.dict_results['actions']) == 0:
			return
		num_actions = len(self.dict_results['actions'])
		index: int = num_actions-1
		while index >= 0:
			dict_action = self.dict_results['actions'][index]
			mirr_dict_action = None
			if dict_action['action'] == 'op':
				mirr_dict_action = {'code': dict_action['code'], 'action': 'cl', 'grouping': 'retorno'}
			elif dict_action['action'] == 'cl':
				mirr_dict_action = {'code': dict_action['code'], 'action': 'op', 'grouping': 'retorno'}
			if mirr_dict_action is not None:
				self.dict_results['actions'].append(mirr_dict_action)
			index = index - 1


	'''
		Method to compose the final sequence of SH switching operations.
	'''
	def compose_final_sw_operations_sh(self):
		# 1. Switches downstreams the area to be isolated
		for i in range(len(self.dados_isolacao_defeito)):
			codigo_chave = (self.dados_isolacao_defeito['chave' + str(i+1)]).lower()
			dict_op = {'code': codigo_chave, 'action': 'op', 'grouping': 'isolacao'}

			# 1.1 Verifiy if sw is recloser
			is_recloser = False
			cod_chv : str = codigo_chave.lower()
			pos_rl = cod_chv.find("rl")
			pos_re = cod_chv.find("re")
			if pos_rl > -1 or pos_re > -1:
				is_recloser = True

			# 1.2 Insert isolation switching
			if is_recloser:
				self.dict_results['actions'].insert(0, dict_op)


	'''
		Method to compose the final sequence of EMERGENCY switching operations.
	'''
	def compose_final_sw_operations_emergency_simulation(self):
		# 1. Switches downstreams the area to be isolated
		for i in range(len(self.dados_isolacao_defeito)):
			codigo_chave = (self.dados_isolacao_defeito['chave' + str(i+1)]).lower()
			dict_op = {'code': codigo_chave, 'action': 'op', 'grouping': 'remanejamento'}
			self.dict_results['actions'].insert(0, dict_op)

		# 2. Check if it is necessary to include switch immediately upstreams the area to be isolated.
		# If upstream sw is circuit breaker or recloser, it is not necessary to be opened.
		codigo_chave_montante = self.dados_simulacao['chave_partida'].lower()
		sw_records = self.networks_data.get_list_switches()
		open_upstream_sw = False
		for sw in sw_records:
			if sw['code_sw'].lower() != codigo_chave_montante.lower(): continue
			if sw['type_sw'] == 'disjuntor' or sw['type_sw'] == 'religadora':
				open_upstream_sw = False
			else:
				open_upstream_sw = True
			break
		if not open_upstream_sw:
			return

		# 3. Check if upstream sw is already in the task list.
		dict_res = None
		for i in range(len(self.dict_results['actions'])):
			dict_res = self.dict_results['actions'][i]
			if dict_res['code'].lower() == codigo_chave_montante.lower():
				break
			dict_res = None

		if dict_res: # if already exists, remove and insert at i=0
			self.dict_results['actions'].remove(dict_res)
			dict_res_novo = {'code': codigo_chave_montante, 'action': 'op', 'grouping': 'isolacao'}
			self.dict_results['actions'].insert(0, dict_res_novo)
		else:  # if does not exist, insert at i=0
			dict_res_novo = {'code': codigo_chave_montante, 'action': 'op', 'grouping': 'isolacao'}
			self.dict_results['actions'].insert(0, dict_res_novo)


	'''
		Method to check if at least one switching operation is not allowed  
	'''
	def check_if_meshed_allowed(self):
		# Check switches to be closed
		for dict_action in self.dict_results['actions']:
			if dict_action['action'] == 'cl':
				# dict format: {'code': codigo_chave_montante, 'action': 'op'}
				code_sw: str = dict_action['code']
				if code_sw.lower() in self.lista_chaves_excecoes:
					return False
		return True


	''' 
		Method to compose the final sequence of SCHEDULED switching operations.
	'''
	def compose_final_sw_operations_scheduled_simulation(self):
		# 1. Check if meshed operation is allowed
		# meshed_allowed = True   # change here, according to actual permission
		meshed_allowed: bool = self.check_if_meshed_allowed()

		if meshed_allowed:
			# 1.1 If meshed operations are allowed, connect neighboring feeder BEFORE de-energizing reference blocks
			for i in range(len(self.dados_isolacao_defeito)):  # Switches downstreams the area to be isolated
				codigo_chave = (self.dados_isolacao_defeito['chave' + str(i + 1)]).lower()
				dict_op = {'code': codigo_chave, 'action': 'op', 'grouping': 'remanejamento'}
				self.dict_results['actions'].append(dict_op)

			# 1.2 Check if immediately upstream switch is already in the task list
			codigo_chave_montante = self.dados_simulacao['chave_partida'].lower()
			dict_res = None
			for i in range(len(self.dict_results['actions'])):
				dict_res = self.dict_results['actions'][i]
				if dict_res['code'].lower() == codigo_chave_montante.lower():
					break
				dict_res = None
			if dict_res:  # if already exists, remove and insert at i=0
				self.dict_results['actions'].remove(dict_res)
				dict_res_novo = {'code': codigo_chave_montante, 'action': 'op', 'grouping': 'isolacao'}
				self.dict_results['actions'].append(dict_res_novo)
			else:  # if does not exist, remove and insert at i=0
				dict_res_novo = {'code': codigo_chave_montante, 'action': 'op', 'grouping': 'isolacao'}
				self.dict_results['actions'].append(dict_res_novo)
		else:
			# 1.3 If meshed operations are NOT allowed, de-energize reference blocks BEFORE connecting neighboring feeder
			for i in range(len(self.dados_isolacao_defeito)):  # Switches downstreams the area to be isolated
				codigo_chave = (self.dados_isolacao_defeito['chave' + str(i + 1)]).lower()
				dict_op = {'code': codigo_chave, 'action': 'op', 'grouping': 'isolacao'}
				self.dict_results['actions'].insert(0, dict_op)
			# 1.4 Check if immediately upstream switch is already in the task list
			codigo_chave_montante = self.dados_simulacao['chave_partida'].lower()
			dict_res = None
			for i in range(len(self.dict_results['actions'])):
				dict_res = self.dict_results['actions'][i]
				if dict_res['code'].lower() == codigo_chave_montante.lower():
					break
				dict_res = None
			if dict_res:  # if already exists, remove and insert at i=0
				self.dict_results['actions'].remove(dict_res)
				dict_res_novo = {'code': codigo_chave_montante, 'action': 'op', 'grouping': 'isolacao'}
				self.dict_results['actions'].insert(0, dict_res_novo)
			else:  # if does not exist, remove and insert at i=0
				dict_res_novo = {'code': codigo_chave_montante, 'action': 'op', 'grouping': 'isolacao'}
				self.dict_results['actions'].insert(0, dict_res_novo)


	'''
	Main method - execution of Graph GA (1st stage)
	'''
	def run_simulator(self, self_healing):
		# Initialize graph GA object
		gga = graphGAModule.GraphGA(self.sm_folder, self.settings_graph_GA, self.settings_switching_GA,
		                            self.sw_assessment, self.networks_data, self.merit_index_conf)

		# Run GA
		gga.run_gga()
		print("\nGGA finalizado")

		# Obtain results
		self.dict_results = gga.get_results()

		# Compose the final sequence of switching operations
		# self.add_initial_necessary_switchings()
		self.compose_final_sw_operations(self_healing)
		
		print("\nDict de resultados:\n")
		print(self.dict_results)
		time.sleep(1)