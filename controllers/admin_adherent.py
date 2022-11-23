#! /usr/bin/python
# -*- coding:utf-8 -*-
import re
from flask import *
import datetime


from connexion_db import get_db

admin_adherent = Blueprint('admin_adherent', __name__,
                        template_folder='templates')

@admin_adherent.route('/admin/adherent/show')
def show_adherent():
    mycursor = get_db().cursor()
    sql = '''SELECT adherent.nom,
           adherent.adresse,
           adherent.date_paiement as datePaiement,
           adherent.id,
           COUNT(emprunt.adherent_id) as nbrEmprunt,
           DATE_ADD(adherent.date_paiement, INTERVAL 1 YEAR) as datePaiementFutur,
           IF(CURRENT_DATE()>DATE_ADD(adherent.date_paiement, INTERVAL 1 YEAR ),1,0) as retard,
           IF(CURRENT_DATE()>DATE_ADD(adherent.date_paiement, INTERVAL 11 MONTH),1,0) as retardProche
    FROM adherent
    LEFT JOIN emprunt on adherent.id = emprunt.adherent_id AND emprunt.date_retour IS NULL
    GROUP BY adherent.nom,
           adherent.adresse,
           adherent.date_paiement,adherent.id
    ORDER BY adherent.nom;'''
    mycursor.execute(sql)
    adherents = mycursor.fetchall()
    return render_template('admin/adherent/show_adherents.html', adherents=adherents)

@admin_adherent.route('/admin/adherent/add', methods=['GET'])
def add_adherent():
    erreurs=[]
    donnees=[]
    return render_template('admin/adherent/add_adherent.html', erreurs=erreurs, donnees=donnees)

@admin_adherent.route('/admin/adherent/add', methods=['POST'])
def valid_add_adherent():
    nom = request.form.get('nom', '')
    adresse = request.form.get('adresse', '')
    datePaiement = request.form.get('datePaiement', '')

    dto_data={'nom': nom, 'adresse': adresse, 'datePaiement': datePaiement}
    valid, errors, dto_data = validator_adherent(dto_data)
    if valid:
        datePaiement=dto_data['datePaiement_us']
        tuple_insert = (nom,adresse,datePaiement)
        mycursor = get_db().cursor()
        sql = '''INSERT INTO adherent(id, nom, adresse, date_paiement)
        VALUES (NULL, %s, %s, %s) '''
        mycursor.execute(sql, tuple_insert)
        get_db().commit()
        message = u'adherent ajouté , libellé :'+nom
        flash(message)
        return redirect('/admin/adherent/show')
    return render_template('admin/adherent/add_adherent.html', erreurs=errors, donnees=dto_data)

@admin_adherent.route('/admin/adherent/delete', methods=['GET'])
def delete_adherent():
    mycursor = get_db().cursor()
    id_adherent = request.args.get('id', '')
    if not(id_adherent and id_adherent.isnumeric()):
        abort("404","erreur id adherent")
    tuple_delete=(id_adherent)
    nb_emprunts = 0
    sql = '''SELECT COUNT(emprunt.exemplaire_id) as nb_emprunts FROM adherent
    LEFT JOIN emprunt ON adherent.id = emprunt.adherent_id
    WHERE adherent.id = %s
    GROUP BY adherent.id;'''
    mycursor.execute(sql, tuple_delete)
    res_nb_emprunts = mycursor.fetchone()
    if 'nb_emprunts' in res_nb_emprunts.keys():
        nb_emprunts=res_nb_emprunts['nb_emprunts']
    if nb_emprunts == 0 :
        sql = '''DELETE FROM adherent WHERE id = %s;'''
        mycursor.execute(sql, tuple_delete)
        get_db().commit()
        flash(u'adherent supprimé, id: ' + id_adherent)
    else :
        flash(u'suppression impossible, il faut supprimer  : ' + str(nb_emprunts) + u' emprunt(s) de cet adherent')
    return redirect('/admin/adherent/show')

@admin_adherent.route('/admin/adherent/edit', methods=['GET'])
def edit_adherent():
    id_adherent = request.args.get('id', '')
    mycursor = get_db().cursor()
    sql = '''SELECT * FROM adherent
    WHERE id = %s;'''
    mycursor.execute(sql, (id_adherent,))
    adherent = mycursor.fetchone()
    if adherent['date_paiement']:
        adherent['datePaiement']=adherent['date_paiement'].strftime("%d/%m/%Y")
    erreurs=[]
    return render_template('admin/adherent/edit_adherent.html', donnees=adherent, erreurs=erreurs)

@admin_adherent.route('/admin/adherent/edit', methods=['POST'])
def valid_edit_adherent():
    id = request.form.get('id', '')
    nom = request.form.get('nom', '')
    adresse = request.form.get('adresse', '')
    datePaiement = request.form.get('datePaiement', '')
    dto_data={'nom': nom, 'adresse': adresse, 'datePaiement': datePaiement, 'id':id}
    valid, errors, dto_data = validator_adherent(dto_data)
    if valid:
        datePaiement=dto_data['datePaiement_us']
        tuple_update = (nom,adresse,datePaiement,id)
        mycursor = get_db().cursor()
        sql = '''UPDATE  adherent SET nom=%s, adresse=%s, date_paiement = %s WHERE id = %s;'''
        mycursor.execute(sql, tuple_update)
        get_db().commit()
        flash(u'adherent modifié, id: ' + id + " nom : " + nom)
        return redirect('/admin/adherent/show')
    return render_template('admin/adherent/edit_adherent.html', erreurs=errors, donnees=dto_data)

def validator_adherent(data):
    valid = True
    errors = dict()

    if 'id' in data.keys():
        if not data['id'].isdecimal():
           errors['id'] = 'type id incorrect'
           valid= False

    if not re.match(r'\w{2,}', data['nom']):
        errors['nom'] = "Le Nom doit avoir au moins deux caractères"
        valid = False

    try:
        datetime.datetime.strptime(data['datePaiement'], '%d/%m/%Y')
    except ValueError:
        errors['datePaiement'] = "Date n'est pas valide format:%d/%m/%Y"
        valid = False
    else:
        data['datePaiement_us'] = datetime.datetime.strptime(data['datePaiement'], "%d/%m/%Y").strftime("%Y-%m-%d")
    return (valid, errors, data)






