import os

from flask import Flask, request, jsonify, flash, render_template
import io
from PIL import Image
from werkzeug.utils import secure_filename

app = Flask(__name__)
ROOT_DIR =  os.path.dirname(os.path.abspath(__file__))


UPLOAD_FOLDER = os.path.join(ROOT_DIR, 'static/images/')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif','bmp'}
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
@app.route("/")
def main():
    return render_template("index.html")
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload", methods=['POST'])
def upload_file():
    filename = ''
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            resp = jsonify({'message': 'No file part in the request'})
            resp.status_code = 400

            return resp

        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            resp = jsonify({'message': 'No file selected for uploading'})
            resp.status_code = 400
            return resp
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            print(f"{filename} uploaded")
            resp = jsonify({'message': 'File successfully uploaded'})
            resp.status_code = 201
            return render_template("image_editor.html",message="File successfully uploaded",image_name=filename)
        else:
            resp = jsonify({'message': 'Allowed file types are png, jpg, jpeg, gif'})
            resp.status_code = 400
            return resp

@app.route('/image_process', methods=['POST'])
def process_image():
    # Get binary image file from request
    ##image_file = request.files.get('image')
    ##image = Image.open(io.BytesIO(image_file.read()))
    ##filename = request.form['image']
    filename = request.json.get('filename')
    target = os.path.join(ROOT_DIR, 'static/images')
    destination = "/".join([target, filename])
    image = Image.open(destination)
    # Get operations from JSON payload
    operations = request.json.get('operations', [])
    resize = request.json.get('resize', None)
    thumbnail_size = request.json.get('thumbnail_size', None)
    rotate=request.json.get('rotate_angle',None)

    # Apply operations
    for op in operations:
        if op == 'flip_horizontal':
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
        elif op == 'flip_vertical':
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
        elif op == 'rotate_left':
            image = image.rotate(-90)
        elif op == 'rotate_right':
            image = image.rotate(90)
        elif op == 'grayscale':
            image = image.convert('L')
    if rotate:
        image=image.rotate(-1*int(rotate))

    # Resize image if requested
    if resize:
        image = image.resize(resize)

    # Generate thumbnail if requested
    if thumbnail_size:
        image.thumbnail(thumbnail_size)
    destination = "/".join([target, 'temp.png'])
    if os.path.isfile(destination):
        os.remove(destination)
    image.save(destination)
    resp = jsonify({'message': 'image successfully saved'})
    resp.status_code = 201
    # Return processed image as binary file
    ##image_io = io.BytesIO()
    #image.save(image_io, 'JPEG')
    #image_io.seek(0)
    #return send_file(image_io, mimetype='image/jpeg')
    return resp

if __name__ == '__main__':
    app.run()
