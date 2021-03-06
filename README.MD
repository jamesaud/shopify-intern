# Purpose 

Flask microservice for the shopify internship challenge. Design a REST API that functions as a minimal online store. 

# Development tools

Developed in flask. Flask_rest_plus is used (https://flask-restplus.readthedocs.io/en/stable/) for optimal Swagger.io integration (https://flask-restplus.readthedocs.io/en/stable/).

MongoDB is used for the database because it facilitated rapid development.

Docker used for development.

# Getting started

Clone the repository, and simply run the command 

`docker-compose up`

The webserver should be running on localhost:8000

Change the default settings in the docker-compose.yml file environment variables.

The backend code is contained in a single file, app/main.py https://github.com/jamesaud/shopify-intern/blob/master/app/main.py

# Production

Heroku is used for production.

It is necessary setup MongoDB on Heroku (mLab MongoDB free plan used). The "MONGODB_URI" config variable (environment variable) will be added automatically on Heroku.

Simply push the code to Heroku via

`git push heroku master`

or setup automatic deployments with Github.

# Live Example

Swagger API (might take a second to load on cold boot on Heroku): http://shopify-internship.herokuapp.com/#/default

Please note to see the documentation it needs to be HTTP and not HTTPS. This is due to a CORS issue over HTTPS.

However, the API itself is fully functional over HTTPS.

Guide at:
https://drive.google.com/open?id=1zGQyks5-sYmzQuZUz87tN5QIrvChMKAVEsyIHddTRO8
