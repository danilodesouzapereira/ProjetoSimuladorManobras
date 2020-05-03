# Python program for Dijkstra's single
# source shortest path algorithm. The program is
# for adjacency matrix representation of the graph

# This code is contributed by Divyanshu Mehta

# Library for INT_MAX
import sys

class Graph:
	def __init__(self, vertices):
		self.V = vertices
		self.graph = [[0 for column in range(vertices)]
					for row in range(vertices)]

	def printSolution(self, dist):
		print("Vertex tDistance from Source")
		for node in range(self.V):
			print(node, "t", dist[node])

	# A utility function to find the vertex with
	# minimum distance value, from the set of vertices
	# not yet included in shortest path tree
	def minDistance(self, dist, sptSet):
		# Initilaize minimum distance for next node
		min = sys.maxsize
		min_index = -1

		# Search not nearest vertex not in the
		# shortest path tree
		for v in range(self.V):
			if dist[v] < min and sptSet[v] == False:
				min = dist[v]
				min_index = v
		return min_index


	'''
	Function to return list of distances from a given ref index
	'''
	def dijkstra_line_values(self, ref_index):
		dist = [sys.maxsize] * self.V ; dist[ref_index] = 0
		sptSet = [False] * self.V

		for cout in range(self.V):

			# Pick the minimum distance vertex from the set of vertices not yet processed.
			# u is always equal to src in first iteration
			u = self.minDistance(dist, sptSet)

			# Put the minimum distance vertex in the shotest path tree
			sptSet[u] = True

			# Update dist value of the adjacent vertices of the picked vertex only if the current
			# distance is greater than new distance and the vertex in not in the shotest path tree
			for v in range(self.V):
				if self.graph[u][v] > 0 and sptSet[v] == False and dist[v] > dist[u] + self.graph[u][v]:
					dist[v] = dist[u] + self.graph[u][v]

		return dist


	# Funtion that implements Dijkstra's single source
	# shortest path algorithm for a graph represented
	# using adjacency matrix representation
	def dijkstra(self, src):

		dist = [sys.maxsize] * self.V
		dist[src] = 0
		sptSet = [False] * self.V

		for cout in range(self.V):

			# Pick the minimum distance vertex from
			# the set of vertices not yet processed.
			# u is always equal to src in first iteration
			u = self.minDistance(dist, sptSet)

			# Put the minimum distance vertex in the
			# shotest path tree
			sptSet[u] = True

			# Update dist value of the adjacent vertices
			# of the picked vertex only if the current
			# distance is greater than new distance and
			# the vertex in not in the shotest path tree
			for v in range(self.V):
				if self.graph[u][v] > 0 and sptSet[v] == False and dist[v] > dist[u] + self.graph[u][v]:
					dist[v] = dist[u] + self.graph[u][v]

		self.printSolution(dist)


def run_dijkstra(inc_mtx):
	num_nodes = len(inc_mtx)
	g = Graph(num_nodes)

	# insert incidence matrix (connections) between nodes (switches)
	for i in range(num_nodes):
		line = inc_mtx[i]
		g.graph[i] = line

	# compute dijkstras shortest path between nodes
	dist_list = []
	for i in range(num_nodes):
		dist_to_node_i = g.dijkstra_line_values(i)
		dist_list.append(dist_to_node_i)

	return dist_list