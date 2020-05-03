import requests
import json

dados_simulacao = {
'local_dss':'C:\\Users\\danilo\\Desktop\\ProjetoSimuladorManobras\\Commwspython\\server\\sm_files\\dss_files',
'local_saida':'C:\\Users\\danilo\\Desktop',
}
r1 = requests.post('http://127.0.0.1:5010/novasimulacao', json=dados_simulacao)
r2 = requests.get('http://127.0.0.1:5010/finalizar')