from flask import Flask, jsonify, request
import simuladorManobras
import sys
import win32com.client
from win32com.client import makepy
import sys
import gc
import numpy as np

app = Flask(__name__)
dados_simulacao = None
	
#===================================================================================#
#              MÉTODOS PRINCIPAIS, CHAMADOS A PARTIR DE ENDPOINTS WS                #
#===================================================================================#
'''
	Endpoint para receber os dados de um pedido de simulação
	Sintaxe da chamada:
		requests.post('http://127.0.0.1:5010/novasimulacao', json=dados_simulacao)
'''
@app.route('/novasimulacao', methods=['POST'])
def nova_simulacao():
	dados_simulacao = request.get_json()
	simulador = simuladorManobras.SM(dados_simulacao)
	simulador.run_simulator()
	simulador.return_response()

	return jsonify({}), 200


'''	
	Endpoint para encerrar o WS server
'''
@app.route('/finalizar', methods=['GET'])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return ""

if __name__ == '__main__':
    app.run(port=5010, debug=True)