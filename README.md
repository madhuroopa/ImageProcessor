# ImageProcessor


## Application Overview:
The Image Processor application consists of a client, API, Image Processing Engine, and Image Repository. The API exposes the functionality of the Image Processor to the client, allowing the user to upload an image, specify the operations to be performed on the image, and retrieve the result. The client provides a UI the user to interact with the Image Processor and communicates with the API to make requests and retrieve the results or provide a JSON request of set of actions and retrieve the final image.
Operations:
•	Flip horizontal, vertical
•	Rotate +/- n degrees
•	Convert to grayscale
•	Resize
•	Generate a thumbnail
•	Rotate left
•	Rotate right
## Architectural Overview

## Components of Image Processor Application:

Client: This component is responsible for making API requests to the server, specifying the image to be processed and the desired operations.
API: This component exposes the functionality of the Image Processor to the client. The API receives requests from the client, performs the specified operations on the image, and returns the result to the client.
Image Processing Engine: This component is responsible for performing the actual image processing operations, such as flipping, rotating, converting to grayscale, resizing, and generating thumbnails.
Image Repository: This component stores the original and processed images.
Connectors: Connectors are used to connect the components and allow them to communicate with each other. For example, the API uses connectors to communicate with the Image Processing Engine and Image Repository.

## Architectural Style 

This whole system can be envisioned as the one which has to execute several steps to process the data. These steps can be configured using one architecture style “Pipe and Filter”. This is an architectural style, which consists of nodes or components known as filters which are connected by connectors known as pipes. The filters act on the data i.e., they perform data processing, whereas, pipes transport the data. Pipes represent channels which transport data using a particular protocol. for instance, HTTP or FTP etc. Filters represent processing units which act upon the input data and generate a result, which is fed to the output channel.
In this application filters act on image uploaded and transforms according to each operation where as pipes transfers the applied filter image to next stage for next image operation.

 ## Little Language
The "little language" for constructing image processing requests can be a JSON payload in a POST request to the API
API end point: http://{base_url}/process_image/img=?
HTTP Method: POST
JSON paylod :
{
"operations": [
"flip_horizontal",
"rotate_left",
“roatate_horizontal”
],
"resize": [width, height],
"thumbnail_size": [width, height]
}
HTTP Response:
	{
		Status : “Success”,
		Message: “Image transformation completed”
	}

The API will parse the "little language"(JSON input) and perform the specified operations accordingly  on the image. According to the example provided above, API would first flip the image horizontally, then left, then rotate horizontally, then resize the image according to the dimensions mentioned and finally create a thumbnail and store it in the Image Repository and send the Response to the client.

### Non Functional requirements:
Performance: The API design should be modular enough so that each and every 
transformation could take place accordingly and give a faster response (transformed image). 
Security: Maintaining a file repository for storing the uploaded, transformed, and final images 
without data loss. 
Usability: The user can easily understand and perform the image operations for the uploaded image. 



