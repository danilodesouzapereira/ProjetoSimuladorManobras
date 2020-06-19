import simuladorManobras
import sys
import sys
import gc
import json
import time

dados_simulacao = None	
if __name__ == '__main__':
	path_arq_parametros = ""

	if len(sys.argv) == 1:
		path_arq_parametros = "Z:\\SINAPgrid\\plataformasinap\\Tmp\\Bin\\Win64\\Dat\\DMS\\DadosSimulacoesManobra\\Executando\\ParametrosExecucao.txt"
	elif len(sys.argv) == 2:
		path_arq_parametros = sys.argv[1]

	file_json_param = open(path_arq_parametros, "r")
	json_param = json.loads(file_json_param.readlines()[0])
	dados_simulacao = json_param['dados_simulacao']
	simulador = simuladorManobras.SM(dados_simulacao)
	simulador.run_simulator()
	simulador.return_response()