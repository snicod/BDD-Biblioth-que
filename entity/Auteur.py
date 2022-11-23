from app_orm import db


class Auteur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prenom = db.Column(db.String(255), nullable=False)
    nom = db.Column(db.String(255), nullable=False)
    oeuvres = db.relationship('Oeuvre', back_populates='auteur')

    def __repr__(self):
        return f'<Auteur {self.id}>'