import os

true_options = ['y', 't', 'true', 'yes', '1']

# This holds some common config between client side of local platform(python scripts using the LocalPlatform) and
# server side(inside the container). For server side, this includes UI and workers

# Where we store data within our workers container
DATA_PATH = os.getenv("DATA_PATH", "/data")
# Our path to our API. This is used mainly by the client side apps(python code) so it is refering to how they would
# access it
API_PATH = os.getenv("API_PATH", 'http://localhost:5000/api')
# Database configuration for our workers
SQLALCHEMY_ECHO = (os.getenv('SQLALCHEMY_ECHO', '0').lower() in true_options)
SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI',
                                    "postgresql+psycopg2://idmtools:idmtools@postgres/idmtools")
