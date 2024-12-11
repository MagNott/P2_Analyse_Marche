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

# url_livre = '/catalogue/the-long-shadow-of-small-ghosts-murder-and-memory-in-an-american-city_848/index.html'
# url_complete_livre = URL_RACINE + url_livre

# url_categorie = '/catalogue/category/books/fiction_10/index.html'
# url_complete_categorie = URL_RACINE + url_categorie

url_intermediaire_livre = 'https://books.toscrape.com/catalogue/'

# Requète pour récupérer un livre
# reponse = requests.get(url_complete_livre)
# if reponse.status_code != 200:
#     print(f"Erreur : La page {url_complete_livre} n'est pas accessible. Statut {reponse.status_code}")
#     exit()

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

data_complete = []


# DEFNITIONS DES FONCTIONS

def extraire_donnees_livre(page_livre, url_page_livre ):
    livres_extraits = []
    data = []

    # récupéation intermédiaires des données de la table dans la page
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

    # Contruction des data
    data.append(url_page_livre)

    # trouver le titre
    titre = page_livre.h1
    if not titre:
        print("Erreur : La balise <h1> qui conient le titre du livre n'a pas été trouvée")
        exit()
    data.append(titre.text)

    # trouver le code
    data.append(liste_info[0])

    # trouver les prix hors taxe et ttc
    data.append(liste_info[2])
    data.append(liste_info[3])

    # trouver le nombre dispo
    disponible = liste_info[5]
    nombre_disponible = re.findall(r"\d+", disponible)
    nombre_str = nombre_disponible[0]
    data.append(int(nombre_str))

    # trouver la description
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

    # trouver la categorie
    menu_categorie = page_livre.ul
    if not menu_categorie:
        print("Erreur : La balise <ul> qui contient la categorie n'a pas été trouvée")
        exit()
    liste = menu_categorie.find_all("li")
    categorie_a_extraire = liste[2]
    categorie = categorie_a_extraire.find("a")
    data.append(categorie.text)

    #trouver la note
    recherche_etoile = page_livre.find("p", class_="star-rating") 
    if not recherche_etoile:
        print("Erreur : La balise <p> avec la classe star-rating qui contient la note n'a pas été trouvée")
        exit()
    nombre_etoiles = recherche_etoile["class"]
    etoiles = nombre_etoiles[1]
    data.append(etoiles)

    # Trouver l'url de l'image
    recherche_url_image = page_livre.find("img", )
    if not recherche_url_image:
        print("Erreur : La balise <img> qui contient l'url de l'image n'a pas été trouvée")
        exit()
    url_relative_image = recherche_url_image['src']
    url_complete_image = URL_RACINE + url_relative_image
    data.append(url_complete_image)
    livres_extraits.append(data)
    return livres_extraits


def extraire_urls_livres(liste_livres_page) :
    liste_urls_livres  = []
    for livre in liste_livres_page:
        url_relative_livre = livre['href']
        if url_relative_livre not in liste_urls_livres :
            liste_urls_livres.append(url_relative_livre)

    return liste_urls_livres 


def recuperation_donnees_livre (liste_urls_livres):
    donnees_livres = []
    for url_livre in liste_urls_livres:
            url_livre_nettoyee = url_livre.lstrip("../")
            url_complete_livre = urljoin(url_intermediaire_livre, url_livre_nettoyee)
            reponse_livre = requests.get(url_complete_livre)
            
            if reponse.status_code != 200:
                print(f"Erreur : La page {url_complete_livre} n'est pas accessible. Statut {reponse.status_code}")
                exit()
            
            # Pour vérifier l'encodage de la page on print reponse.headers ou reponse.apparent_encoding
            reponse_livre.encoding = 'utf-8'

            # Traitement de la requete de la page livre
            page_livre_parse = BeautifulSoup(reponse_livre.text, features="html.parser")

            resultat = extraire_donnees_livre(page_livre_parse, url_complete_livre)
            donnees_livres.extend(resultat)
    return donnees_livres

def extraire_urls_categorie(page_courante) :
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




# LOGIQUE PRINCIPALE

# Requete pour récupérer une categorie
reponse = requests.get(URL_RACINE)
if reponse.status_code != 200:
    print(f"Erreur : La page {URL_RACINE} n'est pas accessible. Statut {reponse.status_code}")
    exit()

# Pour vérifier l'encodage de la page on print reponse.headers ou reponse.apparent_encoding
reponse.encoding = 'utf-8'

# Parse de la page avec beautiful soup
page = BeautifulSoup(reponse.text, features="html.parser")

urls_categories_extraites = extraire_urls_categorie(page)
i = 0

# Répertoire où le script est exécuté
dossier_courant = os.getcwd()
chemin_booktoscrape = os.path.join(dossier_courant, "booktoscrape")
os.makedirs(chemin_booktoscrape, exist_ok=True)

print("Le dossier Booktoscrape est créé")

for url_categorie_extraite in urls_categories_extraites:

    data_complete = []

    reponse = requests.get(url_categorie_extraite)
    if reponse.status_code != 200:
        print(f"Erreur : La page {url_categorie_extraite} n'est pas accessible. Statut {reponse.status_code}")
        exit()

    # Pour vérifier l'encodage de la page on print reponse.headers ou reponse.apparent_encoding
    reponse.encoding = 'utf-8'

    # Parse de la page avec beautiful soup
    page = BeautifulSoup(reponse.text, features="html.parser")

    nom_categorie = page.find('h1').text.strip().replace(" ", "-")

    print(f"Extraction de la catégorie {nom_categorie}...")

    chemin_categorie = os.path.join(chemin_booktoscrape, nom_categorie)
    os.makedirs(chemin_categorie, exist_ok=True)
    print(f"Le dossier de la catégorie {nom_categorie} est créé dans le dossier Booktoscrape")

    # Logique multipage et récupérer les données de chaque livre dans chaque page
    while True:
        # page.find("li", class_="next")

        # Récupération des urls des livres
        liste_livre = page.ol
        liste_livre_iteration = liste_livre.find_all("a")
        ulrs_livres = extraire_urls_livres(liste_livre_iteration) 

        # récupération des données des livre de la page initiale pour les stocker dans une variable
        data_complete.extend(recuperation_donnees_livre(ulrs_livres))
        
        # Changement de page pour récuperer le reste des livres 
        urls_pages_suivante = []
        recherche_page_suivant = page.find("li", class_="next") 
        if recherche_page_suivant:
           
            lien_page_suivante = recherche_page_suivant.find('a')['href']
            url_categorie_sans_index = url_categorie_extraite.removesuffix("index.html")
            url_page_suivante = urljoin(url_categorie_sans_index, lien_page_suivante)
        

            # Requete de la page suivante
            reponse_page = requests.get(url_page_suivante)

            if reponse_page.status_code != 200:
                print(f"Erreur : La page {url_page_suivante} n'est pas accessible. Statut {reponse_page.status_code}")
                break

            # Mettre à jour la variable `page` avec le contenu de la nouvelle page
            page = BeautifulSoup(reponse_page.text, features="html.parser")

            # Récupération des urls des livres
            liste_livre = page.ol
            liste_livre_iteration = liste_livre.find_all("a")
            ulrs_livres = extraire_urls_livres(liste_livre_iteration) 

            # récupération des données des livres de la page initiale pour les stocker dans une variable
            data_complete.extend(recuperation_donnees_livre(ulrs_livres))

        if not page.find("li", class_="next"):
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

 

