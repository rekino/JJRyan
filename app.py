from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/assign', methods=['POST'])
def assign():
    try:
        data = request.get_json()
        engineer = data.get('engineer')
        inspection = data.get('inspection')
        # Process the engineer and inspection data as needed
        # ...

        # Return an HTTP 200 response with the message 'OK'
        return jsonify({'message': 'OK'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
