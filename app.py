from flask import Flask, request, jsonify, send_file
import wave
from main import script
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

@app.route('/process_audio', methods=['POST'])
def process_audio():
    print("okokokok")
    try:
        print("Request received: " + str(request.form))
        rel_path = request.form['audio_file']
        degree = int(request.form['degrees'])
        file_path = "/Users/wou/sideify3/" + rel_path
        print("rel " + rel_path)
        print("degree " + str(degree))

        # Check if file exists
        # with open(file_path, 'rb') as f:
        #     pass

        file = wave.open(file_path)
        print("found file")
        script(file_path, degree)
        return send_file("transformedouput.wav", mimetype='audio/wav')
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    except wave.Error as e:
        return jsonify({"error": "Error processing audio file: " + str(e)}), 400
    except Exception as e:
        print("exception")
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
