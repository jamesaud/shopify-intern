# Purpose 

Flask microservice for the shopify internship challenge. Design a REST API that functions as a minimal online store. 

# Development tools

Developed in flask with docker. Flask_rest_plus is used (https://flask-restplus.readthedocs.io/en/stable/) for optimal Swagger.io integration (https://flask-restplus.readthedocs.io/en/stable/).

MongoDB is used for the database because it facilitated rapid development.

Docker used for development.

# Getting started

Clone the repository, and simply run the command 

`docker-compose up`

The webserver should be running on localhost:8000

# Production

It is necessary setup MongoDB on Heroku (mLab MongoDB free plan used). The "MONGODB_URI" config variable (environment variable) will be added automatically on Heroku.

Simply push the code to Heroku via

`git push heroku master`

or setup automatic deployments with via Github.

