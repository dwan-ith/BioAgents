from server import app

# Vercel needs the Flask app to be available as 'app' or 'handler'
# Since we already have 'app' in server.py, we just import it.
# We can also add a prefix if we want, but it's easier to handle
# routing in vercel.json.
