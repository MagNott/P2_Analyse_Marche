import requests
from bs4 import BeautifulSoup
from pathlib import Path
import csv
import re

url = 'https://books.toscrape.com/catalogue/the-long-shadow-of-small-ghosts-murder-and-memory-in-an-american-city_848/index.html'
# Requète pour vérifier qu'on récupère une réponse du site
reponse = requests.get(url)
# data = reponse.status_code
# print(reponse.text)

# Requète pour récupéer un livre
data_header = ['product_page_url', 'universal_product_code', 'title', 'Price (excl. tax)', 'Price (incl. tax)', 'number_available', 'product_description', 'category', 'review_rating', 'image_url'    ]
data = []
page = BeautifulSoup(reponse.text, features="html.parser")

table = page.table
liste_info = []

for row in table.find_all("tr"):
    for element in row.find_all("td"):
       liste_info.append(element.text)

data.append(url)
titre = page.h1
data.append(titre.text)

# trouver le code
data.append(liste_info[0])

# trouver les prix hors taxe et ttc
data.append(liste_info[2])
data.append(liste_info[3])

# trouver le nombre dispo
disponible = liste_info[5]
nombre_disponible = re.findall(r"\d+", disponible)
data.append(nombre_disponible)

# trouver la description
h2 = page.find("h2")
description = h2.find_next("p")
description_text = description.text
data.append(description_text)

# trouver la categorie
menu_categorie = page.ul
liste = menu_categorie.find_all("li")
categorie_a_extraire = liste[2]
categorie = categorie_a_extraire.find("a")
data.append(categorie.text)

#trouver la note
recherche_etoile = page.find("p", class_="star-rating") 
nombre_etoiles = recherche_etoile["class"]
etoiles = nombre_etoiles[1]
data.append(etoiles)

print(data)




# Création d'un csv pour stocker la réponse du site
# chemin_relatif = Path("data.csv")

# if Path.exists(chemin_relatif):
#     with open(chemin_relatif, "r") as fichier:
#         csv_reader = csv.reader(fichier)
# else:
#     with open(chemin_relatif, "w") as fichier:
#        csv_writer = csv.writer(fichier)
#        csv_writer.writerow([data])  # Écrire une ligne


