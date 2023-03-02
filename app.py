import base64
import os
import uuid
from typing import List, Optional

import requests
from PIL import Image
from apispec import APISpec
from flask import Flask, render_template, request, json
from jsonrpc import JSONRPCResponseManager, dispatcher
from flask_jsonrpc import JSONRPC

from flask_swagger_ui import get_swaggerui_blueprint
import io
from flask_cors import CORS
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Test application"
    },
    # oauth_config={  # OAuth config. See https://github.com/swagger-api/swagger-ui#oauth2-configuration .
    #    'clientId': "your-client-id",
    #    'clientSecret': "your-client-secret-if-required",
    #    'realm': "your-realms",
    #    'appName': "your-app-name",
    #    'scopeSeparator': " ",
    #    'additionalQueryStringParams': {'test': "hello"}
    # }
)

app.register_blueprint(swaggerui_blueprint)
jsonrpc = JSONRPC(app, "/", enable_web_browsable_api=True)

class ImageProcessor:
    @staticmethod
    @jsonrpc.method("ImageProcessor.process")
    def process(image_data: str, operations: List[dict]) -> str:
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
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

                thumbnail_image.thumbnail([300,300],resample=0)
                thumbnail_name = str(uuid.uuid4()) + 'Thumbnail.jpg'  # generate random name for the output image
                thumbnail_image.save(thumbnail_name)

        output_data = io.BytesIO()
        output_name = str(uuid.uuid4()) + 'final.jpg'  # generate random name for the output image
        image.save(output_name)

        output_data.seek(0)
        output_str = base64.b64encode(output_data.getvalue()).decode('utf-8')
        return "Success"

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process_image', methods=['POST'])
def process_image():

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
        operations_list=request.form.getlist('operations[]')
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
        if 'thumbnail' in operations_list:
            operations.append({'type': 'thumbnail'})
        if 'rotate' in operations_list:
            operations.append({'type': 'rotate', 'angle': int(request.form['angle'])})
        if 'resize' in operations_list:
            operations.append(
                {'type': 'resize', 'width': int(request.form['width']), 'height': int(request.form['height'])})




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
    print(response)
    result = response.get('result')
    print(result)
    if result=="Success":
        return result
    else:
        error = response.get('error')
        if error is not None:
            message = error.get('message')
            return f"Error: {message}"
        else:
            return "Unknown error"


if __name__ == '__main__':
    app.run(debug=True)
