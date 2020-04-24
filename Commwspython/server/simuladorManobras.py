import graphGAModule
import dss
import win32com.client
from win32com.client import makepy
import sys
import gc
import numpy as np
import xml.etree.ElementTree as ET

#===================================================================================#
'''
Classe para fazer a conversão entre dados de grafos (vértices e arestas) e os dados de redes 
(OpenDSS) correspondentes.
'''
class ConversorGrafoDSS(object):
	def __init__(self, path_arquivo_xml):
		self.xml_file = None
		self.path_arquivo_xml = path_arquivo_xml
		self.listaArestas = []
		
		
	''' Método para leitura do XML de dados das redes '''
	def le_xml_dados_redes(self):
		self.xml_file = ET.parse(self.path_arquivo_xml)	
		no_raiz = self.xml_file.getroot()
		no_arestas = no_raiz.find('Arestas')
		for no_aresta in no_arestas:
			id = no_aresta.find('Id').text
			cod_chave = no_aresta.find('CodigoChave').text	
			self.listaArestas.append([id, cod_chave])
		
		
	''' Método DEBUG '''
	def imprime_arestas(self):
		for aresta in self.listaArestas:
			print("Id da Aresta: " + str(aresta[0]) + " Codigo da chave: " + str(aresta[1]))
	
	
#===================================================================================#	
'''
Classe principal: SM (Simulador de Manobras)
'''
class SM(object):
	def __init__(self, dados_simulacao):
		# obtém dados e configurações
		self.dados_simulacao = dados_simulacao          
		path_folder = self.dados_simulacao['local_dss']             # diretório com os arquivos DSS
		pathXMLgrafo = path_folder + "\\..\\GrafoAlimentadores.xml" 
		
		# objeto para execução de fluxo de potência
		self.dss = dss.DSS(path_folder)
		#self.dss.solve_power_flow()  # teste (DEBUG)                              
		
		# dados do grafo
		self.conversorGrafoRede = ConversorGrafoDSS(pathXMLgrafo)   
		self.conversorGrafoRede.le_xml_dados_redes()
		#self.conversorGrafoRede.imprime_arestas()
			
			
	''' Método DEBUG '''
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
		
		
	''' Método DEBUG '''
	def print_data(self):
		print(self.dados_simulacao)
	
	
	''' Método DEBUG '''
	def execute_test(self):
		edges = []
		edges.append([0,1,1])
		n_vertices = 21

		graph_description = [n_vertices, edges]
		num_individuals = 10

		gga = graphGAModule.GraphGA(graph_description, num_individuals)
		gga.generate_individuals()             

		print(":::::::::::::::::::::::::::")
		print("       GRAPH MUTATION      ")
		print(":::::::::::::::::::::::::::")
		gga.graph_mutation()

		print(":::::::::::::::::::::::::::")
		print("      GRAPH CROSSOVER      ")
		print(":::::::::::::::::::::::::::")
		gga.graph_crossover()	
	
	
	''' Método principal - execução do algoritmo genético baseado em grafos '''
	def run_simulator(self):
		#________________________________________________________#
		#                                                        #
		#              DEFINIÇÕES E CONFIGURAÇÕES
		#     (Podem ser lidas de arquivo de configurações)

		num_geracoes, num_individuos, pc, pm = 3, 5, 0.9, 0.1
		num_vertices = self.dados_simulacao['num_vertices'] 	
		arestas = [] ; arestas_iniciais = []
		for aresta_json in self.dados_simulacao['arestas']:
			arestas.append([aresta_json['u'], aresta_json['v'], aresta_json['w']])
		for aresta_inicial in self.dados_simulacao['arestas_iniciais']:
			arestas_iniciais.append([aresta_inicial['u'], aresta_inicial['v'], aresta_inicial['w']])
		descricao_grafo = {'num_vertices' : num_vertices, 'arestas' : arestas, 'arestas_iniciais' : arestas_iniciais}
		descricao_ag = {'num_geracoes' : num_geracoes, 'num_individuos' : num_individuos, 'pc' : pc, 'pm' : pm}
		#                                                        #
		#________________________________________________________#
		
		# Inicia objeto de AG
		gga = graphGAModule.GraphGA(descricao_grafo, descricao_ag)
		
		# Executa o AG
		gga.run_gga()
		
		# Obtém os resultados
		gga.get_results()
		
		
		
		
		
		
		
		
		
		
		
		
		
		