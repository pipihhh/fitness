from flask_script import Manager
from apps.main import create_app


if __name__ == '__main__':
    app = create_app()
    app = Manager(app)
    app.run()
