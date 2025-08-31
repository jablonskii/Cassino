Digite no terminal antes de rodar o código:
pip install -r requirements.txt

Para rodar o código:
python app.py

Se der erro ao conectar com a base de dados apague o game.db e digite no terminal:
python -m flask shell
from app import db
db.create_all()
exit()

