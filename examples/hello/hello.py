import os

def hello(event, context):
    greeting = os.environ.get('GREETING', 'Hello')
    target = event['target']
    return {'greeting': '{}, {}!'.format(greeting, target)}
