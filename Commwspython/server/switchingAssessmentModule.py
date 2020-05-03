import dss
import numpy as np
import converterGraphDSSModule

#===================================================================================#
'''
Class to assess fitness function of an individual of SSGA (Sequential Switching GA) 
'''
class AssessSSGAIndiv(object):
   def __init__(self, path_folder):
      xml_file_path = path_folder + "\\..\\GrafoAlimentadores.xml"
      conv = converterGraphDSSModule.ConversorGrafoDSS(xml_file_path)
      feeders_info = conv.read_xml_feeder_protections()
      self.dss = dss.DSS(path_folder) # DSS object for load flow simulations
      self.dss.initialize(feeders_info)


   ''' 
   Method to assess load flow-based merit index
   '''
   def load_flow_merit_index(self, dict_sw_states, sw_changes):
      # set initial conditions (right after fault clearing)
      self.dss.set_initial_sw_states(dict_sw_states)

      # initial load flow
      self.dss.solve_power_flow(show_results=False, plot_circuit=False)

      # gets all 3-phase currents
      mod_curr_initial = self.dss.get_currents_abs()

      # closes or opens switches
      self.dss.change_sw_states(sw_changes)

      # load flow after switchings
      self.dss.solve_power_flow(show_results=False, plot_circuit=False)

      # reverts switching
      self.dss.restore_sw_states(sw_changes)

      # gets all 3-phase currents. Format: [[ia_1, ib_1, ic_1] , [ia_2, ib_2, ic_2] , ... ]
      mod_curr_final = self.dss.get_currents_abs()

      mod_curr_max = [40., 50., 50.]
      LF_MI = self.compute_load_flow_merit_index(mod_curr_initial, mod_curr_final, mod_curr_max)

      return LF_MI


   '''
   Method to compute MI (merit index) related to load flow
   '''
   def compute_load_flow_merit_index(self, mod_curr_initial, mod_curr_final, curr_capacities):
      # margin related to base condition (mod_curr_initial)
      M_b = 0.0 ; w_b_tot = 0.0
      for i in range(len(mod_curr_initial)):
         I_capacity = curr_capacities[i] ; currents = mod_curr_initial[i]
         for ph in range(len(currents)):
            if currents[ph] == 0.0: continue
            diff = I_capacity - currents[ph]
            if diff >= 0.:
               M_b += 1.0 * diff ; w_b_tot += 1.0
            else:
               M_b += 3.0 * diff; w_b_tot += 3.0
      if w_b_tot > 0: M_b /= w_b_tot
      else: M_b = 0.0

      # margin related to final condition (mod_curr_final)
      M = 0.0 ; w_tot = 0.0
      for i in range(len(mod_curr_final)):
         I_capacity = curr_capacities[i] ; currents = mod_curr_final[i]
         for ph in range(len(currents)):
            if currents[ph] == 0.0: continue
            diff = I_capacity - currents[ph]
            if diff >= 0.:
               M += 1.0 * diff ; w_tot += 1.0
            else:
               M += 3.0 * diff ; w_tot += 3.0
      if w_tot > 0: M /= w_tot
      else: M = 0.0

      # compute margin difference in pu (related to base case)
      # Obs: low margin reduction means better solution
      dM_pu = (M_b - M) / M_b

      return dM_pu