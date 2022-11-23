from app_orm import db

class Oeuvre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(255), nullable=False)
    dateParution = db.Column(db.Date, nullable=False)
    photo = db.Column(db.String(255), nullable=False)
    prix = db.Column(db.Numeric(13, 4), nullable=False)
    auteur_id = db.Column(db.Integer, db.ForeignKey('auteur.id'))
    auteur = db.relationship('Auteur', back_populates='oeuvres')

    def __repr__(self):
        return f'<Oeuvre {self.id}>'