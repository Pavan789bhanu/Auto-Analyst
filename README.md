
## **Prerequisites**

### 1. Tools and Dependencies
- **Python 3.10+**
- **pip** (Python package manager)
- **AWS CLI** configured with appropriate permissions
- An **AWS EC2 Instance** with:
  - Open ports in the Security Group (e.g., port `5000` for the application).
  - IAM role attached with access to S3 and Secrets Manager.

### 2. Environment Variables
Set up the following environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key.
- `AWS_REGION`: AWS region of your S3 bucket and Secrets Manager.

---

## **Application Setup**

### 1. Clone the Repository
SSH into your EC2 instance and clone the application repository:
```bash
ssh -i your-key.pem ec2-user@<public-ip>
git clone <repository-url>
cd <repository-folder>
```

### 2. Set Up the Virtual Environment
Create and activate a virtual environment:
```bash
python3 -m venv data-viz-env
source data-viz-env/bin/activate
```

### 3. Install Dependencies
Install all required Python libraries:
```bash
pip install -r requirements.txt
```

### 4. Configure Secrets Manager
Ensure your JWT secret is stored in AWS Secrets Manager:
1. Go to the **AWS Management Console** → **Secrets Manager**.
2. Create a new secret with the key-value pair:
   - Key: `SECRET_KEY`
   - Value: `your-jwt-secret-key`
3. Note the Secret ARN or ID for the application configuration.

---

## **Running the Application**

### 1. Start the Flask App (Development Mode)
For local testing, run the Flask application directly:
```bash
python3 app.py --host=0.0.0.0 --port=5000
```
Access the application via:
```
http://<public-ip>:5000
```

### 2. Run with Gunicorn (Production Mode)
Use Gunicorn for a production-grade WSGI server:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## **Environment Configuration**

### Set Environment Variables
Set required environment variables in your shell:
```bash
export OPENAI_API_KEY="your-openai-api-key"
export AWS_REGION="your-aws-region"
```

### Test OpenAI API Key
Ensure the OpenAI API is configured correctly:
```bash
python3 -c "import openai; openai.api_key = 'your-openai-api-key'; print('API Key Valid')"
```

---

## **License**
This project is licensed under the MIT License.

