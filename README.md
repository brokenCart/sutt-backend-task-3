# Setup Instructions
```
git clone https://github.com/brokenCart/sutt-backend-task-3.git
cd sutt-backend-task-3
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="add-your-secret-key-here"
export DEBUG="true/false (default is false)"
export ALLOWED_HOSTS="add hosts separated by space"
export DATABASE_URL="default is sqlite database, you can leave this line"
export GOOGLE_CLIENT_ID="add google oauth client id"
export GOOGLE_SECRET="add google oauth secret"
python manage.py migrate
```
