import os
from bottle import Bottle, run, request, response, static_file, abort
from app import App, text_error
from modules.parse import is_allowed_path_info

bottle_app = Bottle()
dataApp = App()


def enable_cors(fn):
    def _enable_cors(*args, **kwargs):
        # set CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, ' \
                                                           + 'X-Requested-With, X-CSRF-Token'

        if request.method != 'OPTIONS':
            # actual request; reply with the actual response
            return fn(*args, **kwargs)

    return _enable_cors

@bottle_app.hook('before_request')
def strip_path():
    path = request.environ['PATH_INFO']
    # Reject anything outside the allowlist or containing traversal before the
    # validated value is written back for routing (path-injection guard, S2083).
    if not is_allowed_path_info(path):
        abort(400, 'Invalid request path')
    request.environ['PATH_INFO'] = path.rstrip('/')


@bottle_app.hook('after_request')
def enable_cors_after_request_hook():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'


@bottle_app.route('/')
def server_static(filename='index.html'):
    # root = os.path.dirname(__file__)
    return static_file(filename, root='.')


@bottle_app.route('/swagger.yaml')
def server_swagger_yaml(filename='swagger.yaml'):
    return static_file(filename, root='.')


@bottle_app.route('/swagger/<filepath:path>')
def server_swagger(filepath):
    return static_file(filepath, root='./swagger/')


@bottle_app.route('/cog')
@enable_cors
def cog():
    product = request.params.get('product')
    time_param = request.params.get('time')
    if not product or not time_param:
        return text_error(400, 'Required query parameters: product, time')
    return dataApp.serve_cog(product, time_param)


@bottle_app.route('/data')
@enable_cors
def get_data():
    model   = request.params.get('model')
    fmt     = request.params.get('format')
    dt      = request.params.get('time')
    product = request.params.get('product', 'winds')
    projwin = request.params.get('projwin')
    if not all([model, fmt, dt]):
        return text_error(400, 'Required query parameters: model, format, time')
    projwin = projwin.split(',') if projwin else None
    (output_format, data) = dataApp.get_data(model, fmt, dt, projwin, product)
    response.content_type = output_format
    return data


# Run several worker processes, each with a few threads. A fresh request ties up
# its slot for a few seconds, mostly waiting on a download or a wgrib2/gdal
# subprocess. Workers give us cores and crash isolation, so a native crash kills
# one worker that gunicorn restarts rather than the whole server. Threads let a
# worker keep serving other requests during those waits and share memory across
# them. The PNG rendering was moved off matplotlib's global state so it is safe to
# run on several threads at once. Set VELOSERVER_THREADS=1 to go back to pure
# workers. gunicorn switches to its threaded worker automatically when threads > 1.
_WORKERS = int(os.environ.get('VELOSERVER_WORKERS', 4))
_THREADS = int(os.environ.get('VELOSERVER_THREADS', 4))
_TIMEOUT = int(os.environ.get('VELOSERVER_TIMEOUT', 60))


def main():
    # production
    if (os.path.exists('/certs/key.pem') and os.path.exists('/certs/cert.pem')):
        run(bottle_app,
            host='0.0.0.0',
            port=8104,
            server='gunicorn',
            workers=_WORKERS,
            threads=_THREADS,
            timeout=_TIMEOUT,
            keyfile='/certs/key.pem',
            certfile='/certs/cert.pem')
    else:
        # dev mode
        run(bottle_app,
            host='0.0.0.0',
            port=8104,
            server='gunicorn',
            workers=_WORKERS,
            threads=_THREADS,
            timeout=_TIMEOUT,
            debug=True,
            reloader=True)


if __name__ == '__main__':
    main()
