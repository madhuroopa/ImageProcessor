import base64
import os
import uuid
from typing import List, Optional

import requests
from PIL import Image
from apispec import APISpec
from flask import Flask, render_template, request, json, jsonify
from jsonrpc import JSONRPCResponseManager, dispatcher
from flask_jsonrpc import JSONRPC

from flask_swagger_ui import get_swaggerui_blueprint
import io
from flask_cors import CORS
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Image Processor"
    },

)

app.register_blueprint(swaggerui_blueprint)
jsonrpc = JSONRPC(app, "/", enable_web_browsable_api=True)

class ImageProcessor:
    @staticmethod
    @jsonrpc.method("ImageProcessor.process")
    def process(image_data: str, operations: List[dict]) -> dict:
        print("hello methid")
        try:
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            thumbnails = []
            for operation in operations:
                if operation['type'] == 'flip_horizontal':
                    image = image.transpose(Image.FLIP_LEFT_RIGHT)
                elif operation['type'] == 'flip_vertical':
                    image = image.transpose(Image.FLIP_TOP_BOTTOM)
                elif operation['type'] == 'rotate_left':
                    image = image.rotate(90, expand=True)
                elif operation['type'] == 'rotate_right':
                    image = image.rotate(-90, expand=True)
                elif operation['type'] == 'rotate':
                    angle = operation['angle']
                    image = image.rotate(-1 * angle, expand=True)
                elif operation['type'] == 'grayscale':
                    image = image.convert('L')
                elif operation['type'] == 'resize':
                    width = operation['width']
                    height = operation['height']
                    size = (width, height)
                    image = image.resize(size, resample=Image.Resampling.BICUBIC)
                elif operation['type'] == 'thumbnail':
                    thumbnail_image = image.copy()
                    thumbnail_image.thumbnail([300, 300], resample=0)
                    thumbnail_data = io.BytesIO()
                    thumbnail_image.save(thumbnail_data, format='JPEG')
                    thumbnail_str = base64.b64encode(thumbnail_data.getvalue()).decode('utf-8')
                    thumbnails.append(thumbnail_str)
            output_data = io.BytesIO()
            image.save(output_data, format='JPEG')
            # Setting the file position to the beginning allows you to read the entire contents of the file from the beginning.
            output_data.seek(0)
            output_str = base64.b64encode(output_data.getvalue()).decode('utf-8')
            result={
                "image": output_str,
                 "thumbnails": thumbnails
            }
        except Exception as e:
            # Log the error and return an error response
            print(f"Error processing image: {e}")
            result = {
                "error": str(e)
            }
        return result

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process_image', methods=['POST'])
def process_image():

    try:
        json_file = request.files['json_file']
        image_file = request.files['image_file']
        image_data = image_file.read()

        if json_file:
            json_data = json_file.read()
            # Parse the JSON data to extract the required parameters
            json_obj = json.loads(json_data)

            operations = json_obj['operations']
        else:
            operations = []
            operations_list=request.form.getlist('operation[]')
            print("hello")
            print(operations_list)
            if 'flip_horizontal' in operations_list:
                operations.append({'type': 'flip_horizontal'})
            if 'flip_vertical' in operations_list:
                operations.append({'type': 'flip_vertical'})
            if 'rotate_left' in operations_list:
                operations.append({'type': 'rotate_left'})
            if 'rotate_right' in operations_list:
                operations.append({'type': 'rotate_right'})
            if 'grayscale' in operations_list:
                operations.append({'type': 'grayscale'})

            if 'rotate' in operations_list:
                operations.append({'type': 'rotate', 'angle': int(request.form['angle'])})

            if 'resize' in operations_list:
                operations.append(
                    {'type': 'resize', 'width': int(request.form['width']), 'height': int(request.form['height'])})
            if 'thumbnail' in operations_list:
                operations.append({'type': 'thumbnail'})
        print(operations)

        rpc_request = {
            "jsonrpc": "2.0",
            "method": "ImageProcessor.process",
            "params": {
                "image_data": base64.b64encode(image_data).decode('utf-8'),
                "operations": operations

            },

            "id": 1,
        }
        print(rpc_request)
        r = requests.post('http://localhost:5000/', json=rpc_request)

        response = r.json()
        if r.status_code not in range(200, 300):
            return jsonify({"error": "Server error."}), r.status_code

        result = response.get('result')
        print(result)
        output_str = result["image"]
        thumbnails = result["thumbnails"]
        thumbnail_names=[]
        if result is not None:
            output_bytes = base64.b64decode(output_str)
            output_image = Image.open(io.BytesIO(output_bytes))
            output_name = str(uuid.uuid4()) + 'final.jpg'
            output_image.save(output_name)

            for i, thumbnail_str in enumerate(thumbnails):
                thumbnail_bytes = base64.b64decode(thumbnail_str)
                thumbnail_image = Image.open(io.BytesIO(thumbnail_bytes))
                thumbnail_name = str(uuid.uuid4()) + f'thumbnail_{i}.jpg'
                thumbnail_names.append(thumbnail_name)
                thumbnail_image.save(thumbnail_name,Format='JPG')

            output_result={
                "status": "success",
                "message": "Image processed successfully.",
                "result": {
                    "Final_Image_File_Name": output_name,
                    "Thumbnails":thumbnail_names,
                    "format": "JPEG"
                }
            }
            image_file.close()
            #print(f"{output_name} is the processed final image and {thumbnail_names}is the list of thumbnails created for the image according to the actions specified.")
            return jsonify(output_result),200
            #f"{output_name} is the processed final image and {thumbnail_names}is the list of thumbnails created for the image according to the actions specified."
        else:
            error = response.get('error')
            error.get('code')
            if error is not None:
                message = error.get('message')
                return f"Error: {message}"
            else:
                return "Unknown error"
    except Exception as e:
        #image_file.close()
        error= {"error": "Bad Request."}
        return jsonify(error),500



if __name__ == '__main__':
    app.run(debug=True)


