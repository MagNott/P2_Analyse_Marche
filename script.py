import requests
from bs4 import BeautifulSoup
from pathlib import Path
import csv
import re
from urllib.parse import urljoin
import os


# VARIABLES ET CONSTANTES GLOBALES

# Construction URL
URL_RACINE = 'https://books.toscrape.com'
URL_RACINE_CATEGORIE = 'https://books.toscrape.com/catalogue/category/books/'
URL_INTERMEDIAIRE_LIVRE = 'https://books.toscrape.com/catalogue/'

# Préparation header pour le csv
DATA_HEADER = [
    'product_page_url',
    'universal_product_code',
    'title',
    'Price (excl. tax)',
    'Price (incl. tax)',
    'number_available',
    'product_description',
    'category',
    'review_rating',
    'image_url'
]


# DEFNITIONS DES FONCTIONS

def extraire_donnees_livre(page_livre, url_page_livre, dossier_categorie, titre_categorie ):
    """
    Fonction permettant de récupérer les éléments d'un livre

    page_livre -- Contenu HTMl de la page du livre
    url_page_livre -- URL de la page du livre
    dossier_categorie -- Chemin pour enregistrer l'image
    titre_categorie -- Nom de la catégorie du livre
    """
    
    # Définitions des variables de la fonction
    livres_extraits = []
    data = []

    # Préparation des données intermédiaires du tableau dans la page du livre
    table = page_livre.table
    if not table:
        print("Erreur : La balise <table> n'a pas été trouvée")
        print (page_livre)
        print(url_page_livre)
        exit()

    liste_info = []
    for row in table.find_all("tr"):
        for element in row.find_all("td"):
            liste_info.append(element.text)

    if len(liste_info) < 6:
        print("Erreur : Les informations extraites de la table sont insuffisantes")
        exit()

    # Contruction des data du livres
    data.append(url_page_livre)

    # Trouver le titre
    titre = page_livre.h1
    if not titre:
        print("Erreur : La balise <h1> qui conient le titre du livre n'a pas été trouvée")
        exit()
    titre_nettoye = re.sub(r"[^\w\s-]", "", titre.text).replace(" ", "_")
    data.append(titre_nettoye)

    # Trouver le code
    data.append(liste_info[0])

    # Trouver les prix hors taxe et ttc
    data.append(liste_info[2])
    data.append(liste_info[3])

    # Trouver le nombre dispo
    disponible = liste_info[5]
    nombre_disponible = re.findall(r"\d+", disponible)
    nombre_str = nombre_disponible[0]
    data.append(int(nombre_str))

    # Trouver la description
    h2 = page_livre.find("h2")
    if not h2:
        print("Erreur : La balise <h2> qui contient la description n'a pas été trouvée")
        exit()
    description = h2.find_next("p")
    if not description:
        print("Erreur : La balise <p> qui contient la description n'a pas été trouvée")
        exit()
    description_text = description.text
    data.append(description_text)

    # Trouver la categorie
    menu_categorie = page_livre.ul
    if not menu_categorie:
        print("Erreur : La balise <ul> qui contient la categorie n'a pas été trouvée")
        exit()
    liste = menu_categorie.find_all("li")
    categorie_a_extraire = liste[2]
    categorie = categorie_a_extraire.find("a")
    data.append(categorie.text)

    # Trouver la note
    recherche_etoile = page_livre.find("p", class_="star-rating") 
    if not recherche_etoile:
        print("Erreur : La balise <p> avec la classe star-rating qui contient la note n'a pas été trouvée")
        exit()
    nombre_etoiles = recherche_etoile["class"]
    etoile_traduite = traduction_notes(nombre_etoiles[1])
    data.append(etoile_traduite)

    # Trouver l'url de l'image
    recherche_url_image = page_livre.find("img", )
    if not recherche_url_image:
        print("Erreur : La balise <img> qui contient l'url de l'image n'a pas été trouvée")
        exit()
    url_relative_image = recherche_url_image['src']
    url_complete_image = urljoin(URL_RACINE, url_relative_image)

    # Télécharger l'image
    telechargement_image = requests.get(url_complete_image)
    if telechargement_image.status_code != 200:
        print(f"Erreur : L'image {url_complete_image} n'est pas accessible. Statut {telechargement_image.status_code}")
        exit()
    image = telechargement_image.content
    chemin_image = os.path.join(dossier_categorie, f"{titre_categorie}-{titre_nettoye}.jpg")
    with open(chemin_image, 'wb') as f:
        f.write(image)

    data.append(url_complete_image)
    livres_extraits.append(data)
    return livres_extraits

def extraire_urls_livres(p_page_categorie) :
    """
    Fonction permettant de récupérer les URLS des livres d'une page

    liste_livres_page -- La liste des livres contenus dans une page
    """

    liste_urls_absolues_livres  = []

    # Récupération des urls des livres
    liste_livre = p_page_categorie.ol
    liste_liens_livres_page = liste_livre.find_all("a")

    for livre in liste_liens_livres_page:
        url_relative_livre = livre['href']
        url_livre_nettoyee = url_relative_livre.lstrip("../")
        url_complete_livre = urljoin(URL_INTERMEDIAIRE_LIVRE, url_livre_nettoyee)
        if url_complete_livre not in liste_urls_absolues_livres :
            liste_urls_absolues_livres.append(url_complete_livre)

    return liste_urls_absolues_livres 

def extraire_urls_categorie(page_courante) :
    """
    Fonction permettant de récupérer les URLS complètes de chaque catégorie

    page_courante -- Contenu HTMl de la page d'accueil
    """

    urls_categorie = []
    categories = page_courante.find("ul", class_="nav nav-list")
    if not categories:
        print("Erreur : La balise <ul> avec la classe nav nav-list qui contient le lien de la catégorie n'a pas été trouvée")
        exit()
    liste_categories =  categories.find_all('li')  
    for categorie in liste_categories:
        url_categorie = categorie.find('a')['href']
        url_categorie_nettoyee = url_categorie.lstrip("../")
        url_complete_categorie = urljoin(URL_RACINE, url_categorie_nettoyee)
        urls_categorie.append(url_complete_categorie)

    del urls_categorie[0]
    return urls_categorie

def traduction_notes(p_etoile) :
    """
    Fonction permettant de traduire la note en chiffre

    p_etoile -- note récupérée sur la page du livre 
    """

    match p_etoile:
        case "One":
            p_etoile = 1
        case "Two":
            p_etoile = 2
        case "Three":
            p_etoile = 3
        case "Four":
            p_etoile = 4
        case "Five":
            p_etoile = 5
        case _:
            p_etoile = 0
    return p_etoile

def recuperer_page (p_url) : 
    # Requete pour récupérer une categorie
    reponse = requests.get(p_url)
    if reponse.status_code != 200:
        print(f"Erreur : La page {p_url} n'est pas accessible. Statut {reponse.status_code}")
        exit()

    # Pour vérifier l'encodage de la page on print reponse.headers ou reponse.apparent_encoding
    reponse.encoding = 'utf-8'

    # Retourne le parse de la page avec beautiful soup
    return BeautifulSoup(reponse.text, features="html.parser")



# LOGIQUE PRINCIPALE

# Récupération de la page d'accueil pour chercher les catégories
page_accueil = recuperer_page(URL_RACINE)
urls_categories_extraites = extraire_urls_categorie(page_accueil)

# Compteur pour compter les catégories extraites
i = 0

# Répertoire où le script est exécuté pour créer le dossier booktoscrape qui contiendra tous les éléments issus du scrape
dossier_courant = os.getcwd()
chemin_booktoscrape = os.path.join(dossier_courant, "booktoscrape")
os.makedirs(chemin_booktoscrape, exist_ok=True)
print("Le dossier Booktoscrape est créé")

# Boucle permettant de passer sur chaque catégorie pour en extraires les livres
for url_categorie_extraite in urls_categories_extraites:

    # Initialisation de la variable contenant les données des livres
    data_complete = []

    page_categorie = recuperer_page(url_categorie_extraite)
    nom_categorie = page_categorie.find('h1').text.strip().replace(" ", "-")
    print(f"Extraction de la catégorie {nom_categorie}...")

    chemin_categorie = os.path.join(chemin_booktoscrape, nom_categorie)
    os.makedirs(chemin_categorie, exist_ok=True)
    print(f"Le dossier de la catégorie {nom_categorie} est créé dans le dossier Booktoscrape")

    # Logique multipage et récupérer les données de chaque livre dans chaque page
    while True:
       
        # Récupération des urls des livres d'une page
        ulrs_livres = extraire_urls_livres(page_categorie) 

        # récupération des données des livres de la page initiale pour les stocker dans une variable
        for url_livre in ulrs_livres:
            page_livre_parse = recuperer_page(url_livre)

            resultat_page = extraire_donnees_livre(page_livre_parse, url_livre, chemin_categorie, nom_categorie)
            data_complete.extend(resultat_page)
        
        # Changement de page pour récuperer le reste des livres 
        urls_pages_suivante = []
        recherche_page_suivante = page_categorie.find("li", class_="next") 

        if recherche_page_suivante:
            lien_page_suivante = recherche_page_suivante.find('a')['href']
            url_categorie_sans_index = url_categorie_extraite.removesuffix("index.html")
            url_page_suivante = urljoin(url_categorie_sans_index, lien_page_suivante)
                  
            # Mettre à jour la variable `page_categorie` avec le contenu de la nouvelle page
            page_categorie = recuperer_page(url_page_suivante)

            # Récupération des urls des livres
            ulrs_livres = extraire_urls_livres(page_categorie) 

            # récupération des données des livres de la page initiale pour les stocker dans une variable
            for url_livre in ulrs_livres:
            # Traitement de la requete de la page livre
                page_livre_parse = recuperer_page(url_livre)

                resultat_page_suivante = extraire_donnees_livre(page_livre_parse, url_livre, chemin_categorie, nom_categorie)
                data_complete.extend(resultat_page_suivante)

        if not page_categorie.find("li", class_="next"):
            print(f"Fin de l'extraction de la catégorie {nom_categorie}")
            break

    i += 1
    print (f"{i} sur 50")
        
        
    # Création d'un csv pour stocker la réponse du site
    chemin_relatif_csv = Path(f"{chemin_categorie}/{nom_categorie}.csv")

    with open(chemin_relatif_csv, "w", newline='', encoding="utf-8-sig") as fichier:
        csv_writer = csv.writer(fichier, delimiter=";")
        csv_writer.writerow(DATA_HEADER)
        for ligne in data_complete:
            csv_writer.writerow(ligne)  

    print(f"Les données de la catégorie {nom_categorie} ont été écrites dans le CSV enregistré dans le dossier : booktoscrape/{nom_categorie} .")

 

