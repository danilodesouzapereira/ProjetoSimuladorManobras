import win32com.client
from win32com.client import makepy
import sys
import gc
import numpy as np
import pythoncom

'''
	Classe para permitir cálculo de fluxo de potência
	de uma determinada rede de distribuição.
'''
class DSS(object):
	def __init__(self, dss_folder):
	
		pythoncom.CoInitialize()
	
		self.dss_folder = dss_folder	
		self.dssObj = win32com.client.Dispatch("OpenDSSEngine.DSS")				
		if not self.dssObj.Start(0):
			print("opendss nao inicializado")			
		self.dssText = self.dssObj.Text
		self.dssCircuit = self.dssObj.ActiveCircuit
		self.dssSolution = self.dssCircuit.Solution
		self.dssObj.ClearAll()
		self.dssText.Command = "set datapath=(" + self.dss_folder + ")"
		self.dssText.Command = "compile " + self.dss_folder + "\\master.dss"
		
		
	def solve_power_flow(self):
		self.dssSolution.Solve()
		self.dssText.Command = "show voltage ln nodes"
		self.dssText.Command = "show current elements"