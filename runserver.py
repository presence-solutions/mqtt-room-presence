from server.server import socketio, app

socketio.run(app, host='0.0.0.0', port=5000, use_reloader=False, debug=True)
