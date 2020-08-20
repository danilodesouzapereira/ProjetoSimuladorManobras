import simuladorManobras
import sys
import sys
import gc
import json
import time
from pathlib import Path

dados_simulacao = None	
if __name__ == '__main__':
	path_arq_parametros = ""

	if len(sys.argv) == 1:
		path_arq_parametros = "Z:\\SINAPgrid\\plataformasinap\\Tmp\\Bin\\Win64\\Dat\\DMS\\DadosSimulacoesManobra\\Executando\\ParametrosExecucao.txt"
		path_dat = "Z:\\SINAPgrid\\plataformasinap\\Tmp\\Bin\\Win64\\Dat\\"
	elif len(sys.argv) == 2:
		path_arq_parametros = sys.argv[1]
		pos_dat: int = path_arq_parametros.lower().find("dat")
		path_dat = path_arq_parametros[:pos_dat+4]

	print("Dados passados por parametro: " + str(len(sys.argv)))

	file_json_param = open(path_arq_parametros, "r")
	json_param = json.loads(file_json_param.readlines()[0])

	id_sm = json_param['id']  # Integer number to identify Switching Simulation request
	dados_diretorios = json_param['dados_diretorios']  # Data related to folders' paths
	dados_isolacao_defeito = json_param['dados_isolacao_defeito']  # Data related to switches to be opened to isolate the fault
	dados_simulacao = json_param['dados_simulacao']  # Data related to simulations settings

	simulador = simuladorManobras.SM(dados_diretorios, dados_isolacao_defeito, dados_simulacao)
	simulador.run_simulator()
	simulador.return_response(path_dat, id_sm)