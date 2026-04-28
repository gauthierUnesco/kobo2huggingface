import requests
import json
from huggingface_hub import HfApi
import os

# ---- Config ----
KOBO_TOKEN = os.environ["KOBO_TOKEN"]
HF_TOKEN   = os.environ["HF_TOKEN"]
KOBO_URL   = "https://kf.kobotoolbox.org"
HF_REPO    = "ggauthier/KoboTest"

# ---- Init ----
api     = HfApi()
headers = {"Authorization": f"Token {KOBO_TOKEN}"}

# Charger la liste des formulaires
with open("forms.json", "r") as f:
    forms = json.load(f)

# Récupérer tous les fichiers déjà présents sur HuggingFace (pour éviter les doublons)
existing_files = set(
    api.list_repo_files(repo_id=HF_REPO, repo_type="dataset", token=HF_TOKEN)
)
print(f"📦 {len(existing_files)} fichiers déjà présents sur HuggingFace\n")

# ---- Boucle sur les formulaires ----
for form in forms:
    form_uid  = form["uid"]
    form_name = form["name"]
    print(f"📋 Traitement du formulaire : {form_name} ({form_uid})")

    # Récupérer les soumissions
    response = requests.get(
        f"{KOBO_URL}/api/v2/assets/{form_uid}/data/",
        headers=headers
    )
    submissions = response.json().get("results", [])
    print(f"   → {len(submissions)} soumissions trouvées")

    for submission in submissions:
        # Identifiant unique de la soumission (toujours présent dans KoboToolbox)
        submission_id = submission.get("_uuid", submission.get("_id"))
        attachments   = submission.get("_attachments", [])

        if not attachments:
            continue

        for attachment in attachments:
            # Nom du fichier original (KoboToolbox donne un chemin type "uid/filename.jpg")
            original_name = attachment["filename"].split("/")[-1]

            # Chemin dans le repo HuggingFace
            # Structure : form_name / submission_uuid / fichier
            hf_path = f"{form_name}/{submission_id}/{original_name}"

            # Vérifier si le fichier existe déjà → on skip
            if hf_path in existing_files:
                print(f"   ⏭️  Déjà uploadé : {hf_path}")
                continue

            # Télécharger depuis KoboToolbox
            file_response = requests.get(attachment["download_url"], headers=headers)

            if file_response.status_code != 200:
                print(f"   ❌ Erreur téléchargement : {original_name}")
                continue

            # Uploader sur HuggingFace
            api.upload_file(
                path_or_fileobj=file_response.content,
                path_in_repo=hf_path,
                repo_id=HF_REPO,
                repo_type="dataset",
                token=HF_TOKEN
            )
            print(f"   ✅ Uploadé : {hf_path}")

print("\n✨ Synchronisation terminée !")