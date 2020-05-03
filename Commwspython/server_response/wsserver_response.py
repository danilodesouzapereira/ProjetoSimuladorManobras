from flask import Flask, jsonify, request
import gc

app = Flask(__name__)


'''
	Endpoint para receber os dados de resposta da simulação de manobras, emulando
	o WS do front-end. Sintaxe da chamada:
		requests.post('http://127.0.0.1:5011/retornosimulacao', json=dados_simulacao)
'''
@app.route('/retornosimulacao', methods=['POST'])
def nova_simulacao():
	dados_simulacao = request.get_json() # pega os dados das arestas
	print("Retorno recebido:")
	print(dados_simulacao)

	return jsonify({}), 200


if __name__ == '__main__':
    app.run(port=5011, debug=True)