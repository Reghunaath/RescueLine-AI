from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    print("hi")
    print(data)
    return jsonify({'status': 'received'}), 200

if __name__ == '__main__':
    app.run(port=5001)