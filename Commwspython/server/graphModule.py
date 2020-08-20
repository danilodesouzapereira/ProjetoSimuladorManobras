# Python program for Kruskal's algorithm to find 
# Minimum Spanning Tree of a given connected, 
# undirected and weighted graph 

# from collections import defaultdict
import random 
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np


'''
Class to represent a graph 
'''


class Graph: 
	def __init__(self, vertices):
		self.V = vertices  # Number of vertices
		self.graph = []  # Default dictionary to store graph
		self.edgesKRST = []  # Store edges after KruskalRST procedure


	'''
	Function to add an edge to graph
	'''
	def addEdge(self, u, v, w):
		self.graph.append([u, v, w])


	''' 
	Utility function to find set of an element i
	(uses path compression technique) 
	'''
	def find(self, parent, i): 
		if parent[i] == i: 
			return i 
		return self.find(parent, parent[i]) 

		
	''' 
	Function to plot graph 
	'''
	def plot_graph(self):
		g = nx.Graph()
		nodes_list = set([])
		for edge in self.edgesKRST:
			nodes_list.add(edge[0])
			nodes_list.add(edge[1])
		g.add_nodes_from(nodes_list)
		
		for edge in self.edgesKRST:
			g.add_edge(edge[0], edge[1])

		nx.draw(g, with_labels=True)
		plt.draw()
		plt.show()


	'''
	Method to return vertices which are disconnected to vertice 0
	'''
	def isolated_vertices(self):

		# Assess initially isolated vertices. There is no edge connecting them.
		isol_vertices_1 = set(range(self.V))
		for edge in self.graph:
			if edge[0] in isol_vertices_1:
				isol_vertices_1.remove(edge[0])
			if edge[1] in isol_vertices_1:
				isol_vertices_1.remove(edge[1])

		# Assess initially connected vertices.
		edges_list = self.graph.copy()
		repeat = True
		find_vertice_set = {0}
		while repeat:
			repeat = False
			for i in reversed(range(len(edges_list))):
				edge = edges_list[i]
				if edge[0] in find_vertice_set or edge[1] in find_vertice_set:
					find_vertice_set.add(edge[0])
					find_vertice_set.add(edge[1])
					edges_list.remove(edge)
					repeat = True

		# fill list of isolated vertices based on remaining edges
		isol_vertices_2 = set()
		if len(edges_list) > 0:
			for edge in edges_list:
				isol_vertices_2.add(edge[0])
				isol_vertices_2.add(edge[1])

		# determine the list of all isolated vertices
		list_isolated_vertices = list(isol_vertices_1.union(isol_vertices_2))

		return list_isolated_vertices


		
	''' 
	Function that does union of two sets of x and y (uses union by rank) 
	'''
	def union(self, parent, rank, x, y): 
		xroot = self.find(parent, x) 
		yroot = self.find(parent, y) 

		# Attach smaller rank tree under root of 
		# high rank tree (Union by Rank) 
		if rank[xroot] < rank[yroot]: 
			parent[xroot] = yroot 
		elif rank[xroot] > rank[yroot]: 
			parent[yroot] = xroot 

		# If ranks are same, then make one as root 
		# and increment its rank by one 
		else : 
			parent[yroot] = xroot 
			rank[xroot] += 1

			
	''' 
	The main function to construct MST using Kruskal's algorithm 
	'''
	def KruskalMST(self): 

		result =[] #This will store the resultant MST 

		i = 0 # An index variable, used for sorted edges 
		e = 0 # An index variable, used for result[] 

			# Step 1: Sort all the edges in non-decreasing 
				# order of their 
				# weight. If we are not allowed to change the 
				# given graph, we can create a copy of graph 
		self.graph = sorted(self.graph,key=lambda item: item[2]) 

		parent = [] ; rank = [] 

		# Create V subsets with single elements 
		for node in range(self.V): 
			parent.append(node) 
			rank.append(0) 
	
		# Number of edges to be taken is equal to V-1 
		while e < self.V -1 : 

			# Step 2: Pick the smallest edge and increment 
					# the index for next iteration 
			u,v,w = self.graph[i] 
			i = i + 1
			x = self.find(parent, u) 
			y = self.find(parent ,v) 

			# If including this edge does't cause cycle, 
						# include it in result and increment the index 
						# of result for next edge 
			if x != y: 
				e = e + 1	
				result.append([u,v,w]) 
				self.union(parent, rank, x, y)			 
			# Else discard the edge 

		# print the contents of result[] to display the built MST 
		#print("Following are the edges in the constructed MST")
		#for u,v,weight in result: 
			#print str(u) + " -- " + str(v) + " == " + str(weight) 
			#print ("%d -- %d == %d" % (u,v,weight))
	# Crossover operator. It takes two parent individuals and generates
	# offspring which contains characteristics from both parents.
	#def crossover(self, parent_edges_1, parent_edges_2):
	#	if parent_edges_1 == None or parent_edges_2 == None:
	#		return None
	#	
	#	# Gathers edges from both parents
	#	union_edges = list(set(parent_edges_1) | set(parent_edges_2))
		
		
		
			
	'''		
	Mutation operator. It deletes a random edge and inserts a new one.
	To guarantee radiality, it verifies if newly added edge creates mesh.
	'''
	def mutation(self):
		if len(self.edgesKRST) == 0:
			return
			
		# determines edge to be removed
		i_remove = random.randint(0, len(self.edgesKRST)-1)
		removed_edge = self.edgesKRST[i_remove]
		self.edgesKRST.remove(removed_edge)
		
		# adds edge at random, provided that it does not create mesh
		new_edge = self.pick_radial_edge(removed_edge)
		if new_edge != None:	
			self.edgesKRST.append(new_edge)
		else:
			self.edgesKRST.append(removed_edge)

	'''
	Method to determine if current graph topology is radial
	'''
	def is_radial(self):
		parent = []; rank = []
		for node in range(self.V): parent.append(node); rank.append(0)
		for edge in self.edgesKRST:
			x = self.find(parent, edge[0]); y = self.find(parent, edge[1])
			self.union(parent, rank, x, y)
			if x == y: return False
		return True


	'''
	Method to determine if closing edge causes mesh
	'''
	def creates_mesh(self, candidate_edge):
		parent = [] ; rank = []
		for node in range(self.V):
			parent.append(node) ; rank.append(0)
		for edge in self.edgesKRST:
			x = self.find(parent, edge[0]) ; y = self.find(parent, edge[1])
			self.union(parent, rank, x, y)

		# tries to insert candidate edge
		x = self.find(parent, candidate_edge[0]); y = self.find(parent, candidate_edge[1])
		# returns if candidate edge creates mesh
		return x == y


	'''
	Method to pick a switch/edge to open in order to restore
	graph radiality
	'''
	def edge_to_open_mesh(self, list_switches_to_open):
		# verifications
		if list_switches_to_open is None: return None
		if len(list_switches_to_open) == 0: return None

		str_conn_edges = ""
		for edge in self.edgesKRST:
			str_conn_edges += str(edge) + " "
		str_sw_to_open = ""
		for edge in list_switches_to_open:
			str_sw_to_open += str(edge) + " "
		# print("connected edges: " + str_conn_edges + " switches to open: " + str_sw_to_open)

		# Among the edges that need to be opened, picks an edge
		# to be opened in order to restore radiality
		for edge_to_be_opened in list_switches_to_open:
			# edge_list = list(edge) ; edge_to_be_opened = [edge_list[0], edge_list[1], 1]

			# tries to remove edge_to_be_opened from graph
			edge_to_be_opened_1 = [edge_to_be_opened[0], edge_to_be_opened[1], 1]
			edge_to_be_opened_2 = [edge_to_be_opened[1], edge_to_be_opened[0], 1]
			if edge_to_be_opened_1 in self.edgesKRST:
				edge_to_be_opened = edge_to_be_opened_1
			elif edge_to_be_opened_2 in self.edgesKRST:
				edge_to_be_opened = edge_to_be_opened_2

			# print("edge_to_be_opened: " + str(edge_to_be_opened))
			self.edgesKRST.remove(edge_to_be_opened)

			# if resulting graph is radial, returns.
			if self.is_radial(): return edge_to_be_opened
			else: self.edgesKRST.append(edge_to_be_opened)
		return None


	'''
	Method to pick edge that does not cause mesh
	'''
	def pick_radial_edge(self, removed_edge):
		parent = [] ; rank = []
		for node in range(self.V): 
			parent.append(node) 
			rank.append(0) 
		for edge in self.edgesKRST:
			u = edge[0]; v = edge[1]
			x = self.find(parent, u); y = self.find(parent, v)
			self.union(parent, rank, x, y)	
			
		# gets all candidate edges
		candidate_edges = []
		for edge in self.graph:
			if edge in self.edgesKRST or edge == removed_edge:
				continue
			candidate_edges.append(edge)
			
		#print("total candidates: %d" % (len(candidate_edges)))
		#for edge in candidate_edges:
		#	print("candidate: %d -- %d" % (edge[0], edge[1]))
		
		# Picks an edge at random. If it does not create cycle, returns the edge.
		random_index = -1
		for i in range(len(candidate_edges)):
			random_index = random.randint(0, len(candidate_edges)-1)
			edge = candidate_edges[random_index]
			u = edge[0] ; v = edge[1]
			x = self.find(parent, u); y = self.find(parent, v)
			if x != y:
				return edge
		return None

		
	''' 
	Function to print graph 
	'''
	def print_graph(self):
		# print the contents of result[] to display the built MST 
		for edge in self.edgesKRST: 
			print ("%d -- %d" % (edge[0],edge[1]))


	'''
	Variation of original method "KruskalRST". This one considers edges biased, in such a way that initially closed
	edges are more likely to be picked.
	'''
	def KruskalRST_biased(self, initial_edges, bias_prob):
		result = []  # This will store the resultant RST
		i = 0  # An index variable, used for sorted edges
		e = 0  # An index variable, used for result[]

		# randomly rearrange the graph
		random.shuffle(self.graph)

		# arrange graph in such a way that initially closed edges appear first
		for ini_edge in initial_edges:
			if np.random.randint(0, 100) > bias_prob:
				continue
			index = self.graph.index(ini_edge)
			item = self.graph.pop(index)
			self.graph.insert(0, item)
		parent = []; rank = []

		# Create V subsets with single elements
		for node in range(self.V):
			parent.append(node)
			rank.append(0)

		# Number of edges to be taken is equal to V-1
		while e < self.V - 1:

			# Step 2: Pick the smallest edge and increment
			# the index for next iteration
			u, v, w = self.graph[i]
			i = i + 1
			x = self.find(parent, u)
			y = self.find(parent, v)

			# If including this edge does't cause cycle,
			# include it in result and increment the index
			# of result for next edge
			if x != y:
				e = e + 1
				result.append([u, v, w])
				self.union(parent, rank, x, y)
				self.edgesKRST.append([u, v, w])  # saves spanning tree generated randomly

	# Else discard the edge


	''' 
	The main function to construct RST using Kruskal's algorithm 
	'''
	def KruskalRST(self): 

		result = [] # This will store the resultant RST 
		i = 0       # An index variable, used for sorted edges 
		e = 0       # An index variable, used for result[] 

		# Step 1: Sort all the edges in non-decreasing 
		# order of their 
		# weight. If we are not allowed to change the 
		# given graph, we can create a copy of graph 
		#self.graph = sorted(self.graph,key=lambda item: item[2]) 
		
		
		# randomly rearrange the graph
		random.shuffle(self.graph)			

		parent = [] ; rank = [] 

		# Create V subsets with single elements 
		for node in range(self.V): 
			parent.append(node) 
			rank.append(0) 		
			
		# Number of edges to be taken is equal to V-1 
		while e < self.V -1 : 

			# Step 2: Pick the smallest edge and increment 
			# the index for next iteration 
			u,v,w = self.graph[i] 
			i = i + 1
			x = self.find(parent, u) 
			y = self.find(parent ,v) 

			# If including this edge does't cause cycle, 
						# include it in result and increment the index 
						# of result for next edge 
			if x != y: 
				e = e + 1	
				result.append([u,v,w]) 
				self.union(parent, rank, x, y)			 
				self.edgesKRST.append([u,v,w]) # saves spanning tree generated randomly
			# Else discard the edge 