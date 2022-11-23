#! /usr/bin/python
# -*- coding:utf-8 -*-
from flask import Blueprint
from flask import Flask, request, render_template, redirect, url_for, abort, flash, session, g

from flask import *
import re
import datetime

from connexion_db import get_db

admin_exemplaire = Blueprint('admin_exemplaire', __name__,
                        template_folder='templates')

@admin_exemplaire.route('/admin/exemplaire/show')
def show_exemplaire():
    noOeuvre=request.args.get('noOeuvre', '')
    mycursor = get_db().cursor()
    sql = ''' SELECT 'requete4_1' FROM DUAL '''
    sql = '''SELECT e.id as noExemplaire, a.nom as nomAuteur, o.titre, o.id as noOeuvre, o.date_parution AS date_parution_en, o.photo,
            COUNT(e1.id) as nbExemplaire, COUNT(e2.id) as nombreDispo,
            CONCAT(LPAD(CAST(DAY(o.date_parution)AS CHAR(2)),2,0),'/',LPAD(CAST(MONTH(o.date_parution) AS CHAR(2)),2,0),'/',YEAR(o.date_parution)) AS date_parution
            FROM oeuvre o
            JOIN auteur a on o.auteur_id = a.id
            LEFT JOIN exemplaire e on o.id = e.oeuvre_id
            LEFT JOIN exemplaire e1 on o.id = e1.oeuvre_id
            LEFT JOIN exemplaire e2 on e2.id = e1.id
                AND e2.id NOT IN (
                    SELECT emprunt.exemplaire_id
                    FROM emprunt
                    WHERE emprunt.date_retour IS NULL
                )
            WHERE o.id = %s
            GROUP BY e.id, o.id, a.nom, o.titre, o.date_parution, o.photo
            ORDER BY a.nom ASC,o.titre ASC;'''
    mycursor.execute(sql,(noOeuvre))
    oeuvre = mycursor.fetchone()
    sql = ''' SELECT 'requete4_2' FROM DUAL '''
    sql = '''SELECT exemplaire.id as noExemplaire, exemplaire.etat, exemplaire.date_achat, exemplaire.prix, oeuvre.titre,
                        oeuvre.id as noOeuvre, oeuvre.date_parution as dateParution, exemplaire.id as Exemplaire,
                        IF(e2.id=0,NULL, e2.id) as ExemplaireDispo,
                        IF(COUNT(e2.id)=0,'abs', 'present') as present
                 FROM exemplaire
                 JOIN oeuvre on exemplaire.oeuvre_id = oeuvre.id
                 LEFT JOIN exemplaire e2 on e2.id = exemplaire.id
                 AND e2.id NOT IN (
                        SELECT emprunt.exemplaire_id
                        FROM emprunt
                        WHERE emprunt.date_retour IS NULL
                 )
                 WHERE oeuvre.id = %s
                 GROUP BY oeuvre.titre, exemplaire.etat, exemplaire.date_achat, exemplaire.prix, exemplaire.id, oeuvre.id,
                          oeuvre.date_parution, exemplaire.id
                 ORDER BY ExemplaireDispo DESC;'''
    mycursor.execute(sql,(noOeuvre))
    exemplaires = mycursor.fetchall()
    return render_template('admin/exemplaire/show_exemplaires.html', exemplaires=exemplaires, oeuvre=oeuvre)

@admin_exemplaire.route('/admin/exemplaire/add', methods=['GET'])
def add_exemplaire():
    noOeuvre = request.args.get('noOeuvre', '')
    mycursor = get_db().cursor()
    sql = ''' SELECT 'requete4_3' FROM DUAL '''
    sql = '''SELECT auteur.nom as nomAuteur, oeuvre.titre, oeuvre.id as noOeuvre, oeuvre.date_parution as dateParution
    FROM oeuvre
    JOIN auteur on auteur.id = oeuvre.auteur_id
    WHERE oeuvre.id = %s;'''
    mycursor.execute(sql, (noOeuvre))
    oeuvre = mycursor.fetchone()
    date_achat = datetime.datetime.now().strftime("%d/%m/%Y")
    return render_template('admin/exemplaire/add_exemplaire.html', donnees2=oeuvre, donnees={'dateAchat': date_achat, 'noOeuvre': noOeuvre}, erreurs=[])

@admin_exemplaire.route('/admin/exemplaire/add', methods=['POST'])
def valid_add_exemplaire():
    mycursor = get_db().cursor()
    noOeuvre = request.form.get('noOeuvre', '')
    noOeuvre=int(float(noOeuvre))
    dateAchat = request.form.get('dateAchat', '')
    etat = request.form.get('etat', '')
    prix = request.form.get('prix', '')

    dto_data={'noOeuvre': noOeuvre, 'etat': etat, 'dateAchat': dateAchat, 'prix': prix}
    valid, errors, dto_data = validator_exemplaire(dto_data)
    if valid:
        dateAchat = dto_data['dateAchat_us']
        tuple_insert = (noOeuvre,etat,dateAchat,prix)
        print(tuple_insert)
        sql = ''' SELECT 'requete4_5' FROM DUAL '''
        sql = 'INSERT INTO exemplaire(oeuvre_id, etat, date_achat, prix) VALUES (%s, %s, %s, %s);'''

        mycursor.execute(sql, tuple_insert)
        get_db().commit()
        message = u'exemplaire ajouté , oeuvre_id :'+str(noOeuvre)
        flash(message)
        return redirect('/admin/exemplaire/show?noOeuvre='+str(noOeuvre))

    sql = ''' SELECT 'requete4_3' FROM DUAL '''
    sql = '''SELECT auteur.nom as nomAuteur, oeuvre.titre, oeuvre.id as noOeuvre, oeuvre.date_parution as dateParution
    FROM oeuvre
    JOIN auteur on auteur.id = oeuvre.auteur_id
    WHERE oeuvre.id = %s;'''
    mycursor.execute(sql, (noOeuvre))
    oeuvre = mycursor.fetchone()
    return render_template('admin/exemplaire/add_exemplaire.html', donnees2=oeuvre,
                           donnees=dto_data, erreurs=errors)

@admin_exemplaire.route('/admin/exemplaire/delete', methods=['GET'])
def delete_exemplaire():
    mycursor = get_db().cursor()
    id = request.args.get('id', '') #id de l'exemplaire
    tuple_delete = (id,)
    sql = ''' SELECT 'requete4_9' FROM DUAL '''
    sql = '''SELECT oeuvre_id from exemplaire where id = %s;'''
    mycursor.execute(sql, tuple_delete)
    oeuvre = mycursor.fetchone()
    oeuvre_id=str(oeuvre['oeuvre_id'])
    print(oeuvre,oeuvre_id)
    #noOeuvre = request.form.get('noOeuvre', '')
    if not(id and id.isnumeric()):
        abort("404","erreur id oeuvre")

    nb_emprunts = 0
    sql = ''' SELECT 'requete4_7' FROM DUAL '''
    sql = '''SELECT COUNT(*) as nb_emprunts FROM emprunt join exemplaire on emprunt.exemplaire_id=exemplaire.id WHERE exemplaire.id = %s'''
    mycursor.execute(sql, tuple_delete)
    res_nb_emprunts = mycursor.fetchone()
    if 'nb_emprunts' in res_nb_emprunts.keys():
        nb_emprunts=res_nb_emprunts['nb_emprunts']
    if nb_emprunts == 0 :
        sql = ''' SELECT 'requete4_8' FROM DUAL '''
        sql = '''DELETE FROM exemplaire where id = %s'''
        mycursor.execute(sql, tuple_delete)
        get_db().commit()
        flash(u'oeuvre supprimée, id: ' + id)
    else :
        flash(u'suppression impossible, il faut supprimer  : ' + str(nb_emprunts) + u' emprunt(s) de cet exemplaire')
    return redirect('/admin/exemplaire/show?noOeuvre='+oeuvre_id)

@admin_exemplaire.route('/admin/exemplaire/edit', methods=['GET'])
def edit_exemplaire():
    mycursor = get_db().cursor()
    id = request.args.get('id', '')
    sql = ''' SELECT 'requete4_10' FROM DUAL '''
    sql = '''SELECT auteur.nom as nomAuteur, oeuvre.titre, exemplaire.oeuvre_id as noOeuvre, oeuvre.date_parution as dateParution
    FROM oeuvre
    JOIN exemplaire on oeuvre.id = exemplaire.oeuvre_id
    JOIN auteur on auteur.id = oeuvre.auteur_id
    WHERE exemplaire.id = %s'''
    mycursor.execute(sql, (id))
    oeuvre = mycursor.fetchone()


    id_exemplaire = request.args.get('id', '')
    sql = ''' SELECT 'requete4_11' FROM DUAL '''
    sql = '''SELECT id as id_exemplaire, etat, date_achat as dateAchat, prix, oeuvre_id as noOeuvre from exemplaire where id = %s'''
    mycursor.execute(sql, (id_exemplaire))
    exemplaire = mycursor.fetchone()
    if exemplaire['dateAchat']:
        exemplaire['dateAchat']=exemplaire['dateAchat'].strftime("%d/%m/%Y")
    return render_template('admin/exemplaire/edit_exemplaire.html', donnees=exemplaire, donnees2=oeuvre, erreurs=[])

@admin_exemplaire.route('/admin/exemplaire/edit', methods=['POST'])
def valid_edit_exemplaire():
    mycursor = get_db().cursor()
    id_exemplaire = request.form.get('noExemplaire', '')
    noOeuvre = request.form.get('noOeuvre', '')
    dateAchat = request.form.get('dateAchat', '')
    etat = request.form.get('etat', '')
    prix = request.form.get('prix', '')

    dto_data={'noOeuvre': noOeuvre, 'etat': etat, 'dateAchat': dateAchat, 'prix': prix, 'id_exemplaire':id_exemplaire}
    valid, errors, dto_data = validator_exemplaire(dto_data)
    if valid:
        dateAchat = dto_data['dateAchat_us']
        tuple_update = (noOeuvre, etat, dateAchat, prix, id_exemplaire)
        print(tuple_update)
        sql = ''' SELECT 'requete4_12' FROM DUAL '''
        sql = '''UPDATE exemplaire SET oeuvre_id = %s, etat = %s, date_achat = %s, prix = %s WHERE id = %s'''
        mycursor.execute(sql, tuple_update)
        get_db().commit()
        flash(u' exemplaire modifié, noOeuvre: ' + noOeuvre )
        return redirect('/admin/exemplaire/show?noOeuvre='+noOeuvre)
    sql = ''' SELECT 'requete4_10' FROM DUAL '''
    sql = '''SELECT auteur.nom as nomAuteur, oeuvre.titre, exemplaire.oeuvre_id as noOeuvre, oeuvre.date_parution as dateParution
    FROM oeuvre
    JOIN exemplaire on oeuvre.id = exemplaire.oeuvre_id
    JOIN auteur on auteur.id = oeuvre.auteur_id
    WHERE exemplaire.id = %s'''
    mycursor.execute(sql, (noOeuvre))
    oeuvre = mycursor.fetchone()
    return render_template('admin/exemplaire/edit_exemplaire.html', donnees=dto_data, donnees2=oeuvre, erreurs=errors)

def validator_exemplaire(data):
    mycursor = get_db().cursor()
    # id,etat,date_achat,prix,oeuvre_id
    valid = True
    errors = dict()

    if 'id' in data.keys():
        if not data['id'].isdecimal():
            errors['id'] = 'type id incorrect'
            valid = False

    if not re.match(r'\w{2,}', data['etat']):
        flash('Titre doit avoir au moins deux caractères')
        errors['etat'] = "Le titre doit avoir au moins deux caractères"
        valid = False

    try:
        datetime.datetime.strptime(data['dateAchat'], '%d/%m/%Y')
    except ValueError:
        flash("la Date n'est pas valide")
        errors['dateAchat'] = "la Date n'est pas valide format:%d/%m/%Y"
        valid = False
    else:
        data['dateAchat_us'] = datetime.datetime.strptime(data['dateAchat'], "%d/%m/%Y").strftime("%Y-%m-%d")

    try:
        float(data['prix'])
    except ValueError:
        flash("Prix n'est pas valide")
        errors['prix'] = "le Prix n'est pas valide"
        valid = False

    return (valid, errors, data)