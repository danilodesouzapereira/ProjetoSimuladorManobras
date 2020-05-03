import requests
import json

dados_simulacao = {
'local_dss':'C:\\Users\\danilo\\Desktop\\ProjetoSimuladorManobras\\Commwspython\\server\\sm_files\\dss_files',
'local_saida':'C:\\Users\\danilo\\Desktop',
'arestas':[
	{'u':1, 'v':2, 'w':1},
	{'u':2, 'v':3, 'w':1},
	{'u':0, 'v':6, 'w':1},
	{'u':6, 'v':7, 'w':1},
	{'u':0, 'v':4, 'w':1},
	{'u':4, 'v':5, 'w':1},
	{'u':2, 'v':7, 'w':1},
	{'u':3, 'v':7, 'w':1},
	{'u':2, 'v':5, 'w':1},
	{'u':3, 'v':5, 'w':1}
],
'arestas_iniciais':[
	{'u':0, 'v':4, 'w':1},
	{'u':0, 'v':6, 'w':1},
	{'u':4, 'v':5, 'w':1},
	{'u':6, 'v':7, 'w':1},
	{'u':1, 'v':2, 'w':1},
	{'u':2, 'v':3, 'w':1}
]
}
r1 = requests.post('http://127.0.0.1:5010/novasimulacao', json=dados_simulacao)
r2 = requests.get('http://127.0.0.1:5010/finalizar')