from flask import Flask, jsonify, request
import simuladorManobras
import sys
import win32com.client
from win32com.client import makepy
import sys
import gc
import numpy as np


app = Flask(__name__)

devs = [
    {
        'id': 1,
        'name': 'Rafael Marques',
        'lang': 'python'
    },
    {
        'id': 2,
        'name': 'Robert Hrosher',
        'lang': 'python'
    },
    {
        'id': 3,
        'name': 'John Delare',
        'lang': 'python'
    },
    {
        'id': 4,
        'name': 'John Doe',
        'lang': 'node'
    }
]

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
	dados_simulacao = request.get_json() # pega os dados das arestas
	simulador = simuladorManobras.SM(dados_simulacao)
	simulador.run_simulator()
	#simulador.print_data()
	#simulador.print_output()
	#simulador = None
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

#===================================================================================#
#                        MÉTODOS PARA TESTES DE SERVIÇOS WS REST                    #
#===================================================================================#
	
	
@app.route('/devs', methods=['GET'])
def home():
    return jsonify(devs), 200


@app.route('/devs/<string:lang>', methods=['GET'])
def devs_per_lang(lang):
    devs_per_lang = [dev for dev in devs if dev['lang'] == lang]
    return jsonify(devs_per_lang), 200


@app.route('/devs/<int:id>', methods=['PUT'])
def change_lang(id):
    for dev in devs:
        if dev['id'] == id:
            dev['lang'] = request.get_json().get('lang')

            return jsonify(dev), 200

    return jsonify({'error': 'dev not found'}), 404


@app.route('/devs/<int:id>', methods=['GET'])
def devs_per_id(id):
    for dev in devs:
        if dev['id'] == id:
            return jsonify(dev), 200

    return jsonify({'error': 'not found'}), 404


@app.route('/devs', methods=['POST'])
def save_dev():
    data = request.get_json()
    devs.append(data)
    
    return jsonify(data), 201


@app.route('/devs/<int:id>', methods=['DELETE'])
def remove_dev(id):
    index = id - 1
    del devs[index]

    return jsonify({'message': 'Dev is no longer alive'}), 200


if __name__ == '__main__':
    app.run(port=5010, debug=True)