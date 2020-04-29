import graphGAModule
import switchingAssessmentModule
import xml.etree.ElementTree as ET

#===================================================================================#
'''
Class to convert graphs' data (edges and vertices) into 
their corresponding power networks' (opendss) data.
'''
class ConversorGrafoDSS(object):
	def __init__(self, xml_file_path):
		self.xml_file = None
		self.xml_file_path = xml_file_path
		self.listaArestas = []
		
		
	''' Method to read XML file with power networks' data '''
	def le_xml_dados_redes(self):
		self.xml_file = ET.parse(self.xml_file_path)
		no_raiz = self.xml_file.getroot()
		no_arestas = no_raiz.find('Arestas')
		for no_aresta in no_arestas:
			id_chave = no_aresta.find('Id').text
			cod_chave = no_aresta.find('CodigoChave').text	
			self.listaArestas.append([id_chave, cod_chave])
		
		
	'''
	DEBUG method 
	'''
	def imprime_arestas(self):
		for aresta in self.listaArestas:
			print("Id da Aresta: " + str(aresta[0]) + " Codigo da chave: " + str(aresta[1]))
	
	
#===================================================================================#	
'''
Main class: SM (Simulador de Manobras)
'''
class SM(object):
	def __init__(self, dados_simulacao):
		self.dados_simulacao = dados_simulacao # contains data and settings
		path_folder = self.dados_simulacao['local_dss'] # folder with DSS files
		pathXMLgrafo = path_folder + "\\..\\GrafoAlimentadores.xml" 
		
		# object to assess sequential switching through load flow simulations
		self.sw_assessment = switchingAssessmentModule.AssessSSGAIndiv(path_folder)
		
		# graph data
		self.conversorGrafoRede = ConversorGrafoDSS(pathXMLgrafo)   
		self.conversorGrafoRede.le_xml_dados_redes()
		#self.conversorGrafoRede.imprime_arestas()

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
		# Initialize graph GA object
		gga = graphGAModule.GraphGA(self.graph_descr, self.settings_graph_GA, self.settings_switching_GA)

		# Runs GA
		gga.run_gga()

		# Obtains results
		gga.get_results()
		
		
		
		
		
		
		
		
		
		
		
		
		
		