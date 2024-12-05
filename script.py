import requests
from bs4 import BeautifulSoup

# Requète pour vérifier qu'on récupère une réonse du site
reponse = requests.get('https://books.toscrape.com/index.html')
print(reponse.status_code)
