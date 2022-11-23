#! /usr/bin/python
# -*- coding:utf-8 -*-
import re
from flask import *
import datetime

import os

from connexion_db import get_db

admin_oeuvre = Blueprint('admin_oeuvre', __name__,
                        template_folder='templates')

@admin_oeuvre.route('/admin/oeuvre/show')
def show_oeuvre():
    mycursor = get_db().cursor()
    sql = '''SELECT oeuvre.titre,
           oeuvre.id,
           IF(oeuvre.date_parution IS NULL, '', oeuvre.date_parution) as date_parution_en,
           oeuvre.photo,
           auteur.nom,
           COUNT(exemplaire.id) as nbExemplaire,
           COUNT(E2.id) as nombreDispo,
           CONCAT(LPAD(DAY(oeuvre.date_parution), 2, '0'),'/',LPAD(MONTH(oeuvre.date_parution), 2, '0'),'/',LPAD(YEAR(oeuvre.date_parution), 4, '0')) as date_parution
    FROM oeuvre
    INNER JOIN auteur ON oeuvre.auteur_id = auteur.id
    LEFT JOIN exemplaire ON oeuvre.id = exemplaire.oeuvre_id
    LEFT JOIN exemplaire as E2 ON E2.id = exemplaire.id
        AND E2.id NOT IN (SELECT emprunt.exemplaire_id FROM emprunt WHERE emprunt.date_retour IS NULL)
    GROUP BY oeuvre.id
    ORDER BY auteur.nom, oeuvre.titre;'''
    mycursor.execute(sql)
    oeuvres = mycursor.fetchall()
    return render_template('admin/oeuvre/show_oeuvre.html', oeuvres=oeuvres)

@admin_oeuvre.route('/admin/oeuvre/add', methods=['GET'])
def add_oeuvre():
    mycursor = get_db().cursor()
    sql = '''SELECT auteur.nom, auteur.id FROM auteur
                ORDER BY auteur.nom;'''
    mycursor.execute(sql)
    auteurs = mycursor.fetchall()
    return render_template('admin/oeuvre/add_oeuvre.html', auteurs=auteurs, donnees=[], erreurs=[])

@admin_oeuvre.route('/admin/oeuvre/add', methods=['POST'])
def valid_add_oeuvre():
    mycursor = get_db().cursor()
    titre = request.form.get('titre', '')
    dateParution = request.form.get('dateParution', '')
    idAuteur = request.form.get('idAuteur', '')
    photo = request.form.get('photo', '')

    dto_data={'titre': titre, 'photo': photo, 'dateParution': dateParution, 'idAuteur': idAuteur}
    valid, errors, dto_data = validator_oeuvre(dto_data)
    if valid:
        dateParution = dto_data['dateParution_us']
        tuple_insert = (titre,dateParution,photo,idAuteur)
        sql = '''INSERT INTO oeuvre(titre, date_parution, photo, auteur_id) VALUES
                (%s, %s, %s, %s);'''
        mycursor.execute(sql, tuple_insert)
        get_db().commit()
        print(u'oeuvre ajouté , nom: ', titre, ' - idAuteur:', idAuteur, ' - photo:', photo)
        message = u'oeuvre ajouté , nom:'+titre + '- idAuteur:' + idAuteur + ' - photo:' + photo
        flash(message)
        return redirect('/admin/oeuvre/show')
    sql = '''SELECT auteur.nom, auteur.id FROM auteur
                ORDER BY auteur.nom;'''
    mycursor.execute(sql)
    auteurs = mycursor.fetchall()
    return render_template('admin/oeuvre/add_oeuvre.html', auteurs=auteurs, erreurs=errors, donnees=dto_data)

@admin_oeuvre.route('/admin/oeuvre/delete', methods=['GET'])
def delete_oeuvre():
    mycursor = get_db().cursor()
    id = request.args.get('id', '')
    if not(id and id.isnumeric()):
        abort("404","erreur id oeuvre")
    tuple_delete = (id,)

    nb_exemplaires = 0
    sql = '''SELECT COUNT(exemplaire.id) AS nb_exemplaires FROM oeuvre
            LEFT JOIN exemplaire ON oeuvre.id = exemplaire.oeuvre_id
            WHERE oeuvre.id = %s;'''
    mycursor.execute(sql, tuple_delete)
    res_nb_exemplaires = mycursor.fetchone()
    if 'nb_exemplaires' in res_nb_exemplaires.keys():
        nb_exemplaires=res_nb_exemplaires['nb_exemplaires']
    if nb_exemplaires == 0 :
        sql = '''DELETE FROM oeuvre WHERE id = %s;'''
        mycursor.execute(sql, tuple_delete)
        get_db().commit()
        flash(u'oeuvre supprimée, id: ' + id)
    else :
        flash(u'suppression impossible, il faut supprimer  : ' + str(nb_exemplaires) + u' exemplaire(s) de cet oeuvre')
    return redirect('/admin/oeuvre/show')

@admin_oeuvre.route('/admin/oeuvre/edit', methods=['GET'])
def edit_oeuvre():
    id = request.args.get('id', '')
    mycursor = get_db().cursor()
    sql = '''SELECT titre, photo, id, auteur_id as idAuteur, date_parution as dateParution
            FROM oeuvre
            WHERE id = %s;'''
    mycursor.execute(sql, (id,))
    oeuvre = mycursor.fetchone()
    if oeuvre['dateParution']:
        oeuvre['dateParution']=oeuvre['dateParution'].strftime("%d/%m/%Y")
    sql = '''SELECT auteur.nom, auteur.id FROM auteur
                ORDER BY auteur.nom;'''
    mycursor.execute(sql)
    auteurs = mycursor.fetchall()
    return render_template('admin/oeuvre/edit_oeuvre.html', donnees=oeuvre, auteurs=auteurs, erreurs=[])

@admin_oeuvre.route('/admin/oeuvre/edit', methods=['POST'])
def valid_edit_oeuvre():
    mycursor = get_db().cursor()
    id = request.form.get('id', '')
    titre = request.form.get('titre', '')
    dateParution = request.form.get('dateParution', '')
    idAuteur = request.form.get('idAuteur', '')
    photo = request.form.get('photo', '')
    dto_data={'titre': titre, 'photo': photo, 'dateParution': dateParution, 'idAuteur': idAuteur, 'id': id}
    print(dto_data)
    valid, errors, dto_data = validator_oeuvre(dto_data)
    if valid:
        dateParution=dto_data['dateParution_us']
        tuple_update = (titre,idAuteur,dateParution,photo,id)
        print(tuple_update)
        sql = '''UPDATE oeuvre SET titre = %s, auteur_id = %s, date_parution = %s, photo = %s WHERE id = %s;'''
        mycursor.execute(sql, tuple_update)
        get_db().commit()
        print(u'oeuvre modifiée , titre : ', titre, ' - auteur_id:', idAuteur)
        message = u'oeuvre modifiée , titre:'+titre + '- auteur_id:' + idAuteur
        flash(message)
        return redirect('/admin/oeuvre/show')
    sql = '''SELECT auteur.nom, auteur.id FROM auteur
                ORDER BY auteur.nom;'''
    mycursor.execute(sql)
    auteurs = mycursor.fetchall()
    return render_template('admin/oeuvre/edit_oeuvre.html', auteurs=auteurs, erreurs=errors, donnees=dto_data)


def validator_oeuvre(data):
    mycursor = get_db().cursor()
    # id,titre,date_parution,photo,auteur_id
    valid = True
    errors = dict()

    if 'id' in data.keys():
        if not data['id'].isdecimal():
           errors['id'] = 'type id incorrect'
           valid= False
    sql = '''SELECT * FROM auteur
            WHERE id = %s;'''
    mycursor.execute(sql, (data['idAuteur'],))
    auteur = mycursor.fetchone()
    if not auteur:
        flash("Auteur n'existe pas")
        errors['idAuteur'] = "Saisir un Auteur"
        valid = False
    else :
        data['idAuteur']=int(data['idAuteur'])

    if not re.match(r'\w{2,}', data['titre']):
        flash('Titre doit avoir au moins deux caractères')
        errors['titre'] = "Le titre doit avoir au moins deux caractères"
        valid = False

    try:
        datetime.datetime.strptime(data['dateParution'], '%d/%m/%Y')
    except ValueError:
        flash("la Date n'est pas valide")
        errors['dateParution'] = "la Date n'est pas valide format:%d/%m/%Y"
        valid = False
    else:
        data['dateParution_us'] = datetime.datetime.strptime(data['dateParution'], "%d/%m/%Y").strftime("%Y-%m-%d")

    if data['photo']:
        photo_path = os.path.join(current_app.root_path,
                                  'static', 'assets', 'images', data['photo'])

        if not os.path.isfile(photo_path):
            flash(f"Photo n'existe pas: { photo_path }")
            errors['photo'] = f"la Photo n'existe pas: { photo_path }"
            valid = False
    return (valid, errors, data)
