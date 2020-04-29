import dss
import win32com.client


#===================================================================================#
'''
Class to assess fitness function of an individual of SSGA (Sequential Switching GA) 
'''
class AssessSSGAIndiv(object):
   def __init__(self, path_folder):
      self.dss = dss.DSS(path_folder) # DSS object for load flow simulations


