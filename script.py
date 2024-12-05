import requests
from bs4 import BeautifulSoup
from pathlib import Path
import csv

# Requète pour vérifier qu'on récupère une réonse du site
reponse = requests.get('https://books.toscrape.com/index.html')
data = reponse.status_code
print(reponse.status_code)

# Création d'un csv pour stocker la réponse du site
chemin_relatif = Path("data.csv")

if Path.exists(chemin_relatif):
    with open(chemin_relatif, "r") as fichier:
        csv_reader = csv.reader(fichier)
else:
    with open(chemin_relatif, "w") as fichier:
       csv_writer = csv.writer(fichier)
       csv_writer.writerow([data])  # Écrire une ligne
