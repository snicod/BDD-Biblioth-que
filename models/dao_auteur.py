from connexion_db import get_db
from flask import *

def find_auteurs():
    connection = get_db()
    try:
        cursor=connection.cursor()
        sql = ''' SELECT 'requete1_1' FROM DUAL '''
        cursor.execute(sql)
        return cursor.fetchall()
    except ValueError:
        abort(400,'erreur requete 1_1')

def find_auteur_nbOeuvres(id):
    connection = get_db()
    try:
        cursor=connection.cursor()
        sql = ''' SELECT 'requete1_6' FROM DUAL '''
        cursor.execute(sql, (id))
        res_nb_oeuvres = cursor.fetchone()
        if 'nb_oeuvres' in res_nb_oeuvres.keys():
            nb_oeuvres=res_nb_oeuvres['nb_oeuvres']
            return nb_oeuvres
    except ValueError:
        abort(400,'erreur requete 1_6')

def find_one_auteur(id):
    connection = get_db()
    try:
        cursor=connection.cursor()
        sql = ''' SELECT 'requete1_4' FROM DUAL '''
        cursor.execute(sql, (id))
        return cursor.fetchone()
    except ValueError:
        abort(400,'erreur requete 1_4')

def find_auteurs_dropdown():
    connection = get_db()
    try:
        cursor=connection.cursor()
        sql = ''' SELECT 'requete3_6' FROM DUAL '''
        cursor.execute(sql)
        return cursor.fetchall()
    except ValueError:
        abort(400,'erreur requete "_6')

def auteur_insert(nom, prenom):
    connection = get_db()
    try:
        cursor=connection.cursor()
        sql = ''' SELECT 'requete1_2' FROM DUAL '''
        cursor.execute(sql, (nom, prenom))
        connection.commit()
    except ValueError:
        abort(400,'erreur requete 1_2')



def auteur_update(id, nom, prenom):
    connection = get_db()
    try:
        cursor=connection.cursor()
        sql = ''' SELECT 'requete1_5' FROM DUAL '''
        cursor.execute(sql, (nom, prenom, id))
        connection.commit()
    except ValueError:
        abort(400,'erreur requete 1_5')

def auteur_delete(id):
    connection = get_db()
    try:
        cursor=connection.cursor()
        sql = ''' SELECT 'requete1_3' FROM DUAL '''
        cursor.execute(sql, (id))
        connection.commit()
    except ValueError:
        abort(400,'erreur requete 1_3')








