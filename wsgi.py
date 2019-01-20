from app.main import app
import os
if __name__ == "__main__":
    PORT = os.environ['PORT']
    PRODUCTION = os.environ.get("PRODUCTION") == 'True'   # Production should be set to "true" if the env variable is set
    app.run(host='0.0.0.0', debug=PRODUCTION, port=PORT) 