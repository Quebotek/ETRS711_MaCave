"""Script de test pour les nouvelles routes d'inventaire."""

from macave import create_app
from macave import db as db_module

app = create_app()

with app.app_context():
    db = db_module.Database("macave.db").__enter__()

    # Tester la route d'inventaire
    with app.test_client() as client:
        # Se connecter en tant qu'alice
        client.post("/auth/login", data={
            "username": "alice",
            "password": "password123"
        }, follow_redirects=True)

        # Tester l'inventaire
        response = client.get("/inventaire/")
        print(f"Status inventaire: {response.status_code}")
        print(f"Longueur réponse: {len(response.data)}")

        # Vérifier que les vins sont présents
        html = response.data.decode('utf-8')
        if "Château Montelena" in html:
            print(" Château Montelena trouvé dans l'inventaire")
        if "Mon Inventaire" in html:
            print(" Page d'inventaire chargée correctement")
        if "15.0" in html or "15,0" in html:
            print(" Note moyenne affichée")

        # Tester le détail d'un vin
        response = client.get("/inventaire/vin/1")
        print(f"\nStatus détail vin: {response.status_code}")
        html = response.data.decode('utf-8')
        if "Château Montelena" in html:
            print(" Page de détail du vin chargée")
        if "Note communautaire" in html:
            print(" Section de notation présente")

        # Tester le catalogue
        response = client.get("/catalogue/vins")
        print(f"\nStatus catalogue: {response.status_code}")
        html = response.data.decode('utf-8')
        if "Catalogue des vins" in html:
            print(" Page catalogue chargée")
        if "15.0" in html or "15,0" in html:
            print(" Notes affichées dans le catalogue")

    db.close()

print("\n Tests terminés !")
