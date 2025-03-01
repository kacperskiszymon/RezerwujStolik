from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rezerwacje.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'tajny_klucz'

db = SQLAlchemy(app)

class Stolik(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Nie przechowujemy globalnego statusu stolika – sprawdzamy rezerwacje na dany termin

class Rezerwacja(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    imie = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    telefon = db.Column(db.String(20), nullable=False)
    liczba_osob = db.Column(db.Integer, nullable=False)
    stolik_id = db.Column(db.Integer, nullable=False)
    data_rezerwacji = db.Column(db.String(20), nullable=False)  # Format: YYYY-MM-DD
    godzina = db.Column(db.String(10), nullable=False)  # Format: HH:MM

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/rezerwuj', methods=['GET', 'POST'])
def rezerwuj():
    if request.method == 'POST':
        try:
            stolik_id = int(request.form['stolik_id'])
        except ValueError:
            return redirect(url_for('error'))
        imie = request.form['imie']
        email = request.form['email']
        telefon = request.form['telefon']
        liczba_osob = int(request.form['liczba_osob'])
        data = request.form['data']
        godzina = request.form['godzina']
        
        # Łączymy datę i godzinę w datetime
        try:
            chosen_dt = datetime.strptime(f"{data} {godzina}", "%Y-%m-%d %H:%M")
        except ValueError:
            return redirect(url_for('error'))
        reservation_duration = timedelta(hours=5)
        
        # Sprawdzamy, czy dla tego stolika i daty istnieje kolizja (różnica mniejsza niż 5 godzin)
        existing = Rezerwacja.query.filter_by(stolik_id=stolik_id, data_rezerwacji=data).all()
        conflict = False
        for res in existing:
            res_dt = datetime.strptime(f"{res.data_rezerwacji} {res.godzina}", "%Y-%m-%d %H:%M")
            if abs((chosen_dt - res_dt).total_seconds()) < reservation_duration.total_seconds():
                conflict = True
                break
        
        if conflict:
            return redirect(url_for('error'))
        
        new_reservation = Rezerwacja(
            imie=imie, email=email, telefon=telefon,
            liczba_osob=liczba_osob, stolik_id=stolik_id,
            data_rezerwacji=data, godzina=godzina
        )
        db.session.add(new_reservation)
        db.session.commit()
        return redirect(url_for('sukces'))
    
    # Dla GET – przygotowujemy listę stolików 1 do 10
    stoliki = [i for i in range(1, 11)]
    return render_template('rezerwuj.html', stoliki=stoliki)

@app.route('/sukces')
def sukces():
    return render_template('sukces.html')

@app.route('/error')
def error():
    return render_template('error.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Utwórz rekordy stolików, jeśli nie istnieją
        if Stolik.query.count() == 0:
            for i in range(1, 11):
                db.session.add(Stolik(id=i))
            db.session.commit()
    app.run(debug=True)
