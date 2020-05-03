import xml.etree.ElementTree as ET


'''
Class to convert graphs' data (edges and vertices) into 
their corresponding power networks' (opendss) data.
'''
class ConversorGrafoDSS(object):
	def __init__(self, xml_file_path):
		self.xml_file = None
		self.xml_file_path = xml_file_path
		self.edges_list = []

	''' Method to read data regarding the power networks' '''
	def read_xml_network_graph(self):
		self.xml_file = ET.parse(self.xml_file_path)
		root_node = self.xml_file.getroot()

		# reads edges data
		edges_node = root_node.find('Arestas')
		for XMLnode in edges_node:
			dict_sw = {} # dict
			dict_sw.update({'id_sw':XMLnode.find('Id').text})
			dict_sw.update({'code_sw': XMLnode.find('CodigoChave').text})
			dict_sw.update({'vertice_1': XMLnode.find('Vertice1').text})
			dict_sw.update({'vertice_2': XMLnode.find('Vertice2').text})
			self.edges_list.append(dict_sw)


	''' Method to read information related to the feeders' protection equipemnt '''
	def read_xml_feeder_protections(self):
		feeder_info = []
		self.xml_file = ET.parse(self.xml_file_path)
		root_node = self.xml_file.getroot()

		# reads feeders data
		feeders_node = root_node.find('Alimentadores')
		for XMLnode in feeders_node:
			dict_fd = {}  # dict
			dict_fd.update({'feeder': XMLnode.find('CodigoAlimentador').text})
			dict_fd.update({'prot_switch': XMLnode.find('ChaveProtecao').text})
			feeder_info.append(dict_fd)
		return feeder_info