def hello(event, context):
    target = event['target']
    return {'greeting': 'Hello, {}!'.format(target)}

