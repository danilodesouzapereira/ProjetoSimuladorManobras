import xml.etree.ElementTree as ET
import dijkstraModule


'''
This class is aimed to deal with all massive data related to the investigated
networks (power feeders). Contents:
	- Feeders registration
	- Switches registration
	- Graph of edges related to the faulted networks
	- Graph of the entire networks
'''

class NetworksData(object):
	def __init__(self, sm_folder_path):
		self.xml_file = None
		self.xml_file_path = sm_folder_path + "DadosRedes.xml"

		# initializations
		self.list_feeders_dicts = []
		self.list_switches_dicts = []
		self.list_graph_operable_switches_dicts = []
		self.list_graph_incidence_matrix = []
		self.crew_displ_times_mtx = [] # matrix of crew displacement times


	def initialize(self):
		self.xml_file = ET.parse(self.xml_file_path)
		root_node = self.xml_file.getroot()

		self.read_feeders_registration(root_node)
		self.read_switches_registration(root_node)
		self.read_graph_operable_switches(root_node)
		self.read_graph_incidence_matrix(root_node)

		# compute crew displacement times, using Dijkstra's algorithm,
		# which is based on shortest path determination
		self.compute_crew_displacement_times()


	'''
	Method to compute crew displacement times among switches, based on
	networks' incidence matrix.
	'''
	def compute_crew_displacement_times(self):
		inc_mtx = self.list_graph_incidence_matrix
		self.crew_displ_times_mtx = dijkstraModule.run_dijkstra(inc_mtx)
		a = 0


	def read_feeders_registration(self, root_node):
		node_feeders_registration = root_node.find('CadastroAlimentadores')
		for XMLnode in node_feeders_registration:
			dict_fd = {} # dict
			dict_fd.update({'code': XMLnode.find('CodigoAlimentador').text})
			dict_fd.update({'protection': XMLnode.find('ChaveProtecao').text})
			dict_fd.update({'max_current': float(XMLnode.find('MaximaCorrente').text)})
			self.list_feeders_dicts.append(dict_fd)


	def read_switches_registration(self, root_node):
		node_switches_registration = root_node.find('CadastroChaves')
		for XMLnode in node_switches_registration:
			dict_sw = {} # dict
			dict_sw.update({'id': int(XMLnode.find('Id').text)})
			dict_sw.update({'code': XMLnode.find('Codigo').text})
			dict_sw.update({'type': XMLnode.find('Tipo').text})
			self.list_switches_dicts.append(dict_sw)


	'''
	Method to read all data concerning the graph that represents the power networks, considering all
	possible operable switches.
	'''
	def read_graph_operable_switches(self, root_node):
		node_operable_edges = root_node.find('GrafoArestasOperaveis')
		for XMLnode in node_operable_edges:
			dict_edge = {} # dict
			dict_edge.update({'v1': int(XMLnode.find('V1').text)})
			dict_edge.update({'v2': int(XMLnode.find('V2').text)})
			dict_edge.update({'switch': XMLnode.find('Chave').text}) # code of its corresponding switch
			dict_edge.update({'initial': XMLnode.find('Inicial').text == "sim"}) # if it is initially closed
			self.list_graph_operable_switches_dicts.append(dict_edge)


	'''
	Method to read incidence matrix concerning the entire networks. This matrix
	is aimed at determining shortest paths between two given switches.
	'''
	def read_graph_incidence_matrix(self, root_node):
		node_graph_complete_network = root_node.find('GrafoRedeCompleta')
		node_incidence_matrix = node_graph_complete_network.find('MatrizIncidencias')

		list_elements = node_incidence_matrix.findall('Linha')

		# navigates over matrix lines, which have sintax: "3,1,2,3,5,3,2"
		for element in list_elements:
			matrix_line = element.text + ","
			list_mtx_items = [] ; pos = 0
			for i in range(len(matrix_line)):
				if matrix_line[i:i+1] == ",":
					list_mtx_items.append(float(matrix_line[pos:i]))
					pos = i+1
			# appends matrix line into final list of lines
			self.list_graph_incidence_matrix.append(list_mtx_items)



	'''
	Method to return list with switches' registration
	'''
	def get_list_switches(self):
		sw_list = []
		for sw in self.list_switches_dicts:
			dict_sw = {}
			dict_sw.update({'id_sw':sw['id']})
			dict_sw.update({'code_sw': sw['code']})
			dict_sw.update({'type_sw': sw['type']})
			sw_list.append(dict_sw)
		return sw_list


	'''
	Method to return information regarding graph edges representing
	all operable switches.
	'''
	def get_list_edges(self):
		edges_list = []

		list_edges_dicts = self.list_graph_operable_switches_dicts
		for dict_item in list_edges_dicts:

			# get switch ID
			sw_id = -1
			for sw in self.list_switches_dicts:
				if sw['code'] == dict_item['switch']:
					sw_id = int(sw['id'])
					break
			dict_edge = {}
			dict_edge.update({'id_sw': sw_id})
			dict_edge.update({'vertice_1': dict_item['v1']})
			dict_edge.update({'vertice_2': dict_item['v2']})
			dict_edge.update({'code_sw': dict_item['switch']})
			edges_list.append(dict_edge)
		return edges_list


	'''
	Method to return information regarding feeders' protection equipment
	'''
	def feeder_protections(self):
		feeder_info = []
		for item in self.list_feeders_dicts:
			dict_fd = {}  # dict
			dict_fd.update({'feeder': item['code']})
			dict_fd.update({'prot_switch': item['protection']})
			dict_fd.update({'max_curr': float(item['max_current'])})
			feeder_info.append(dict_fd)
		return feeder_info