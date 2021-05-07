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
	path_chv_sem_manobra_anel = ""
	id_plano = -1
	self_healing = 0    # 0: no, 1: yes
	if len(sys.argv) == 1:
		path_arq_parametros = "Z:\\SINAPgrid\\PlataformaSinap\\Tmp\\Bin\\Win64\\Dat\\DMS\\DadosSimulacoesManobra\\Executando\\ParametrosExecucao.txt"
		path_chv_sem_manobra_anel = "Z:\\SINAPgrid\\PlataformaSinap\\Tmp\\Bin\\Win64\\Dat\\DMS\\DadosSimulacoesManobra\\Executando\\ChavesSemManobraAnel.txt"
		path_dat = "Z:\\SINAPgrid\\PlataformaSinap\\Tmp\\Bin\\Win64\\Dat\\"
		id_plano = 1
		self_healing = 0  # 0: no, 1: yes
	elif len(sys.argv) == 2:
		path_arq_parametros = sys.argv[1]
		pos_dat: int = path_arq_parametros.lower().find("dat")
		path_dat = path_arq_parametros[:pos_dat+4]
		pos_executando: int = path_arq_parametros.lower().find("executando")
		path_chv_sem_manobra_anel = path_arq_parametros[:pos_executando+11] + "ChavesSemManobraAnel.txt"
		id_plano = 1
		self_healing = 0   # 0: no, 1: yes
	elif len(sys.argv) == 3:
		path_arq_parametros = sys.argv[1]
		pos_dat: int = path_arq_parametros.lower().find("dat")
		path_dat = path_arq_parametros[:pos_dat+4]
		pos_executando: int = path_arq_parametros.lower().find("executando")
		path_chv_sem_manobra_anel = path_arq_parametros[:pos_executando+11] + "ChavesSemManobraAnel.txt"
		id_plano = int(sys.argv[2])
		self_healing = 0  # 0: no, 1: yes
	elif len(sys.argv) == 4:
		path_arq_parametros = sys.argv[1]
		pos_dat: int = path_arq_parametros.lower().find("dat")
		path_dat = path_arq_parametros[:pos_dat+4]
		pos_executando: int = path_arq_parametros.lower().find("executando")
		path_chv_sem_manobra_anel = path_arq_parametros[:pos_executando+11] + "ChavesSemManobraAnel.txt"
		id_plano = int(sys.argv[2])
		self_healing = int(sys.argv[3])  # 0: no, 1: yes

	file_json_param = open(path_arq_parametros, "r")
	json_param = json.loads(file_json_param.readlines()[0])

	id_sm = int(json_param['id'])  # Integer number to identify Switching Simulation request
	dados_diretorios = json_param['dados_diretorios']  # Data related to folders' paths
	dados_isolacao_defeito = json_param['dados_isolacao_defeito']  # Data related to switches to be opened to isolate the fault
	dados_simulacao = json_param['dados_simulacao']  # Data related to simulations settings

	simulador = simuladorManobras.SM(dados_diretorios, dados_isolacao_defeito, dados_simulacao, path_chv_sem_manobra_anel)
	simulador.run_simulator(self_healing)
	simulador.return_response(path_dat, id_sm, id_plano, self_healing)