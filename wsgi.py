from app.main import app
import os
if __name__ == "__main__":
    PORT = os.environ['PORT']
    app.run(host='0.0.0.0', debug=True, port=PORT)