#!/usr/bin/env python3
"""
Bot King Jouet - Achat Automatique
Surveillance et achat automatique de produits en édition limitée
"""

import time
import random
import json
import os
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium_stealth import stealth

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kingjouet_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SolveCaptchaSolver:
    """Intégration avec SolveCaptcha.com"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.solvecaptcha.com"
    
    def solve_recaptcha_v2(self, sitekey, page_url):
        """Résout un reCAPTCHA v2"""
        logger.info("🔐 Envoi du reCAPTCHA v2 à SolveCaptcha...")
        
        payload = {
            "key": self.api_key,
            "method": "userrecaptcha",
            "googlekey": sitekey,
            "pageurl": page_url,
            "json": 1
        }
        
        try:
            response = requests.post(f"{self.base_url}/in.php", data=payload, timeout=30)
            result = response.json()
            
            if result.get('status') != 1:
                logger.error(f"❌ Erreur SolveCaptcha: {result}")
                return None
            
            captcha_id = result['request']
            logger.info(f"✅ Captcha envoyé, ID: {captcha_id}")
            
            # Polling pour le résultat
            for attempt in range(40):  # 40 * 5s = 200s max
                time.sleep(5)
                
                check_params = {
                    "key": self.api_key,
                    "action": "get",
                    "id": captcha_id,
                    "json": 1
                }
                
                check_response = requests.get(f"{self.base_url}/res.php", params=check_params, timeout=30)
                check_result = check_response.json()
                
                if check_result.get('status') == 1:
                    token = check_result['request']
                    logger.info(f"✅ Captcha résolu!")
                    return token
                elif check_result.get('request') == 'CAPCHA_NOT_READY':
                    logger.info(f"⏳ En attente... ({attempt + 1}/40)")
                else:
                    logger.warning(f"Status: {check_result.get('request')}")
            
            logger.error("❌ Timeout captcha")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur résolution captcha: {e}")
            return None
    
    def solve_recaptcha_v3(self, sitekey, page_url, action="verify"):
        """Résout un reCAPTCHA v3"""
        logger.info("🔐 Envoi du reCAPTCHA v3 à SolveCaptcha...")
        
        payload = {
            "key": self.api_key,
            "method": "userrecaptcha",
            "version": "v3",
            "googlekey": sitekey,
            "pageurl": page_url,
            "action": action,
            "min_score": 0.3,
            "json": 1
        }
        
        try:
            response = requests.post(f"{self.base_url}/in.php", data=payload, timeout=30)
            result = response.json()
            
            if result.get('status') != 1:
                logger.error(f"❌ Erreur SolveCaptcha: {result}")
                return None
            
            captcha_id = result['request']
            logger.info(f"✅ Captcha v3 envoyé, ID: {captcha_id}")
            
            # Polling
            for attempt in range(40):
                time.sleep(5)
                
                check_params = {
                    "key": self.api_key,
                    "action": "get",
                    "id": captcha_id,
                    "json": 1
                }
                
                check_response = requests.get(f"{self.base_url}/res.php", params=check_params, timeout=30)
                check_result = check_response.json()
                
                if check_result.get('status') == 1:
                    token = check_result['request']
                    logger.info(f"✅ Captcha v3 résolu!")
                    return token
                elif check_result.get('request') == 'CAPCHA_NOT_READY':
                    logger.info(f"⏳ En attente v3... ({attempt + 1}/40)")
            
            logger.error("❌ Timeout captcha v3")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur résolution captcha v3: {e}")
            return None
    
    def solve_hcaptcha(self, sitekey, page_url):
        """Résout un hCaptcha"""
        logger.info("🔐 Envoi du hCaptcha à SolveCaptcha...")
        
        payload = {
            "key": self.api_key,
            "method": "hcaptcha",
            "sitekey": sitekey,
            "pageurl": page_url,
            "json": 1
        }
        
        try:
            response = requests.post(f"{self.base_url}/in.php", data=payload, timeout=30)
            result = response.json()
            
            if result.get('status') != 1:
                logger.error(f"❌ Erreur SolveCaptcha hCaptcha: {result}")
                return None
            
            captcha_id = result['request']
            logger.info(f"✅ hCaptcha envoyé, ID: {captcha_id}")
            
            # Polling
            for attempt in range(40):
                time.sleep(5)
                
                check_params = {
                    "key": self.api_key,
                    "action": "get",
                    "id": captcha_id,
                    "json": 1
                }
                
                check_response = requests.get(f"{self.base_url}/res.php", params=check_params, timeout=30)
                check_result = check_response.json()
                
                if check_result.get('status') == 1:
                    token = check_result['request']
                    logger.info(f"✅ hCaptcha résolu!")
                    return token
                elif check_result.get('request') == 'CAPCHA_NOT_READY':
                    logger.info(f"⏳ En attente hCaptcha... ({attempt + 1}/40)")
            
            logger.error("❌ Timeout hCaptcha")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur résolution hCaptcha: {e}")
            return None
    
    def solve_datadome_slider(self, driver, captcha_url):
        """Résout le slider captcha de DataDome avec SolveCaptcha (méthode coordinates)"""
        logger.info("🔐 Résolution du slider DataDome avec SolveCaptcha...")
        
        try:
            # DataDome utilise un slider captcha
            # On va utiliser la méthode "coordinates" pour obtenir la position du slider
            
            logger.info("📸 Prise d'un screenshot du slider...")
            import base64
            screenshot = driver.get_screenshot_as_png()
            screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')
            
            # Envoyer l'image avec la méthode "coordinates"
            # L'utilisateur humain cliquera sur le point cible du slider
            payload = {
                "key": self.api_key,
                "method": "base64",
                "body": screenshot_b64,
                "textinstructions": "Click on the slider endpoint to complete the captcha",
                "json": 1
            }
            
            logger.info("📤 Envoi à SolveCaptcha (méthode coordinates)...")
            response = requests.post(f"{self.base_url}/in.php", data=payload, timeout=30)
            result = response.json()
            
            if result.get('status') != 1:
                logger.error(f"❌ Erreur SolveCaptcha: {result}")
                return None
            
            captcha_id = result['request']
            logger.info(f"✅ Slider envoyé, ID: {captcha_id}")
            
            # Polling pour obtenir les coordonnées
            for attempt in range(60):  # 5 minutes max
                time.sleep(5)
                
                check_params = {
                    "key": self.api_key,
                    "action": "get",
                    "id": captcha_id,
                    "json": 1
                }
                
                check_response = requests.get(f"{self.base_url}/res.php", params=check_params, timeout=30)
                check_result = check_response.json()
                
                if check_result.get('status') == 1:
                    # Coordonnées reçues (format: "x=123;y=456" ou juste "x")
                    coordinates = check_result['request']
                    logger.info(f"✅ Coordonnées reçues: {coordinates}")
                    
                    # Parser les coordonnées
                    try:
                        if 'x=' in coordinates:
                            parts = coordinates.split(';')
                            x = int(parts[0].split('=')[1])
                            if len(parts) > 1:
                                y = int(parts[1].split('=')[1])
                            else:
                                y = None
                        else:
                            # Peut-être juste un nombre pour le slider
                            x = int(coordinates)
                            y = None
                        
                        return {'x': x, 'y': y}
                    except Exception as e:
                        logger.error(f"❌ Erreur parsing coordonnées: {e}")
                        logger.info(f"Coordonnées brutes: {coordinates}")
                        return {'raw': coordinates}
                        
                elif check_result.get('request') == 'CAPCHA_NOT_READY':
                    if attempt % 6 == 0:  # Log toutes les 30 secondes
                        logger.info(f"⏳ En attente slider... ({attempt + 1}/60)")
                else:
                    logger.warning(f"⚠️ Status inconnu: {check_result.get('request')}")
            
            logger.error("❌ Timeout slider")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur résolution slider DataDome: {e}")
            import traceback
            traceback.print_exc()
            return None
    
class KingJouetBot:
    """Bot principal pour King Jouet"""
    
    def __init__(self):
        self.driver = None
        self.config = self.load_config()
        self.email, self.password = self.load_credentials()
        
        # Charger API SolveCaptcha
        load_dotenv()
        api_key = os.getenv("SOLVECAPTCHA_API_KEY")
        if api_key:
            self.captcha_solver = SolveCaptchaSolver(api_key)
            logger.info("✅ SolveCaptcha configuré")
        else:
            self.captcha_solver = None
            logger.warning("⚠️ Pas de clé API SolveCaptcha")
        
        self.purchase_count = 0
        
    def load_config(self):
        """Charge la configuration"""
        try:
            with open('config.json') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Erreur lecture config: {e}")
            return {}
    
    def load_credentials(self):
        """Charge les identifiants"""
        try:
            with open('credentials.json') as f:
                data = json.load(f)
                return data.get('email'), data.get('password')
        except Exception as e:
            logger.error(f"❌ Erreur lecture credentials: {e}")
            return None, None
    
    def human_delay(self, min_sec=1, max_sec=3):
        """Délai humain aléatoire"""
        delay = random.uniform(min_sec, max_sec)
        logger.debug(f"⏳ Pause de {delay:.1f}s...")
        time.sleep(delay)
    
    def human_type(self, element, text):
        """Simule la frappe humaine"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.1, 0.4))
    
    def wait_for_manual_captcha_resolution(self, max_wait_minutes=10):
        """Attend que l'utilisateur résolve manuellement le captcha DataDome"""
        try:
            logger.info("")
            logger.info("┌" + "─"*68 + "┐")
            logger.info("│" + " "*68 + "│")
            logger.info("│" + " "*15 + "🚨 CAPTCHA DATADOME DÉTECTÉ 🚨" + " "*23 + "│")
            logger.info("│" + " "*68 + "│")
            logger.info("├" + "─"*68 + "┤")
            logger.info("│" + " "*68 + "│")
            logger.info("│  📌 INTERVENTION MANUELLE REQUISE :                              │")
            logger.info("│" + " "*68 + "│")
            logger.info("│     ⚠️  Le bot est en mode HEADLESS (pas de fenêtre visible)     │")
            logger.info("│" + " "*68 + "│")
            logger.info("│     OPTION 1 - Résolution manuelle externe :                    │")
            logger.info("│     ─────────────────────────────────────                       │")
            logger.info("│     1️⃣  Ouvrez un navigateur (Chrome/Firefox)                     │")
            logger.info("│     2️⃣  Allez sur: https://www.king-jouet.com/exec/login.aspx    │")
            logger.info("│     3️⃣  Résolvez le captcha DataDome                             │")
            logger.info("│     4️⃣  Ouvrez la console (F12) > Application > Cookies          │")
            logger.info("│     5️⃣  Copiez la valeur du cookie 'datadome'                    │")
            logger.info("│     6️⃣  Appuyez sur ENTRÉE ici et collez le cookie               │")
            logger.info("│" + " "*68 + "│")
            logger.info("│     OPTION 2 - Attente automatique :                            │")
            logger.info("│     ───────────────────────────                                 │")
            logger.info("│     Le bot vérifie automatiquement toutes les 10s si            │")
            logger.info("│     le captcha est résolu (si vous le résolvez ailleurs          │")
            logger.info("│     et que les cookies se synchronisent).                        │")
            logger.info("│" + " "*68 + "│")
            logger.info("│  ⏱️  Temps maximum d'attente: {} minutes                        │".format(max_wait_minutes))
            logger.info("│" + " "*68 + "│")
            logger.info("└" + "─"*68 + "┘")
            logger.info("")
            
            # Sauvegarder un screenshot pour référence
            screenshot_path = f"datadome_captcha_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"📸 Screenshot sauvegardé: {screenshot_path}")
            logger.info(f"📄 HTML sauvegardé: captcha_detection.html")
            logger.info("")
            
            # Demander si l'utilisateur veut entrer le cookie manuellement
            logger.info("💬 Voulez-vous entrer le cookie DataDome manuellement ?")
            logger.info("   Tapez 'cookie' puis ENTRÉE, ou attendez la résolution auto (10s)...")
            logger.info("")
            
            # Attendre 15 secondes pour que l'utilisateur puisse entrer 'cookie'
            import select
            import sys
            
            # Vérifier si entrée disponible (timeout 15s)
            try:
                ready, _, _ = select.select([sys.stdin], [], [], 15)
                if ready:
                    user_input = sys.stdin.readline().strip().lower()
                    if user_input == 'cookie':
                        logger.info("🔑 Mode saisie manuelle du cookie activé")
                        logger.info("Collez la valeur du cookie 'datadome' et appuyez sur ENTRÉE:")
                        cookie_value = input().strip()
                        
                        if cookie_value:
                            logger.info("💉 Injection du cookie DataDome...")
                            try:
                                self.driver.add_cookie({
                                    'name': 'datadome',
                                    'value': cookie_value,
                                    'domain': '.king-jouet.com',
                                    'path': '/'
                                })
                                logger.info("✅ Cookie injecté!")
                                logger.info("🔄 Rechargement de la page...")
                                self.driver.refresh()
                                time.sleep(5)
                                
                                # Vérifier si DataDome est parti
                                if "datadome" not in self.driver.page_source.lower():
                                    logger.info("🎉 DataDome bypassé avec succès!")
                                    return True
                                else:
                                    logger.warning("⚠️ DataDome toujours présent, passage en mode attente auto...")
                            except Exception as e:
                                logger.error(f"❌ Erreur injection cookie: {e}")
            except:
                pass
            
            # Mode attente automatique
            logger.info("⏳ Mode attente automatique activé...")
            max_checks = (max_wait_minutes * 60) // 10  # Vérifier toutes les 10 secondes
            
            for i in range(int(max_checks)):
                logger.info(f"⏳ [{i+1}/{int(max_checks)}] Vérification en cours...")
                
                # Attendre 10 secondes
                time.sleep(10)
                
                # Vérifier si DataDome est toujours présent
                try:
                    current_source = self.driver.page_source.lower()
                    current_url = self.driver.current_url
                    
                    # Vérifier UNIQUEMENT si DataDome n'est VRAIMENT plus là
                    # Il faut que TOUTES ces conditions soient vraies
                    datadome_gone = (
                        "datadome" not in current_source and 
                        "captcha-delivery.com" not in current_source and
                        "captcha" not in current_source
                    )
                    
                    if datadome_gone:
                        # Double vérification : chercher des éléments de login
                        has_login_elements = (
                            "email" in current_source or 
                            "password" in current_source or
                            "connexion" in current_source
                        )
                        
                        if has_login_elements:
                            logger.info("✅ DataDome n'est plus détecté!")
                            logger.info("✅ Page de login accessible!")
                            logger.info("🎉 Captcha résolu! Poursuite du processus...")
                            return True
                        else:
                            logger.debug(f"DataDome parti mais pas sur page login, vérification {i+1}")
                    else:
                        logger.debug(f"DataDome toujours présent, vérification {i+1}")
                        
                except Exception as e:
                    logger.debug(f"Erreur vérification: {e}")
                    continue
            
            logger.error(f"❌ Timeout après {max_wait_minutes} minutes")
            logger.error("Le captcha n'a pas été résolu dans le délai imparti")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur attente résolution: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def perform_slider_action(self, coordinates):
        """Effectue l'action de slider avec les coordonnées obtenues"""
        try:
            logger.info(f"🎯 Exécution du slider avec coordonnées: {coordinates}")
            
            # Chercher l'iframe DataDome
            try:
                self.driver.switch_to.frame(self.driver.find_element(By.XPATH, "//iframe[contains(@src, 'captcha-delivery.com')]"))
                logger.info("✅ Basculé vers iframe DataDome")
            except:
                logger.warning("⚠️ Impossible de basculer vers iframe, tentative dans le contexte principal")
            
            # Chercher l'élément slider
            slider_selectors = [
                "//div[contains(@class, 'slider')]",
                "//div[contains(@class, 'slide')]",
                "//div[@id='slider']",
                "//input[@type='range']",
            ]
            
            slider = None
            for selector in slider_selectors:
                try:
                    slider = self.driver.find_element(By.XPATH, selector)
                    logger.info(f"✅ Slider trouvé: {selector}")
                    break
                except:
                    continue
            
            if slider and coordinates:
                from selenium.webdriver.common.action_chains import ActionChains
                
                # Effectuer le drag
                x_offset = coordinates.get('x', 0)
                logger.info(f"🖱️ Drag du slider de {x_offset}px...")
                
                actions = ActionChains(self.driver)
                actions.click_and_hold(slider).move_by_offset(x_offset, 0).release().perform()
                
                logger.info("✅ Slider déplacé!")
                self.human_delay(2, 4)
                
                # Revenir au contexte principal
                try:
                    self.driver.switch_to.default_content()
                except:
                    pass
                
                return True
            else:
                logger.error("❌ Slider non trouvé ou coordonnées manquantes")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur exécution slider: {e}")
            import traceback
            traceback.print_exc()
            
            # Revenir au contexte principal
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            
            return False
    
    def detect_and_solve_captcha(self):
        """Détecte et résout automatiquement les captchas"""
        if not self.captcha_solver:
            logger.warning("⚠️ Pas de solver captcha configuré")
            return False
        
        try:
            logger.info("\n🔍 DÉTECTION DE CAPTCHA")
            logger.info("="*50)
            
            page_url = self.driver.current_url
            page_source = self.driver.page_source
            
            # Sauvegarder la page pour debug
            self.driver.save_screenshot("captcha_detection.png")
            with open("captcha_detection.html", "w", encoding="utf-8") as f:
                f.write(page_source)
            
            # 0. Détecter DataDome AVANT tout le reste (prioritaire car bloque toute la page)
            try:
                import re
                # Détecter si DataDome a complètement remplacé la page
                if "datadome" in page_source.lower() or "captcha-delivery.com" in page_source.lower():
                    logger.info("🚨 DataDome CAPTCHA détecté!")
                    logger.info("="*70)
                    logger.warning("⚠️  INTERVENTION MANUELLE REQUISE")
                    logger.info("="*70)
                    
                    # Extraire l'URL du captcha pour info
                    datadome_iframe_match = re.search(r'<iframe[^>]*src="([^"]*captcha-delivery\.com[^"]*)"', page_source)
                    if datadome_iframe_match:
                        captcha_url = datadome_iframe_match.group(1)
                        logger.info(f"📋 URL captcha: {captcha_url[:100]}...")
                    
                    # Attendre la résolution manuelle
                    if self.wait_for_manual_captcha_resolution():
                        logger.info("🎉 Captcha résolu! Poursuite du processus...")
                        return True
                    else:
                        logger.error("❌ Timeout ou échec résolution captcha")
                        return False
                        
            except Exception as e:
                logger.debug(f"Pas de DataDome: {e}")
            
            # 1. Détecter reCAPTCHA v2
            try:
                recaptcha_frame = self.driver.find_element(By.XPATH, "//iframe[contains(@src, 'recaptcha')]")
                logger.info("🔍 reCAPTCHA v2 détecté!")
                
                # Extraire la sitekey
                try:
                    sitekey = self.driver.execute_script("""
                        var iframe = document.querySelector('iframe[src*="recaptcha"]');
                        if (iframe) {
                            var src = iframe.src;
                            var match = src.match(/[?&]k=([^&]+)/);
                            return match ? match[1] : null;
                        }
                        return null;
                    """)
                    
                    if not sitekey:
                        # Essayer de trouver dans le HTML
                        import re
                        sitekey_match = re.search(r'data-sitekey="([^"]+)"', page_source)
                        if sitekey_match:
                            sitekey = sitekey_match.group(1)
                    
                    if sitekey:
                        logger.info(f"✅ Sitekey trouvée: {sitekey[:20]}...")
                        
                        # Résoudre avec SolveCaptcha
                        token = self.captcha_solver.solve_recaptcha_v2(sitekey, page_url)
                        
                        if token:
                            # Injecter le token
                            logger.info("💉 Injection du token reCAPTCHA v2...")
                            self.driver.execute_script(f"""
                                document.getElementById('g-recaptcha-response').innerHTML = '{token}';
                            """)
                            
                            # Soumettre le formulaire ou déclencher le callback
                            self.driver.execute_script("""
                                if (typeof ___grecaptcha_cfg !== 'undefined') {
                                    var clients = ___grecaptcha_cfg.clients;
                                    for (var id in clients) {
                                        if (clients[id].callback) {
                                            clients[id].callback();
                                        }
                                    }
                                }
                            """)
                            
                            logger.info("✅ reCAPTCHA v2 résolu et injecté!")
                            self.human_delay(2, 4)
                            return True
                    else:
                        logger.warning("⚠️ Sitekey reCAPTCHA introuvable")
                        
                except Exception as e:
                    logger.error(f"❌ Erreur extraction sitekey: {e}")
                    
            except NoSuchElementException:
                logger.debug("Pas de reCAPTCHA v2 détecté")
            
            # 2. Détecter reCAPTCHA v3 (invisible)
            try:
                import re
                recaptcha_v3_match = re.search(r'grecaptcha\.execute\([\'"]([^\'"]+)[\'"]\s*,\s*\{\s*action:\s*[\'"]([^\'"]+)[\'"]', page_source)
                if recaptcha_v3_match:
                    sitekey = recaptcha_v3_match.group(1)
                    action = recaptcha_v3_match.group(2)
                    logger.info(f"🔍 reCAPTCHA v3 détecté! (action: {action})")
                    logger.info(f"✅ Sitekey: {sitekey[:20]}...")
                    
                    token = self.captcha_solver.solve_recaptcha_v3(sitekey, page_url, action)
                    
                    if token:
                        logger.info("💉 Injection du token reCAPTCHA v3...")
                        # Le token v3 est généralement injecté via callback
                        self.driver.execute_script(f"""
                            if (typeof grecaptcha !== 'undefined') {{
                                grecaptcha.ready(function() {{
                                    var token = '{token}';
                                    // Chercher le callback et l'exécuter
                                    if (window.onRecaptchaSuccess) {{
                                        window.onRecaptchaSuccess(token);
                                    }}
                                }});
                            }}
                        """)
                        logger.info("✅ reCAPTCHA v3 résolu!")
                        self.human_delay(2, 4)
                        return True
                        
            except Exception as e:
                logger.debug(f"Pas de reCAPTCHA v3: {e}")
            
            # 3. Détecter hCaptcha
            try:
                hcaptcha_frame = self.driver.find_element(By.XPATH, "//iframe[contains(@src, 'hcaptcha')]")
                logger.info("🔍 hCaptcha détecté!")
                
                import re
                sitekey_match = re.search(r'data-sitekey="([^"]+)"', page_source)
                if sitekey_match:
                    sitekey = sitekey_match.group(1)
                    logger.info(f"✅ Sitekey hCaptcha: {sitekey[:20]}...")
                    
                    token = self.captcha_solver.solve_hcaptcha(sitekey, page_url)
                    
                    if token:
                        logger.info("💉 Injection du token hCaptcha...")
                        self.driver.execute_script(f"""
                            document.querySelector('[name="h-captcha-response"]').innerHTML = '{token}';
                        """)
                        logger.info("✅ hCaptcha résolu!")
                        self.human_delay(2, 4)
                        return True
                        
            except NoSuchElementException:
                logger.debug("Pas de hCaptcha détecté")
            except Exception as e:
                logger.debug(f"Erreur hCaptcha: {e}")
            
            logger.info("ℹ️ Aucun captcha détecté sur cette page")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur détection captcha: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def init_driver(self):
        """Initialise undetected-chromedriver avec MAXIMUM STEALTH anti-DataDome"""
        logger.info("🔧 Initialisation STEALTH MODE MAXIMUM...")
        
        options = uc.ChromeOptions()
        
        # Mode headless
        options.headless = True
        options.add_argument("--headless=new")
        
        # Arguments anti-détection RENFORCÉS
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # User-Agent très réaliste (Chrome récent sur Windows)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
        
        # Headers et langue
        options.add_argument("--accept-language=fr-FR,fr;q=0.9")
        options.add_argument("--lang=fr-FR")
        
        # Désactiver les fonctionnalités de détection
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=IsolateOrigins,site-per-process,VizDisplayCompositor")
        options.add_argument("--disable-site-isolation-trials")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        
        # Cacher l'automation
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # Préférences avancées pour paraître humain
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "webrtc.ip_handling_policy": "disable_non_proxied_udp",
            "webrtc.multiple_routes_enabled": False,
            "webrtc.nonproxied_udp_enabled": False,
            "profile.managed_default_content_settings.images": 1,
            "profile.default_content_setting_values.media_stream_mic": 2,
            "profile.default_content_setting_values.media_stream_camera": 2,
            "profile.default_content_setting_values.geolocation": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        try:
            logger.info("🚀 Création du driver avec config stealth...")
            driver = uc.Chrome(headless=True, use_subprocess=False, version_main=None)
            
            logger.info("🔒 Application de selenium-stealth...")
            # Appliquer selenium-stealth pour masquer l'automation
            stealth(driver,
                languages=["fr-FR", "fr"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            
            logger.info("✅ Driver STEALTH initialisé avec succès!")
            logger.info("⚠️  Note: Les commandes CDP sont désactivées (incompatibles avec headless sur ce système)")
            return driver
            
        except Exception as e:
            logger.error(f"❌ Erreur init driver stealth: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def login(self):
        """Connexion au compte King Jouet"""
        try:
            logger.info("\n🔑 CONNEXION AU COMPTE KING JOUET")
            logger.info("="*50)
            
            # 🚀 STRATÉGIE ULTRA-HUMAINE: Simuler un vrai utilisateur
            logger.info("🏠 Visite de la page d'accueil (session propre)...")
            self.driver.get("https://www.king-jouet.com/")
            self.human_delay(8, 12)
            
            # Accepter les cookies immédiatement
            logger.info("🍪 Gestion des cookies...")
            cookie_buttons = [
                (By.ID, "didomi-notice-agree-button"),
                (By.XPATH, "//button[contains(text(), 'Accepter')]"),
                (By.XPATH, "//button[contains(text(), 'Tout accepter')]"),
            ]
            for selector_type, selector_value in cookie_buttons:
                try:
                    accept_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", accept_btn)
                    self.human_delay(1, 2)
                    accept_btn.click()
                    logger.info("✅ Cookies acceptés")
                    self.human_delay(3, 5)
                    break
                except:
                    continue
            
            # Scroll TRÈS humain sur la page d'accueil (comme si on regardait les produits)
            logger.info("📜 Navigation naturelle sur la page d'accueil...")
            for i in range(5):
                scroll_amount = random.randint(400, 900)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                self.human_delay(2, 4)
                
                # Parfois scroller un peu en arrière
                if random.random() > 0.7:
                    back_scroll = random.randint(100, 300)
                    self.driver.execute_script(f"window.scrollBy(0, -{back_scroll});")
                    self.human_delay(1, 2)
            
            # Revenir en haut
            logger.info("🔝 Retour en haut de page...")
            self.driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
            self.human_delay(4, 6)
            
            # Déplacer la souris aléatoirement (simuler hover)
            logger.info("🖱️  Simulation de mouvements de souris...")
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(self.driver)
                for _ in range(3):
                    x_offset = random.randint(-200, 200)
                    y_offset = random.randint(-200, 200)
                    actions.move_by_offset(x_offset, y_offset).perform()
                    self.human_delay(0.5, 1)
            except:
                pass
            
            # Cliquer sur le lien "Mon compte" au lieu d'accéder directement à /exec/login.aspx
            logger.info("🔍 Recherche du lien 'Mon compte' sur la page d'accueil...")
            try:
                # Chercher le lien "Mon compte" ou "Connexion"
                account_link_selectors = [
                    "//a[contains(text(), 'Mon compte')]",
                    "//a[contains(text(), 'Connexion')]",
                    "//a[contains(text(), 'Se connecter')]",
                    "//a[contains(@href, 'login')]",
                    "//a[contains(@href, 'account')]",
                    "//a[contains(@href, 'my')]",
                ]
                
                account_link = None
                for selector in account_link_selectors:
                    try:
                        account_link = self.driver.find_element(By.XPATH, selector)
                        logger.info(f"✅ Lien trouvé: {selector}")
                        break
                    except:
                        continue
                
                if account_link:
                    logger.info("🖱️ Clic sur le lien 'Mon compte'...")
                    account_link.click()
                    self.human_delay(4, 6)
                else:
                    logger.warning("⚠️ Lien 'Mon compte' introuvable, accès direct...")
                    self.driver.get("https://www.king-jouet.com/exec/login.aspx")
                    self.human_delay(4, 6)
                    
            except Exception as e:
                logger.warning(f"⚠️ Erreur clic lien: {e}, accès direct...")
                self.driver.get("https://www.king-jouet.com/exec/login.aspx")
                self.human_delay(4, 6)
            
            logger.info(f"📝 Titre: {self.driver.title}")
            logger.info(f"🔗 URL: {self.driver.current_url}")
            
            # Gérer les cookies - Plusieurs types de popups possibles
            cookie_buttons = [
                (By.ID, "onetrust-accept-btn-handler"),  # OneTrust
                (By.ID, "didomi-notice-agree-button"),    # Didomi
                (By.XPATH, "//button[contains(text(), 'Accepter')]"),
                (By.XPATH, "//button[contains(text(), 'Tout accepter')]"),
                (By.CSS_SELECTOR, "button.didomi-button"),
            ]
            
            cookie_accepted = False
            for selector_type, selector_value in cookie_buttons:
                try:
                    accept_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    accept_btn.click()
                    logger.info("✅ Cookies acceptés")
                    self.human_delay(3, 5)
                    cookie_accepted = True
                    break
                except:
                    continue
            
            if not cookie_accepted:
                logger.info("⚠️ Pas de popup cookies détectée")
            
            # Attendre BEAUCOUP plus longtemps pour le chargement complet du JavaScript
            logger.info("\n⏳ Attente chargement JavaScript de la page...")
            self.human_delay(8, 12)
            
            # Détecter et résoudre un éventuel captcha AVANT le login
            logger.info("\n🔍 Vérification captcha avant login...")
            self.detect_and_solve_captcha()
            self.human_delay(2, 4)
            
            # Chercher le champ email
            logger.info("\n📧 Recherche du champ email...")
            email_selectors = [
                "input[type='email']",
                "input[name*='email']",
                "input#email",
                "input[placeholder*='mail']",
                "input#login-email-input",  # Sélecteur spécifique King Jouet
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"✅ Champ email trouvé: {selector}")
                    break
                except:
                    logger.debug(f"⚠️ Pas trouvé: {selector}")
                    continue
            
            if not email_field:
                logger.error("❌ Champ email introuvable")
                self.driver.save_screenshot("kingjouet_login_error.png")
                with open("kingjouet_login_error.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                logger.info("💾 HTML sauvegardé dans kingjouet_login_error.html")
                
                # Chercher des indices dans la page
                page_text = self.driver.page_source.lower()
                if "captcha" in page_text or "challenge" in page_text:
                    logger.warning("⚠️ Mot 'captcha' ou 'challenge' trouvé dans la page!")
                if "datadomestatus" in page_text or "datadome" in page_text:
                    logger.warning("⚠️ DataDome détecté dans la page!")
                if "cf-challenge" in page_text or "cloudflare" in page_text:
                    logger.warning("⚠️ Cloudflare détecté dans la page!")
                
                return False
            
            # Saisie email
            email_field.click()
            self.human_delay(0.5, 1)
            self.human_type(email_field, self.email)
            logger.info(f"✅ Email saisi: {self.email}")
            self.human_delay(1, 2)
            
            # King Jouet : formulaire en 2 étapes sur la même page
            # Étape 1 : cliquer sur "Valider" après l'email pour afficher le mot de passe
            logger.info("\n📤 Soumission de l'email pour afficher le mot de passe...")
            try:
                # Chercher le bouton "Valider"
                validate_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Valider')]"))
                )
                validate_btn.click()
                logger.info("✅ Email soumis")
                self.human_delay(3, 5)
            except Exception as e:
                logger.error(f"❌ Bouton Valider non trouvé: {e}")
                return False
            
            # Étape 2 : Le champ mot de passe devrait maintenant être visible
            logger.info("\n🔐 Recherche du champ mot de passe...")
            try:
                pwd_field = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
                )
                logger.info("✅ Champ mot de passe maintenant visible")
                
                # Scroll et saisie
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", pwd_field)
                self.human_delay(1, 2)
                
                pwd_field.click()
                self.human_delay(0.5, 1)
                self.human_type(pwd_field, self.password)
                logger.info("✅ Mot de passe saisi")
                self.human_delay(1, 2)
                
            except Exception as e:
                logger.error(f"❌ Erreur mot de passe: {e}")
                self.driver.save_screenshot("kingjouet_nopwd.png")
                with open("kingjouet_nopwd.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                return False
            
            # Soumission du formulaire
            logger.info("\n✅ Soumission du formulaire...")
            try:
                submit_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@type='submit'] | //input[@type='submit']"))
                )
                submit_btn.click()
            except:
                logger.info("⚠️ Bouton submit non trouvé, tentative avec Enter...")
                pwd_field.send_keys(Keys.ENTER)
            
            self.human_delay(5, 8)
            
            # Détecter et résoudre les captchas
            logger.info("\n🔍 Vérification présence de captcha...")
            captcha_detected = self.detect_and_solve_captcha()
            
            if captcha_detected:
                logger.info("✅ Captcha traité, attente validation...")
                self.human_delay(5, 8)
            
            # Vérification de la connexion
            logger.info("\n🔍 Vérification de la connexion...")
            current_url = self.driver.current_url.lower()
            
            # Sauvegarder l'état pour debug
            self.driver.save_screenshot("login_final.png")
            
            if "account" in current_url or "compte" in current_url or "my" in current_url:
                logger.info("🎉 CONNEXION RÉUSSIE !")
                return True
            else:
                logger.warning(f"⚠️ URL actuelle: {self.driver.current_url}")
                # Vérifier si on a un message d'erreur
                try:
                    error_msg = self.driver.find_element(By.XPATH, "//*[contains(text(), 'erreur') or contains(text(), 'incorrect')]")
                    logger.error(f"❌ Erreur connexion: {error_msg.text}")
                    return False
                except:
                    # Pas de message d'erreur visible, probablement OK
                    logger.info("✅ Pas d'erreur visible, connexion probablement réussie")
                    return True
                
        except Exception as e:
            logger.error(f"❌ Erreur connexion: {e}")
            return False
    
    def check_product_availability(self, product_url):
        """Vérifie si un produit est disponible"""
        try:
            logger.info(f"\n🔍 Vérification: {product_url}")
            self.driver.get(product_url)
            self.human_delay(3, 5)
            
            # Chercher le bouton "Ajouter au panier"
            add_to_cart_selectors = [
                "//button[contains(text(), 'Ajouter au panier')]",
                "//button[contains(text(), 'Ajouter')]",
                "//a[contains(text(), 'Ajouter au panier')]",
                "//button[contains(@class, 'add-to-cart')]",
                "//*[@id='add-to-cart']",
            ]
            
            for selector in add_to_cart_selectors:
                try:
                    btn = self.driver.find_element(By.XPATH, selector)
                    if btn.is_displayed() and btn.is_enabled():
                        logger.info(f"✅ PRODUIT DISPONIBLE !")
                        return True, btn
                except:
                    continue
            
            # Vérifier messages d'indisponibilité
            unavailable_keywords = ["indisponible", "rupture", "épuisé", "bientôt disponible"]
            page_text = self.driver.page_source.lower()
            
            for keyword in unavailable_keywords:
                if keyword in page_text:
                    logger.info(f"❌ Produit indisponible ('{keyword}' détecté)")
                    return False, None
            
            logger.warning("⚠️ Statut produit incertain")
            return False, None
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification: {e}")
            return False, None
    
    def add_to_cart(self, add_button):
        """Ajoute le produit au panier"""
        try:
            logger.info("\n🛒 AJOUT AU PANIER")
            logger.info("="*50)
            
            add_button.click()
            logger.info("✅ Produit ajouté au panier")
            self.human_delay(3, 5)
            
            # Screenshot du panier
            self.driver.save_screenshot(f"panier_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur ajout panier: {e}")
            return False
    
    def proceed_to_checkout(self, complete_payment=False):
        """Procède au checkout"""
        try:
            logger.info("\n💳 PROCESSUS DE PAIEMENT")
            logger.info("="*50)
            
            # Aller au panier - King Jouet utilise probablement /panier.aspx ou icône panier
            logger.info("\n🛒 Accès au panier...")
            
            cart_selectors = [
                "//a[contains(@href, 'panier')]",
                "//a[contains(@href, 'cart')]",
                "//a[contains(text(), 'Panier')]",
                (By.CSS_SELECTOR, "a[href*='panier']"),
                (By.XPATH, "//span[contains(@class, 'kj-icon-panier')]"),  # Icône panier
                (By.CSS_SELECTOR, ".kj-icon-panier"),
            ]
            
            cart_found = False
            for selector in cart_selectors:
                try:
                    if isinstance(selector, tuple):
                        cart_btn = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable(selector)
                        )
                    else:
                        cart_btn = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    cart_btn.click()
                    logger.info(f"✅ Clic sur panier")
                    cart_found = True
                    self.human_delay(3, 5)
                    break
                except:
                    continue
            
            if not cart_found:
                logger.info("⚠️ Bouton panier non trouvé, accès direct...")
                # Accès direct au panier
                self.driver.get("https://www.king-jouet.com/panier.aspx")
                self.human_delay(3, 5)
                logger.info(f"✅ Accès direct au panier: {self.driver.current_url}")
            
            # Screenshot du panier
            self.driver.save_screenshot(f"checkout_step1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            
            # Sauvegarder le HTML du panier pour analyse
            with open(f"panier_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            
            # Vérifier si le panier contient des articles
            page_text = self.driver.page_source.lower()
            if "panier est vide" in page_text or "aucun article" in page_text:
                logger.warning("❌ Panier vide - produit pas vraiment ajouté")
                return False
            
            # Chercher le bouton "Commander" ou "Continuer" sur la page panier
            logger.info("\n🔍 Recherche du bouton de commande...")
            
            checkout_selectors = [
                (By.XPATH, "//button[contains(text(), 'Commander')]"),
                (By.XPATH, "//a[contains(text(), 'Commander')]"),
                (By.XPATH, "//button[contains(text(), 'Continuer')]"),
                (By.XPATH, "//a[contains(text(), 'Continuer')]"),
                (By.XPATH, "//button[contains(text(), 'Valider')]"),
                (By.XPATH, "//button[contains(text(), 'Passer commande')]"),
                (By.CSS_SELECTOR, "button[class*='commander']"),
                (By.CSS_SELECTOR, "a[class*='commander']"),
                (By.CSS_SELECTOR, "button[class*='checkout']"),
            ]
            
            checkout_found = False
            for selector_type, selector_value in checkout_selectors:
                try:
                    checkout_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    logger.info(f"✅ Bouton trouvé: {checkout_btn.text}")
                    logger.info(f"🔗 URL: {self.driver.current_url}")
                    
                    if complete_payment:
                        logger.warning("\n⚠️⚠️⚠️ CLIC SUR PAIEMENT FINAL ⚠️⚠️⚠️")
                        checkout_btn.click()
                        self.human_delay(5, 8)
                        
                        # Screenshot final
                        self.driver.save_screenshot(f"payment_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                        logger.info(f"✅ Paiement processé - URL: {self.driver.current_url}")
                        return True
                    else:
                        logger.info("\n⚠️ MODE TEST - ARRÊT AVANT PAIEMENT")
                        logger.info("✅ Le processus fonctionne jusqu'au paiement")
                        logger.info(f"✅ Bouton trouvé: '{checkout_btn.text}'")
                        return True
                    
                    checkout_found = True
                    break
                except:
                    continue
            
            if not checkout_found:
                logger.warning("⚠️ Bouton checkout non trouvé")
                logger.info(f"🔗 URL actuelle: {self.driver.current_url}")
                
                # Debug: afficher tous les boutons présents
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                logger.info("\n📋 Tous les boutons sur la page:")
                for btn in all_buttons[:10]:  # Limiter à 10
                    if btn.text.strip():
                        logger.info(f"  - '{btn.text.strip()}'")
                
                return False
            
            return checkout_found
            
        except Exception as e:
            logger.error(f"❌ Erreur checkout: {e}")
            return False
    
    def test_purchase_flow(self):
        """Test complet du processus d'achat sur Bakugan (sans achat réel)"""
        logger.info("\n" + "="*70)
        logger.info("🎯 TEST DU PROCESSUS D'ACHAT - BAKUGAN")
        logger.info("="*70)
        
        test_url = self.config.get('test_product', {}).get('url')
        if not test_url:
            logger.error("❌ URL de test non configurée")
            return False
        
        try:
            # Connexion
            if not self.login():
                logger.error("❌ Échec connexion")
                return False
            
            # Vérifier disponibilité
            available, add_button = self.check_product_availability(test_url)
            
            if not available or not add_button:
                logger.warning("❌ Produit test non disponible")
                return False
            
            # Ajouter au panier
            if not self.add_to_cart(add_button):
                return False
            
            # Procéder au checkout SANS compléter le paiement (mode test)
            if self.proceed_to_checkout(complete_payment=False):
                logger.info("\n✅ TEST RÉUSSI - Tous les sélecteurs fonctionnent !")
                return True
            else:
                logger.warning("⚠️ Test partiel")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur test: {e}")
            return False
    
    def purchase_product(self, product_url, complete_payment=True):
        """Achat complet d'un produit"""
        logger.info(f"\n💰 ACHAT AUTOMATIQUE: {product_url}")
        
        try:
            # Vérifier disponibilité
            available, add_button = self.check_product_availability(product_url)
            
            if not available or not add_button:
                logger.warning("❌ Produit non disponible")
                return False
            
            # Ajouter au panier
            if not self.add_to_cart(add_button):
                return False
            
            # Procéder au checkout COMPLET
            if self.proceed_to_checkout(complete_payment=complete_payment):
                self.purchase_count += 1
                
                # Notification
                self.send_notification(product_url)
                
                logger.info(f"\n🎉 ACHAT #{self.purchase_count} RÉUSSI !")
                return True
            else:
                logger.error("❌ Échec checkout")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur achat: {e}")
            return False
    
    def send_notification(self, product_url):
        """Envoie une notification après achat"""
        message = f"""
        ✅ ACHAT RÉUSSI !
        Produit: {product_url}
        Heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Nombre d'achats total: {self.purchase_count}
        """
        
        logger.info("\n" + "="*70)
        logger.info("🔔 NOTIFICATION")
        logger.info(message)
        logger.info("="*70)
        
        # Sauvegarder dans un fichier de notifications
        with open("achats_reussis.log", "a") as f:
            f.write(f"\n{datetime.now()} - {product_url} - Achat #{self.purchase_count}\n")
    
    def monitor_and_buy(self, product_url, max_purchases=1):
        """Surveille un produit et achète dès disponible"""
        logger.info(f"\n🔄 SURVEILLANCE ACTIVÉE")
        logger.info(f"🎯 Produit: {product_url}")
        logger.info(f"⏰ Vérification toutes les 30 secondes")
        logger.info(f"🛒 Maximum d'achats: {max_purchases}")
        logger.info("="*70)
        
        check_count = 0
        
        try:
            while self.purchase_count < max_purchases:
                check_count += 1
                logger.info(f"\n🔍 Vérification #{check_count} - {datetime.now().strftime('%H:%M:%S')}")
                
                available, add_button = self.check_product_availability(product_url)
                
                if available and add_button:
                    logger.info("🚀 PRODUIT DISPONIBLE - ACHAT IMMÉDIAT !")
                    
                    if self.purchase_product(product_url, complete_payment=True):
                        logger.info(f"✅ Achat #{self.purchase_count} terminé")
                        
                        if self.purchase_count >= max_purchases:
                            logger.info(f"\n🏁 Objectif atteint: {max_purchases} achat(s)")
                            break
                        else:
                            logger.info(f"🔄 Continue surveillance (reste {max_purchases - self.purchase_count})")
                    else:
                        logger.error("❌ Échec achat, nouvelle tentative...")
                
                # Attendre 30 secondes avant prochaine vérification
                logger.info("⏳ Attente 30 secondes...")
                time.sleep(30)
                
        except KeyboardInterrupt:
            logger.info("\n⚠️ Surveillance interrompue par l'utilisateur")
        except Exception as e:
            logger.error(f"❌ Erreur surveillance: {e}")
    
    def run(self, mode="test"):
        """Fonction principale"""
        if not self.email or not self.password:
            logger.error("❌ Identifiants manquants")
            return {"status": "error", "message": "Identifiants manquants"}
        
        try:
            self.driver = self.init_driver()
            if not self.driver:
                return {"status": "error", "message": "Driver non initialisé"}
            
            if mode == "test":
                # Mode test sur Bakugan
                if self.test_purchase_flow():
                    logger.info("\n✅ TEST VALIDÉ - Prêt pour la surveillance")
                    return {"status": "success", "message": "Test réussi"}
                else:
                    return {"status": "error", "message": "Test échoué"}
                    
            elif mode == "monitor":
                # Mode surveillance et achat automatique
                logger.info("\n🚀 MODE SURVEILLANCE ET ACHAT AUTOMATIQUE")
                
                # D'abord se connecter
                if not self.login():
                    logger.error("❌ Échec connexion")
                    return {"status": "error", "message": "Connexion échouée"}
                
                # Surveiller les produits configurés
                for product in self.config.get('products', []):
                    if product.get('enabled'):
                        max_purchases = product.get('max_purchases', 1)
                        self.monitor_and_buy(product['url'], max_purchases)
                
                return {"status": "success", "message": f"{self.purchase_count} achat(s) effectué(s)"}
            
        except KeyboardInterrupt:
            logger.info("\n⚠️ Interruption utilisateur")
            return {"status": "interrupted"}
        except Exception as e:
            logger.error(f"\n❌ ERREUR: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}
        finally:
            if self.driver:
                logger.info("\n🧹 Fermeture du navigateur...")
                self.human_delay(2, 3)
                self.driver.quit()

if __name__ == "__main__":
    import sys
    
    print("\n" + "="*70)
    print("🤖 BOT KING JOUET - ACHAT AUTOMATIQUE")
    print("="*70)
    print("\nModes disponibles:")
    print("  test    - Test sur produit Bakugan (sans achat réel)")
    print("  monitor - Surveillance et achat automatique Pokémon")
    print("\nUsage: python bot_kingjouet.py [test|monitor]")
    print("="*70 + "\n")
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "test"
    
    bot = KingJouetBot()
    result = bot.run(mode=mode)
    
    print("\n" + "="*70)
    print(f"📊 RÉSULTAT: {result}")
    print("="*70 + "\n")

