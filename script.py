import requests
from bs4 import BeautifulSoup
from pathlib import Path
import csv
import re
from urllib.parse import urljoin


# VARIABLES ET CONSTANTES GLOBALES

# Construction URL
URL_RACINE = 'https://books.toscrape.com'

# url_livre = '/catalogue/the-long-shadow-of-small-ghosts-murder-and-memory-in-an-american-city_848/index.html'
# url_complete_livre = URL_RACINE + url_livre

url_categorie = '/catalogue/category/books/mystery_3/index.html'
url_complete_categorie = URL_RACINE + url_categorie

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




# LOGIQUE PRINCIPALE

# Requete pour récupérer une categorie
reponse = requests.get(url_complete_categorie)
if reponse.status_code != 200:
    print(f"Erreur : La page {url_complete_categorie} n'est pas accessible. Statut {reponse.status_code}")
    exit()

# Pour vérifier l'encodage de la page on print reponse.headers ou reponse.apparent_encoding
reponse.encoding = 'utf-8'


# Parse de la page avec beautiful soup
page = BeautifulSoup(reponse.text, features="html.parser")


# Aller sur les pages suivantes
while page.find("li", class_="next"):
    if not page.find("li", class_="next"):
        print("Pas de page suivante trouvée. Fin de la boucle.")
        break

    url_intermediaire_livre = 'https://books.toscrape.com/catalogue/'

    # Récupération des urls des livres
    liste_livre = page.ol
    liste_livre_iteration = liste_livre.find_all("a")
    ulrs_livres = extraire_urls_livres(liste_livre_iteration) 

    for url_livre in ulrs_livres:
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
        data_complete.extend(resultat)
   
    urls_pages_suivante = []
    recherche_page_suivant = page.find("li", class_="next") 
    if not recherche_page_suivant:
        print("Erreur : La balise <li> avec la classe next qui contient le lien de la page suivante n'a pas été trouvée")
        exit()

    lien_page_suivante = recherche_page_suivant.find('a')['href']
    url_intermediaire_categorie = 'https://books.toscrape.com/catalogue/category/books/mystery_3/'
    url_page_suivante = urljoin(url_intermediaire_categorie, lien_page_suivante)
  

    reponse_page = requests.get(url_page_suivante)
    if reponse.status_code != 200:
        print(f"Erreur : La page {url_page_suivante} n'est pas accessible. Statut {reponse.status_code}")
        break

     # Mettre à jour la variable `page` avec le contenu de la nouvelle page
    page = BeautifulSoup(reponse_page.text, features="html.parser")

      # Récupération des urls des livres
    liste_livre = page.ol
    liste_livre_iteration = liste_livre.find_all("a")
    ulrs_livres = extraire_urls_livres(liste_livre_iteration) 

    url_intermediaire_livre = 'https://books.toscrape.com/catalogue/'
    for url_livre in ulrs_livres:
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
        data_complete.extend(resultat)
        
        print(data_complete)
        
# Création d'un csv pour stocker la réponse du site
chemin_relatif_csv = Path("data.csv")

with open(chemin_relatif_csv, "w", newline='', encoding="utf-8-sig") as fichier:
    csv_writer = csv.writer(fichier, delimiter=";")
    csv_writer.writerow(DATA_HEADER)
    for ligne in data_complete:
        csv_writer.writerow(ligne)  

print("Les données ont été écrites dans le CSV.")
# print (data_complete)


