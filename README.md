# ImageProAPI

**ImageProAPI** is an Image Processing API designed to allow clients to upload images and apply various transformations through simple RESTful endpoints. The API supports operations such as image resizing, format conversion, filter application, and metadata extraction. Built with Django, it focuses on performance, security, and scalability, making it suitable for integration into web, mobile, or data-processing applications.

---

## Features

- Image processing with Pillow (compression, filters, resize, and format conversion)  
- Asynchronous image processing using Celery  
- Automatic deletion of images after download expiry or inactivity  
- JWT-based authentication for secure API access  

---

## Setup Instructions

1. Clone the repository:  
   ```bash
   git clone https://github.com/JhayceeCodes/ImageProAPI
   cd ImageProAPI 
   ```

2. Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    venv\Scripts\activate     # Windows
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4. Configure environment variables (if any, e.g., Redis URL, Django secret key).

5. Run migrations:
    ```bash
    python manage.py migrate
    ```
6. Start the development server
    ```bash
    python manage.py runserver
    ```

7. Start Celery worker (ensure Redis is running):
    ```bash
    celery -A <project_name> worker -l info
    ```

8. Start Celery beat (for scheduled tasks like auto-deletion):
    ```bash
    celery -A <project_name> beat -l info
    ```

Future plans: Support Docker for easier setup and deployment.

## API Endpoints
### Authentication
| Method | Endpoint                            | Description       |
| ------ | ----------------------------------- | ----------------- |
| POST   | `/accounts/register/`               | Register a new user   |
| POST   | `/accounts/login/`               | Login and obtain access & refresh token   |
| POST   | `/accounts/refresh/`                  | Refresh access token   |
| POST   | `/account/logout/`                  | Logout and blacklist refresh token  |

### Image Operations
| Method | Endpoint                            | Description       |
| ------ | ----------------------------------- | ----------------- |
| POST   | `/api/images/`               | Upload a new image with operations (as JSON).   |
| POST   | `/api/images/{id}/`               | Retrieve image details including status and download URL (if ready).   |
| POST   | `/api/images/{id}download/`                  | Download the processed image. Only available if status = completed.
   |

## Usage Instructions

- Upload an image via `/api/images/` endpoint along with a JSON array of operations: resize, compress, filter, or convert.

-  Access the image details via `/api/images/{id}/` endpoint.

- Once the processing status is "completed", a download link becomes available.

- Download the processed image via `/api/images/{id}/download/`.

## Celery Tasks and Background Processing

- Image Processing: All image transformations are handled asynchronously by Celery workers to prevent blocking the API.

- Automatic Cleanup: Expired images are automatically deleted via a scheduled Celery task.

- Redis is used as the Celery broker.


## Notes on Expiry

- Images are automatically deleted 5 minutes after the first download.

- If an image is not downloaded at all, it is automatically deleted after 24 hours.


## Technologies Used

- Django

- Django REST Framework

- Pillow

- Celery

- Redis


