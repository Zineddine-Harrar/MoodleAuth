from flask import Flask, redirect
import requests
import urllib3
from urllib.parse import urlencode, quote
import logging
import os
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

# Désactiver les avertissements SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration Moodle
MOODLE_URL = "https://atalearn.captivante-rh.com"
H5P_EMBED_URL = "https://atalearn.captivante-rh.com/h5p/embed.php"
H5P_PACKAGE_URL = "https://atalearn.captivante-rh.com/pluginfile.php/32923/mod_h5pactivity/package/0/interactive-video-317.h5p"
H5P_COMPONENT = "mod_h5pactivity"

# Base de données des agents
AGENTS = {
    "ag20": {"username": "ag20", "token": "e9dea90aa3e84ba120eb3395647aa0d6"},
    # Ajoutez d'autres agents ici, par exemple:
    # "ag21": {"username": "ag21", "token": "token_de_ag21_ici"},
    # "ag22": {"username": "ag22", "token": "token_de_ag22_ici"},
}

app = Flask(__name__)

@app.route('/')
def index():
    agent_list = "<br>".join([f"Agent: {agent}" for agent in AGENTS.keys()])
    return f"<h1>Service d'accès vidéo en ligne</h1><p>Agents disponibles:</p><p>{agent_list}</p>"

@app.route('/video/<agent_id>')
def direct_video_access(agent_id):
    """Génère un lien frais et redirige directement vers la vidéo"""
    if agent_id not in AGENTS:
        logger.warning(f"Accès refusé: agent inconnu {agent_id}")
        return "Agent non reconnu", 404
    
    # Log de l'accès
    logger.info(f"Accès vidéo pour l'agent {agent_id} à {datetime.now()}")
    
    try:
        # Informations de l'agent
        agent = AGENTS[agent_id]
        
        # Génération du lien d'authentification
        auth_url = f"{MOODLE_URL}/webservice/rest/server.php"
        auth_params = {
            "wstoken": agent["token"],
            "wsfunction": "auth_userkey_request_login_url",
            "moodlewsrestformat": "json",
            "user[username]": agent["username"]
        }
        
        response = requests.post(auth_url, data=auth_params, verify=False)
        result = response.json()
        
        if 'loginurl' in result:
            # URL de la vidéo
            video_params = {
                "url": H5P_PACKAGE_URL,
                "component": H5P_COMPONENT
            }
            video_url = f"{H5P_EMBED_URL}?{urlencode(video_params)}"
            
            # URL finale
            final_url = f"{result['loginurl']}&wantsurl={quote(video_url)}"
            
            # Redirection immédiate
            return redirect(final_url)
        else:
            logger.error(f"Erreur API pour {agent_id}: {result}")
            return "Erreur de génération du lien", 500
    except Exception as e:
        logger.error(f"Exception pour {agent_id}: {str(e)}")
        return "Erreur technique", 500

if __name__ == '__main__':
    # Récupérer le port défini par Heroku ou utiliser 5000 par défaut
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
