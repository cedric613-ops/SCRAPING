#!/usr/bin/env python3
"""
Bot Fnac avec intégration 2Captcha pour DataDome
"""

import time
import random
import json
import os
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class TwoCaptchaSolver:
    """Classe pour résoudre les captchas avec 2Captcha"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://2captcha.com"
    
    def solve_datadome(self, page_url, captcha_url):
        """Résout un captcha DataDome"""
        print("🔐 Envoi du captcha à 2Captcha...")
        
        # Envoyer le captcha
        params = {
            'key': self.api_key,
            'method': 'userrecaptcha',
            'googlekey': 'datadome',  # Pour DataDome
            'pageurl': page_url,
            'json': 1
        }
        
        try:
            response = requests.post(f"{self.base_url}/in.php", data=params, timeout=30)
            result = response.json()
            
            if result.get('status') != 1:
                print(f"❌ Erreur 2Captcha: {result}")
                return None
            
            captcha_id = result['request']
            print(f"✅ Captcha envoyé, ID: {captcha_id}")
            
            # Attendre la résolution (max 120 secondes)
            print("⏳ Attente de la résolution...")
            for attempt in range(24):  # 24 * 5s = 120s
                time.sleep(5)
                
                check_params = {
                    'key': self.api_key,
                    'action': 'get',
                    'id': captcha_id,
                    'json': 1
                }
                
                check_response = requests.get(f"{self.base_url}/res.php", params=check_params, timeout=30)
                check_result = check_response.json()
                
                if check_result.get('status') == 1:
                    token = check_result['request']
                    print(f"✅ Captcha résolu!")
                    return token
                elif check_result.get('request') == 'CAPCHA_NOT_READY':
                    print(f"⏳ En attente... ({attempt + 1}/24)")
                else:
                    print(f"⚠️ Status: {check_result.get('request')}")
            
            print("❌ Timeout: captcha non résolu dans le délai")
            return None
            
        except Exception as e:
            print(f"❌ Erreur lors de la résolution: {e}")
            return None

class FnacBot2Captcha:
    def __init__(self):
        self.driver = None
        self.email, self.password = self.load_credentials()
        
        # Charger la clé API 2Captcha
        load_dotenv()
        api_key = os.getenv("SOLVECAPTCHA_API_KEY")
        if api_key:
            self.captcha_solver = TwoCaptchaSolver(api_key)
            print("✅ 2Captcha configuré")
        else:
            self.captcha_solver = None
            print("⚠️ Pas de clé API 2Captcha - mode manuel")
        
    def load_credentials(self):
        try:
            with open('credentials.json') as f:
                data = json.load(f)
                return data.get('email'), data.get('password')
        except Exception as e:
            print(f"❌ Erreur lecture credentials: {e}")
            return None, None
    
    def human_delay(self, min_sec=1, max_sec=3):
        delay = random.uniform(min_sec, max_sec)
        print(f"⏳ Pause de {delay:.1f}s...")
        time.sleep(delay)
    
    def human_type(self, element, text):
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.1, 0.4))
    
    def init_driver(self):
        print("🔧 Initialisation du driver...")
        
        options = webdriver.ChromeOptions()
        
        # Mode headless (nécessaire sur Linux sans X)
        options.add_argument("--headless=new")
        
        # User agent réaliste
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        options.add_argument(f'user-agent={user_agent}')
        
        # Anti-détection
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--lang=fr-FR,fr")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
        }
        options.add_experimental_option("prefs", prefs)
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            print("✅ Driver initialisé")
            
            # Selenium-stealth
            stealth(driver,
                languages=["fr-FR", "fr"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            print("✅ Stealth activé")
            
            return driver
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return None
    
    def detect_datadome_captcha(self):
        """Détecte si un captcha DataDome est présent"""
        try:
            # Vérifier dans le titre
            if 'datadome' in self.driver.page_source.lower():
                return True
            
            # Vérifier les iframes DataDome
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                src = iframe.get_attribute("src") or ""
                if "captcha-delivery.com" in src or "datadome" in src:
                    return True
            
            return False
        except:
            return False
    
    def solve_datadome_if_present(self):
        """Résout le captcha DataDome s'il est présent"""
        if not self.detect_datadome_captcha():
            print("✅ Pas de captcha DataDome détecté")
            return True
        
        print("⚠️ Captcha DataDome détecté!")
        
        if not self.captcha_solver:
            print("❌ Pas de clé API 2Captcha configurée")
            print("📝 Résolution manuelle nécessaire...")
            input("Appuyez sur Entrée après avoir résolu le captcha manuellement...")
            return False
        
        # Résoudre avec 2Captcha
        current_url = self.driver.current_url
        token = self.captcha_solver.solve_datadome(current_url, current_url)
        
        if token:
            # Injecter le token (à adapter selon DataDome)
            print("💉 Injection du token...")
            try:
                self.driver.execute_script(f"""
                    // Tentative d'injection du token DataDome
                    if (window.datadome) {{
                        window.datadome.responseToken = '{token}';
                    }}
                """)
                self.human_delay(2, 4)
                
                # Recharger la page
                print("🔄 Rechargement de la page...")
                self.driver.refresh()
                self.human_delay(3, 5)
                
                return not self.detect_datadome_captcha()
            except Exception as e:
                print(f"❌ Erreur injection: {e}")
                return False
        
        return False
    
    def run(self):
        if not self.email or not self.password:
            return {"status": "error", "message": "Identifiants manquants"}
        
        try:
            self.driver = self.init_driver()
            if not self.driver:
                return {"status": "error", "message": "Driver non initialisé"}
            
            print("\n🚀 Début du test Fnac + 2Captcha")
            print("="*50)
            
            # Accès au site
            print("\n🌐 Accès à fnac.com...")
            self.driver.get("https://www.fnac.com/")
            self.human_delay(5, 8)
            
            # Sauvegarder pour analyse
            with open("fnac_page.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"📝 Titre: {self.driver.title}")
            
            # Vérifier et résoudre DataDome
            if self.detect_datadome_captcha():
                print("\n🔐 Captcha DataDome détecté!")
                
                if self.captcha_solver:
                    print("🤖 Tentative de résolution automatique avec 2Captcha...")
                    if self.solve_datadome_if_present():
                        print("✅ Captcha résolu avec succès!")
                    else:
                        print("❌ Échec de la résolution automatique")
                        print("💡 Pour DataDome, il faut souvent un service spécialisé")
                        print("💡 Alternatives: CapSolver, CapMonster, ou résolution manuelle")
                        return {"status": "captcha", "message": "DataDome non résolu"}
                else:
                    print("⚠️ Pas de solver configuré")
                    return {"status": "captcha", "message": "DataDome présent, pas de solver"}
            
            # Si pas de captcha ou captcha résolu, continuer
            print("\n✅ Page accessible, prêt pour la connexion!")
            print(f"URL actuelle: {self.driver.current_url}")
            
            return {"status": "success", "message": "Test réussi"}
            
        except KeyboardInterrupt:
            return {"status": "interrupted"}
        except Exception as e:
            print(f"\n❌ ERREUR: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            if self.driver:
                print("\n🧹 Fermeture...")
                self.human_delay(2, 3)
                self.driver.quit()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 FNAC BOT avec 2CAPTCHA - POC")
    print("="*60)
    
    bot = FnacBot2Captcha()
    result = bot.run()
    
    print("\n" + "="*60)
    print(f"📊 RÉSULTAT: {result}")
    print("="*60 + "\n")


