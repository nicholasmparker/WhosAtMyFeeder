import os
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = '0'

import yaml
from webui import app

def load_config():
    with open('./config/config.yml', 'r') as config_file:
        return yaml.safe_load(config_file)

if __name__ == '__main__':
    config = load_config()
    
    import gunicorn.app.base

    class StandaloneApplication(gunicorn.app.base.BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            for key, value in self.options.items():
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    options = {
        'bind': f"{config['webui']['host']}:{config['webui']['port']}",
        'workers': 1,
        'worker_class': 'sync',
        'reload': False,
        'preload_app': True,
        'accesslog': '-',  # Log to stdout
        'errorlog': '-'    # Log to stdout
    }

    print(f"Starting Gunicorn on {options['bind']}", flush=True)
    StandaloneApplication(app, options).run()
