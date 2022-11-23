#! /usr/bin/python
# -*- coding:utf-8 -*-
from flask import Blueprint
from flask import Flask, request, render_template, redirect, url_for, abort, flash, session, g

from connexion_db import get_db

from datetime import date

admin_emprunt = Blueprint('admin_emprunt', __name__,
                        template_folder='templates')

@admin_emprunt.route('/admin/emprunt/adherent-select')
def emprunt_select_adherent():
    mycursor = get_db().cursor()
    action = request.args.get('action', '')
    if action == 'emprunter':
        sql = '''select a.id, a.nom, a.date_paiement, group_concat(empr.date_emprunt), group_concat(empr.date_retour) as liste_retour,
       count(distinct empr.date_emprunt, empr.exemplaire_id) as nbrEmprunt,
       if ((current_date() > date_add(a.date_paiement, interval '1' year)), 1, 0) as retardCotisation,
           group_concat(if (current_date() > date_add(a.date_paiement, interval '1' year), 1, 0)) as listeRetard,
       COUNT(empr.adherent_id) as nbreRetard
from adherent a
left join emprunt empr on empr.adherent_id = a.id
group by a.id
having nbrEmprunt<6
order by a.nom;'''
        mycursor.execute(sql)
        donneesAdherents = mycursor.fetchall()
        return render_template('admin/emprunt/select_adherent_emprunts.html', donneesAdherents=donneesAdherents, action=action, erreurs=[])
    if action == 'rendre':
        sql = '''SELECT DISTINCT a.id, a.nom
FROM adherent a
JOIN emprunt e on a.id = e.adherent_id
WHERE date_emprunt
AND date_retour IS NULL
GROUP BY a.id, a.nom
ORDER BY a.nom;'''
        mycursor.execute(sql)
        donneesAdherents = mycursor.fetchall()
        return render_template('admin/emprunt/select_adherent_emprunts.html', donneesAdherents=donneesAdherents,
                                   action=action, erreurs=[])
    abort(404,"erreur de paramètres")




@admin_emprunt.route('/admin/emprunt/emprunter', methods=['POST'])
def emprunt_emprunter():
    mycursor = get_db().cursor()
    donnees = {}
    idAdherent = request.form.get('idAdherent', '')
    dateEmprunt = request.form.get('dateEmprunt', '')
    noExemplaire = request.form.get('noExemplaire', '')
    if idAdherent == '':
        sql = '''select a.id, a.nom, a.date_paiement, group_concat(empr.date_emprunt), group_concat(empr.date_retour) as liste_retour,
        count(distinct empr.date_emprunt, empr.exemplaire_id) as nbrEmprunt,
        if ((current_date() > date_add(a.date_paiement, interval '1' year)), 1, 0) as retardCotisation,
        group_concat(if (current_date() > date_add(a.date_paiement, interval '1' year), 1, 0)) as listeRetard
from adherent a
left join emprunt empr on empr.adherent_id = a.id
group by a.id
order by a.nom;'''
        mycursor.execute(sql)
        donneesAdherents = mycursor.fetchall()
        erreurs = {'idAdherent': u'Selectionner un adhérent'}
        return render_template('admin/emprunt/select_adherent_emprunts.html', donneesAdherents=donneesAdherents,
                               action='emprunter', erreurs=erreurs)

    sql = '''select count(e.exemplaire_id) as nbrEmprunt, count(if(curdate() > date_add(e.date_emprunt, interval '3' month), 1, 0)) as retard
from emprunt e
where e.adherent_id = %s and e.date_retour is null;'''
    mycursor.execute(sql, idAdherent)
    nbrEmprunts = mycursor.fetchone()
    print(nbrEmprunts)
    if nbrEmprunts is None:
        nbrEmprunts = {}
        nbrEmprunts['nbrEmprunt'] = 0
    print(nbrEmprunts)

    if idAdherent != '' and dateEmprunt != '' and noExemplaire != '' and nbrEmprunts['nbrEmprunt'] < 6:
        # traitement des erreurs
        tuple_isert = (idAdherent, noExemplaire, dateEmprunt)
        sql = '''insert into emprunt(adherent_id, exemplaire_id, date_emprunt, date_retour) values
(%s, %s, %s, null);'''
        mycursor.execute(sql, tuple_isert)
        get_db().commit()
        nbrEmprunts['nbrEmprunt'] = nbrEmprunts['nbrEmprunt']+1

    sql = '''select id, nom, adresse, date_paiement as datePaiement
from adherent
where id = %s;'''
    mycursor.execute(sql, idAdherent)
    donneesAdherent = mycursor.fetchone()

    sql = '''select a.nom as nomAuteur, o.titre, o.id as noOeuvre, e.id as noExemplaire
from auteur a
inner join oeuvre o on o.auteur_id = a.id
inner join exemplaire e on e.oeuvre_id = o.id where e.id not in (
    select empr.exemplaire_id
    from emprunt empr
    where date_emprunt and date_retour is null
)
order by a.nom asc, o.id desc;'''
    mycursor.execute(sql)
    listeExempDispo = mycursor.fetchall()

    sql = '''select a.id as idAdherent, ex.id as noExemplaire, o.titre, a.nom as nomAdherent,
    emp.date_emprunt, emp.date_retour, datediff(curdate(), emp.date_emprunt) as nbJoursEmprunt
from adherent a
left join emprunt emp on emp.adherent_id = a.id
left join exemplaire ex on ex.id = emp.exemplaire_id
left join oeuvre o on o.id = ex.oeuvre_id
where a.id = %s and emp.date_retour is null
order by datediff(curdate(), emp.date_emprunt);'''
    mycursor.execute(sql, idAdherent)
    donneesEmprunt = mycursor.fetchall()

    if 'dateEmprunt' not in donnees.keys() or donnees['dateEmprunt'] == '':
        donnees['dateEmprunt'] = date.today().strftime("%Y-%m-%d")

    return render_template('admin/emprunt/add_emprunts.html', donneesAdherent=donneesAdherent, action='emprunter',
                           listeExempDispo=listeExempDispo, donneesEmprunt=donneesEmprunt, nbrEmprunts=nbrEmprunts,
                           donnees=donnees, erreurs=[])

@admin_emprunt.route('/admin/emprunt/rendre', methods=['POST'])
def emprunt_rendre():
    mycursor = get_db().cursor()
    idAdherent = request.form.get('idAdherent', '')
    if idAdherent == '':
        sql = '''SELECT DISTINCT a.id, a.nom
FROM adherent a
JOIN emprunt e on a.id = e.adherent_id
WHERE date_emprunt
AND date_retour IS NULL
GROUP BY a.id, a.nom
ORDER BY a.nom;'''
        mycursor.execute(sql)
        donneesAdherents = mycursor.fetchall()
        erreurs={'idAdherent': u'Selectionner un adhérent'}
        return render_template('admin/emprunt/select_adherent_emprunts.html', donneesAdherents=donneesAdherents,
                                   action='rendre', erreurs=erreurs)


    dateEmprunt = request.form.get('dateEmprunt', '')
    noExemplaire = request.form.get('noExemplaire', '')
    dateRetour = request.form.get('dateRetour', '')

    if idAdherent != '' and dateEmprunt != '' and noExemplaire !='' and dateRetour != '' :
        # traitement des erreurs
        tuple_update = (dateRetour, idAdherent, noExemplaire, dateEmprunt)
        sql = '''update emprunt set date_retour=%s where adherent_id=%s and exemplaire_id=%s and date_emprunt=%s;'''
        mycursor.execute(sql, tuple_update)
        get_db().commit()

    sql = '''SELECT *
FROM adherent a
WHERE a.id = %s;'''
    mycursor.execute(sql,(idAdherent))
    donneesAdherent = mycursor.fetchone()
    sql = '''SELECT coalesce(count(e.exemplaire_id),0) as nbrEmprunt,
       IF(
           CURDATE() > DATE_ADD(date_retour, INTERVAL 3 MONTH),1,0
        ) as retard
FROM emprunt e
WHERE adherent_id = %s AND date_retour is null
GROUP BY date_retour;
'''
    mycursor.execute(sql,(idAdherent))
    nbrEmprunts = mycursor.fetchone()
    sql = '''SELECT a.id as idAdherent, e.id as noExemplaire, o.titre, a.nom, e2.date_emprunt, e2.date_retour, DATEDIFF(CURDATE(), e2.date_emprunt) as nbJoursEmprunt
FROM adherent a
JOIN emprunt e2 on a.id = e2.adherent_id
JOIN exemplaire e on e2.exemplaire_id = e.id
JOIN oeuvre o on e.oeuvre_id = o.id
WHERE a.id = %s AND e2.date_retour is null
ORDER BY e2.date_emprunt DESC;'''
    mycursor.execute(sql,(idAdherent))
    donneesEmprunts = mycursor.fetchall()

    donnees={}
    if 'dateRetour' not in donnees.keys() or donnees['dateRetour'] == '':
        donnees['dateRetour'] = date.today().strftime("%Y-%m-%d")

    return render_template('admin/emprunt/return_emprunts.html' , donneesAdherents=donneesAdherent,
            action = 'rendre',
            donneesEmprunt = donneesEmprunts,
            nbrEmprunts = nbrEmprunts,
            donnees = donnees,
            erreurs = [])


@admin_emprunt.route('/admin/emprunt/delete', methods=['GET','POST'])
def delete_emprunt_valid():
    mycursor = get_db().cursor()
    idAdherent = request.args.get('idAdherent', 'pasid')
    print("Id adherent : " + idAdherent)
    if request.method == 'POST':
        list_emprunts=request.form.getlist('select_emprunt')
        if(len(list_emprunts)>=1):
            print(list_emprunts)
            for elt in list_emprunts:
                list_emprunts_split=elt.split('_')
                print(list_emprunts_split)
                sql = '''SELECT date_retour FROM emprunt WHERE adherent_id = %s AND exemplaire_id = %s AND date_emprunt = %s;'''
                mycursor.execute(sql, list_emprunts_split)
                if len(mycursor.fetchall()) != 1:
                    message = u'emprunt à supprimé, PB , oeuvre_id :' + str(elt)
                    flash(message)
                    return redirect('/admin/emprunt/delete')
                sql = '''DELETE FROM emprunt WHERE adherent_id = %s AND exemplaire_id = %s AND date_emprunt = %s;'''
                mycursor.execute(sql, list_emprunts_split)
                get_db().commit()
            message = u'emprunt(s) supprimé(s)'
            flash(message)
        return redirect('/admin/emprunt/delete')

    sql = '''SELECT a.id as idAdherent, e.id as idExemplaire, o.titre, a.nom as nomAdherent, e2.date_emprunt as dateEmprunt,
       e2.date_retour as dateRetour, DATEDIFF(CURDATE(), e2.date_emprunt) as nbJoursEmprunt
FROM adherent a
JOIN emprunt e2 on a.id = e2.adherent_id
JOIN exemplaire e on e2.exemplaire_id = e.id
JOIN oeuvre o on e.oeuvre_id = o.id'''
    if idAdherent.isnumeric():
        sql = sql + " WHERE a.id ="+str(idAdherent)
    sql=sql + " ORDER BY nomAdherent, dateEmprunt desc;"

    mycursor.execute(sql)
    donnees = mycursor.fetchall()
    sql = '''SELECT a.id as idAdherent, a.nom
FROM adherent a
ORDER BY a.nom;'''
    mycursor.execute(sql)
    donneesAdherents = mycursor.fetchall()
    return render_template('admin/emprunt/delete_all_emprunts.html', donnees=donnees, donneesAdherents=donneesAdherents)


@admin_emprunt.route('/admin/emprunt/bilan-retard', methods=['GET'])
def bilan_emprunt():
    mycursor = get_db().cursor()
    sql = '''SELECT a.id as idAdherent, e.id as idExemplaire, o.titre, a.nom as nomAdherent, e2.date_emprunt,
       e2.date_retour as dateRetour, DATEDIFF(CURDATE(), e2.date_emprunt) as nbJoursEmprunt,
       DATEDIFF(CURDATE(),DATE_ADD(e2.date_emprunt,INTERVAL 3 MONTH)) as RETARD,
       DATE_ADD(e2.date_emprunt, INTERVAL 3 MONTH) as dateRenduTheorique,
       IF(DATEDIFF(CURDATE(), e2.date_emprunt) > 90,1,0) as flagRetard,
       IF(DATEDIFF(CURDATE(), e2.date_emprunt) > 120,1,0) as flagPenalite,
       IF(
           DATEDIFF(CURDATE(),DATE_ADD(e2.date_emprunt,INTERVAL 3 MONTH)) < 0,0,
           IF(
           (DATEDIFF(DATE_SUB(CURDATE(),INTERVAL 4 MONTH), e2.date_emprunt)*0.5) > 0 AND
           (DATEDIFF(DATE_SUB(CURDATE(),INTERVAL 4 MONTH), e2.date_emprunt)*0.5) < 25,
           (DATEDIFF(DATE_SUB(CURDATE(),INTERVAL 4 MONTH), e2.date_emprunt)*0.5), 25
               )
           ) as dette
FROM adherent a
JOIN emprunt e2 on a.id = e2.adherent_id
JOIN exemplaire e on e.id = e2.exemplaire_id
JOIN oeuvre o on o.id = e.oeuvre_id
WHERE e2.date_retour is null;'''
    mycursor.execute(sql)
    donneesBilan = mycursor.fetchall()
    return render_template('admin/emprunt/bilan_emprunt.html', donnees=donneesBilan)