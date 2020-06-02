import simuladorManobras
import sys
import sys
import gc
import json
import time

dados_simulacao = None	
if __name__ == '__main__':

	path_arq_parametros = sys.argv[1]	
	file_json_param = open(path_arq_parametros, "r")	
	json_param = file_json_param.readlines()[0]
	json_param = json.loads(json_param)	
	dados_simulacao = json_param['dados_simulacao']		
	simulador = simuladorManobras.SM(dados_simulacao)	
	simulador.run_simulator()		
	simulador.return_response()	