import requests
from bs4 import BeautifulSoup
from pathlib import Path
import csv
import re

# Construction URL
url_racine = 'https://books.toscrape.com'
url_livre = '/catalogue/the-long-shadow-of-small-ghosts-murder-and-memory-in-an-american-city_848/index.html'
url_complete = url_racine + url_livre

# Requète pour récupérer un livre
reponse = requests.get(url_complete)
if reponse.status_code != 200:
    print(f"Erreur : La page {url_complete} n'est pas accessible. Statut {reponse.status_code}")
    exit()

# Pour vérifier l'encodage de la page on print reponse.headers ou reponse.apparent_encoding
reponse.encoding = 'utf-8'

# Préparation header pour le csv
data_header = ['product_page_url', 'universal_product_code', 'title', 'Price (excl. tax)', 'Price (incl. tax)', 'number_available', 'product_description', 'category', 'review_rating', 'image_url']

# Traitement de la requete
data = []
page = BeautifulSoup(reponse.text, features="html.parser")

# récupéation intermédiaires des données de la table dans la page
table = page.table
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
data.append(url_complete)

# trouver le titre
titre = page.h1
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
h2 = page.find("h2")
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
menu_categorie = page.ul
if not menu_categorie:
    print("Erreur : La balise <ul> qui contient la categorie n'a pas été trouvée")
    exit()
liste = menu_categorie.find_all("li")
categorie_a_extraire = liste[2]
categorie = categorie_a_extraire.find("a")
data.append(categorie.text)

#trouver la note
recherche_etoile = page.find("p", class_="star-rating") 
if not recherche_etoile:
    print("Erreur : La balise <p> avec la classe star-rating qui contient la note n'a pas été trouvée")
    exit()
nombre_etoiles = recherche_etoile["class"]
etoiles = nombre_etoiles[1]
data.append(etoiles)

# Trouver l'url de l'image
recherche_url_image = page.find("img", )
if not recherche_url_image:
    print("Erreur : La balise <img> qui contient l'url de l'image n'a pas été trouvée")
    exit()
url_relative_image = recherche_url_image['src']
url_complete_image = url_racine + url_relative_image
data.append(url_complete_image)


# Création d'un csv pour stocker la réponse du site
chemin_relatif_csv = Path("data.csv")

with open(chemin_relatif_csv, "w", newline='', encoding="utf-8-sig") as fichier:
    csv_writer = csv.writer(fichier, delimiter=",")
    csv_writer.writerow(data_header)
    csv_writer.writerow(data)  

print("Les données ont été écrites dans le CSV.")



