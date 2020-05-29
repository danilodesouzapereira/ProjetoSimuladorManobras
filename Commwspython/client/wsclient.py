import requests
import json

dados_simulacao = {
'local_dss':'C:\\Users\\danilo\\Desktop\\ProjetoSimuladorManobras\\Commwspython\\server\\sm_files\\dss_files',
'local_saida':'C:\\Users\\danilo\\Desktop',
'av_conf_indice_merito':{'k_load_flow':1.0, 'k_crew_displacement':1.0, 'k_outage_duration':1.0, 'k_number_switching':1.0},
'chave_partida':'cf10',
'conf_ag_grafo':{'num_geracoes':20, 'num_individuos':20, 'pc':0.90, 'pm':0.2},
'conf_ag_chv_otimo':{'num_geracoes':2, 'num_individuos':3, 'pc':0.90, 'pm':0.1, 'min_porc_fitness':5.0}
}
r1 = requests.post('http://127.0.0.1:5010/novasimulacao', json=dados_simulacao)
r2 = requests.get('http://127.0.0.1:5010/finalizar')