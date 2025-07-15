# Gunicorn config file

# Worker processes
workers = 4
worker_class = 'sync'

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'debug'

# Server socket
# Dockerコンテナ内で実行するため、0.0.0.0でリッスンします
bind = '0.0.0.0:5000'

# その他
# デーモン化はしない（Dockerがプロセスを管理するため）
daemon = False
