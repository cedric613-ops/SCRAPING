import time
import random
import json
import requests
import os
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re

class FnacLoginBot:
    def __init__(self):
        self.driver = None
        self.email, self.password = self.load_credentials()
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
        
        # Charger la clé API SolveCaptcha
        load_dotenv()
        self.api_key = os.getenv("SOLVECAPTCHA_API_KEY")
        if not self.api_key:
            print("⚠ Avertissement: SOLVECAPTCHA_API_KEY non trouvé dans le fichier .env")
        
    def load_credentials(self):
        try:
            with open('credentials.json') as f:
                data = json.load(f)
                return data.get('email'), data.get('password')
        except Exception as e:
            print(f"Erreur lecture credentials: {e}")
            return None, None

    def human_delay(self, min_sec=1, max_sec=3):
        time.sleep(random.uniform(min_sec, max_sec))

    def human_type(self, element, text):
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.3))
            
    def extract_hcaptcha_sitekey(self):
        """Extrait dynamiquement le sitekey hCaptcha de la page"""
        try:
            # Recherche du sitekey dans les iframes hCaptcha
            hcaptcha_frame = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[contains(@src, 'hcaptcha.com')]"))
            )
            
            # Récupération de l'URL de l'iframe
            iframe_src = hcaptcha_frame.get_attribute("src")
            
            # Extraction du sitekey depuis l'URL
            sitekey_match = re.search(r'sitekey=([a-f0-9\-]+)', iframe_src)
            if sitekey_match:
                return sitekey_match.group(1)
            
            # Alternative: recherche dans les données de la page
            sitekey_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'h-captcha')]")
            for element in sitekey_elements:
                sitekey = element.get_attribute("data-sitekey")
                if sitekey:
                    return sitekey
                    
            # Dernière tentative: recherche dans le JavaScript
            page_source = self.driver.page_source
            sitekey_match = re.search(r'sitekey["\']?\s*[:=]\s*["\']([a-f0-9\-]+)["\']', page_source, re.IGNORECASE)
            if sitekey_match:
                return sitekey_match.group(1)
                
            return "0a541f40-63af-4354-ad11-995a5997082d"  # Fallback au sitekey par défaut
            
        except Exception as e:
            print(f"⚠ Impossible d'extraire le sitekey: {str(e)[:100]}")
            return "0a541f40-63af-4354-ad11-995a5997082d"  # Sitekey par défaut pour Fnac

    def solve_hcaptcha(self):
        """Résout le hCaptcha en utilisant SolveCaptcha"""
        if not self.api_key:
            print("❌ Clé API SolveCaptcha manquante - Résolution manuelle nécessaire")
            input("Appuyez sur Entrée après avoir résolu le CAPTCHA manuellement...")
            return False
            
        print("🔄 Début de la résolution automatique du hCaptcha...")
        
        try:
            # Récupérer le sitekey du hCaptcha dynamiquement
            sitekey = self.extract_hcaptcha_sitekey()
            pageurl = self.driver.current_url
            
            print(f"[INFO] Sitekey: {sitekey}")
            print(f"[INFO] Page URL: {pageurl}")
            
            # Envoyer la requête à SolveCaptcha
            print("[INFO] Envoi de la requête à SolveCaptcha...")
            payload = {
                "key": self.api_key,
                "method": "hcaptcha",
                "sitekey": sitekey,
                "pageurl": pageurl,
                "json": 1
            }
            
            r = requests.post("https://api.solvecaptcha.com/in.php", data=payload, timeout=30)
            res = r.json()
            
            if res.get("status") != 1:
                raise ValueError(f"Erreur SolveCaptcha: {res}")
                
            captcha_id = res["request"]
            print(f"[INFO] ID du captcha: {captcha_id}")

            # Polling pour récupérer le token (augmenté à 35 tentatives)
            print("[INFO] En attente de la résolution du captcha...")
            token = None
            for i in range(35):  # timeout 35*5 = 175s max
                time.sleep(5)
                try:
                    check = requests.get("https://api.solvecaptcha.com/res.php", params={
                        "key": self.api_key,
                        "action": "get",
                        "id": captcha_id,
                        "json": 1
                    }, timeout=30)
                    
                    check_res = check.json()
                    if check_res.get("status") == 1:
                        token = check_res["request"]
                        print(f"[INFO] Token reçu: {token[:20]}... (tronqué)")
                        break
                    elif check_res.get("request") == "CAPCHA_NOT_READY":
                        print(f"[INFO] Token pas encore prêt, tentative {i+1}/35...")
                    else:
                        print(f"[INFO] Statut: {check_res.get('request')}")
                except Exception as e:
                    print(f"[ERREUR] lors du polling: {str(e)}")
                    
            if not token:
                raise TimeoutError("Le token SolveCaptcha n'a pas été récupéré dans le délai imparti.")

            # Injection sécurisée du token avec échappement des caractères spéciaux
            print("[INFO] Injection du token dans la page...")
            
            # Échapper les caractères spéciaux du token pour JavaScript
            escaped_token = json.dumps(token)
            
            # Script simplifié et plus ciblé
            script = f"""
            let token = {escaped_token};
            
            console.log('Injection du token hCaptcha...');
            
            // Trouver le textarea h-captcha-response principal
            let hcaptchaResponse = document.querySelector('textarea[name="h-captcha-response"]');
            if (!hcaptchaResponse) {{
                hcaptchaResponse = document.createElement('textarea');
                hcaptchaResponse.name = 'h-captcha-response';
                hcaptchaResponse.style.display = 'none';
                document.body.appendChild(hcaptchaResponse);
            }}
            hcaptchaResponse.value = token;
            
            // Déclencher les événements nécessaires
            const changeEvent = new Event('change', {{ bubbles: true }});
            const inputEvent = new Event('input', {{ bubbles: true }});
            hcaptchaResponse.dispatchEvent(changeEvent);
            hcaptchaResponse.dispatchEvent(inputEvent);
            
            // Utiliser l'API hCaptcha si disponible
            if (typeof window.hcaptcha !== 'undefined') {{
                try {{
                    window.hcaptcha.setResponse(token);
                    console.log('hCaptcha API utilisée');
                }} catch (e) {{
                    console.log('Erreur hCaptcha API:', e);
                }}
            }}
            
            // Activer le bouton de validation
            const validateButton = document.querySelector('button[type="submit"]');
            if (validateButton && validateButton.disabled) {{
                validateButton.disabled = false;
                validateButton.style.opacity = '1';
                validateButton.style.pointerEvents = 'auto';
                console.log('Bouton activé');
            }}
            
            return 'Token injecté avec succès';
            """
            
            # Exécuter le script
            try:
                result = self.driver.execute_script(script)
                print(f"✅ {result}")
            except Exception as js_error:
                print(f"⚠ Erreur JavaScript: {str(js_error)[:100]}...")
                return False
            
            # Attendre brièvement puis cliquer sur le bouton de manière naturelle
            self.human_delay(2, 3)
            
            try:
                # Trouver et cliquer sur le bouton de validation
                validate_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
                )
                
                # Vérifier que le bouton n'est pas désactivé
                if validate_btn.get_attribute("disabled"):
                    self.driver.execute_script("arguments[0].disabled = false;", validate_btn)
                
                # Cliquer naturellement sur le bouton
                ActionChains(self.driver).move_to_element(validate_btn).pause(
                    random.uniform(0.5, 1.0)).click().perform()
                print("✅ Bouton de validation cliqué")
                
            except Exception as e:
                print(f"⚠ Impossible de cliquer sur le bouton: {str(e)[:70]}...")
                # Essayer avec JavaScript en dernier recours
                try:
                    self.driver.execute_script("document.querySelector('button[type=\"submit\"]').click();")
                    print("✅ Bouton cliqué via JavaScript")
                except:
                    print("❌ Impossible de cliquer sur le bouton")
                    return False
            
            # Attendre que la redirection se fasse
            print("⏳ Attente de la redirection après validation...")
            self.human_delay(5, 8)
            
            # Vérifier si nous avons été redirigés
            current_url = self.driver.current_url
            if "fnac.com" not in current_url and "error" in current_url:
                print(f"⚠ Redirection suspecte détectée: {current_url}")
                # Revenir à la page précédente et réessayer
                self.driver.back()
                self.human_delay(3, 5)
                return False
            
            return True
                
        except Exception as e:
            print(f"❌ Erreur lors de la résolution du hCaptcha: {str(e)}")
            print("⚠ Passage en mode résolution manuelle...")
            self.driver.save_screenshot("hcaptcha_error.png")
            print("📸 Capture d'écran sauvegardée: hcaptcha_error.png")
            input("Appuyez sur Entrée après avoir résolu le CAPTCHA manuellement...")
            return False

    def init_driver(self):
        options = uc.ChromeOptions()
        
        # Configuration optimisée
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--lang=fr-FR")
        
        # Options pour mieux voir l'interface
        options.add_argument("--start-maximized")
        
        # Désactivation des logs inutiles
        options.add_argument("--log-level=3")
        
        # Configuration de undetected-chromedriver (simplifié)
        try:
        driver = uc.Chrome(
            options=options,
                headless=False
            )
            print("✅ Driver initialisé avec options personnalisées")
        except Exception as e:
            print(f"⚠️ Erreur lors de l'initialisation avec Chrome: {e}")
            print("Tentative avec configuration minimale...")
            driver = uc.Chrome(headless=False)
            print("✅ Driver initialisé avec configuration minimale")
        
        # Note: undetected-chromedriver gère déjà le masquage des propriétés WebDriver
        # Pas besoin de commandes CDP supplémentaires
        
        return driver

    def handle_cookies(self):
        try:
            accept_btn = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            ActionChains(self.driver).move_to_element(accept_btn).pause(
                random.uniform(0.2, 1.5)).click().perform()
            print("✅ Cookies acceptés")
            self.human_delay(2, 4)
        except Exception as e:
            print(f"⚠ Gestion cookies non nécessaire: {str(e)[:70]}...")

    def handle_subscription_popup(self):
        try:
            no_thanks_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "batchsdk-ui-alert__buttons_negative"))
            )
            ActionChains(self.driver).move_to_element(no_thanks_btn).pause(
                random.uniform(0.5, 1.5)).click().perform()
            print("🚫 Popup d'abonnement refusée")
            self.human_delay(2, 3)
        except Exception as e:
            print(f"⚠ Pas de popup d'abonnement: {str(e)[:70]}...")

    def wait_for_hcaptcha_and_solve(self):
        """Attend l'apparition du hCaptcha et le résout"""
        try:
            print("⏳ Attente de l'apparition du hCaptcha...")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[contains(@src, 'hcaptcha.com')]"))
            )
            print("✅ hCaptcha détecté - Début de la résolution")
            self.human_delay(2, 3)
            return self.solve_hcaptcha()
        except TimeoutException:
            print("⚠ Aucun hCaptcha détecté après la soumission de l'email")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de l'attente du hCaptcha: {str(e)}")
            return False

    def check_password_field_alternative_selectors(self):
        """Vérifie les sélecteurs alternatifs pour le champ mot de passe"""
        selectors = [
            "input[type='password']",
            "input#password",
            "input[name*='password']",
            "input[name*='motdepasse']",
            "input[name*='pwd']",
            "input[data-test*='password']",
            "input[placeholder*='mot de passe']",
            "input[placeholder*='password']"
        ]
        
        for selector in selectors:
            try:
                field = self.driver.find_element(By.CSS_SELECTOR, selector)
                if field.is_displayed():
                    return field
            except:
                continue
        return None

    def login_sequence(self):
        try:
            print("🌐 Accès à Fnac.com...")
            self.driver.get("https://www.fnac.com/")
            self.human_delay(5, 8)
            
            self.handle_cookies()
            self.handle_subscription_popup()
            
            # Cliquer sur "Me connecter"
            try:
                login_btn = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Me connecter') or contains(text(), 'Connexion')]"))
                )
                ActionChains(self.driver).move_to_element(login_btn).pause(
                    random.uniform(0.5, 1.5)).click().perform()
                print("➡ Clic sur 'Me connecter'")
                self.human_delay(3, 5)
            except Exception as e:
                print(f"⚠ Impossible de trouver 'Me connecter': {str(e)[:70]}...")
                try:
                    login_btn = WebDriverWait(self.driver, 15).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='identification'], .login-button, [data-test*='login']"))
                    )
                    login_btn.click()
                    print("➡ Clic sur 'Me connecter' (sélecteur alternatif)")
                    self.human_delay(3, 5)
                except:
                    print("❌ Impossible de trouver le bouton de connexion")
                    return False
            
            # Saisie de l'email
            try:
                email_field = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[type='mail'], input#email, input[name*='email'], input[name*='mail']"))
                )
            except:
                print("❌ Impossible de trouver le champ email")
                try:
                    email_field = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//input[@id='adresse email']"))
                    )
                except:
                    print("❌ Impossible de trouver le champ email")
                    self.driver.save_screenshot("email_field_not_found.png")
                    return False
            
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", email_field)
            self.human_delay(1, 2)
            
            ActionChains(self.driver).move_to_element(email_field).pause(
                random.uniform(0.5, 1.0)).click().perform()
            self.human_delay(0.5, 1)
            
            email_field.send_keys(Keys.CONTROL + "a")
            email_field.send_keys(Keys.DELETE)
            self.human_delay(0.5, 1)
            
            self.human_type(email_field, self.email)
            self.human_delay(1, 2)
            
            # Soumission de l'email
            try:
                submit_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Connexion') or contains(., 'Continuer') or contains(., 'Suivant') or @type='submit']"))
                )
                ActionChains(self.driver).move_to_element(submit_btn).pause(
                    random.uniform(0.5, 1.5)).click().perform()
                print("✅ Email soumis")
                self.human_delay(3, 5)
            except Exception as e:
                print(f"⚠ Impossible de trouver le bouton de soumission: {str(e)[:70]}...")
                email_field.send_keys(Keys.ENTER)
                print("✅ Email soumis avec Entrée")
                self.human_delay(3, 5)
            
            # Résoudre le hCaptcha
            if not self.wait_for_hcaptcha_and_solve():
                print("❌ Échec de la résolution du hCaptcha")
                return False
            
            # Attendre le champ mot de passe avec plus de flexibilité
            print("⏳ Attente de l'apparition du champ mot de passe...")
            self.human_delay(8, 12)  # Attendre plus longtemps après le hCaptcha
            
            # Vérifier si nous sommes sur une page d'erreur
            current_url = self.driver.current_url
            if "error" in current_url or "404" in current_url:
                print(f"❌ Page d'erreur détectée: {current_url}")
                print("🔄 Tentative de retour à la page précédente...")
                self.driver.back()
                self.human_delay(3, 5)
                return False
            
            password_field = None
            
            # Essayer de trouver le champ mot de passe
            try:
                password_field = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
                )
            except TimeoutException:
                print("⚠ Champ mot de passe non trouvé, essai des sélecteurs alternatifs...")
                password_field = self.check_password_field_alternative_selectors()
            
            if not password_field:
                print("❌ Champ mot de passe non trouvé après validation du captcha")
                # Vérifier si le processus de connexion a déjà réussi
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/account'], .account-info, [data-test*='account']"))
                    )
                    print("🎉 Connexion réussie (redirection directe après hCaptcha)")
                    return True
                except:
                    self.driver.save_screenshot("password_field_missing.png")
                    return False
            
            # Saisie du mot de passe
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", password_field)
            self.human_delay(1, 2)
            
            ActionChains(self.driver).move_to_element(password_field).pause(
                random.uniform(0.5, 1.0)).click().perform()
            self.human_delay(0.5, 1)
            
            password_field.send_keys(Keys.CONTROL + "a")
            password_field.send_keys(Keys.DELETE)
            self.human_delay(0.5, 1)
            
            self.human_type(password_field, self.password)
            self.human_delay(1, 2)
            
            # Soumission finale
            try:
                login_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Se connecter') or contains(., 'Connexion') or @type='submit']"))
                )
                ActionChains(self.driver).move_to_element(login_btn).pause(
                    random.uniform(0.5, 1.5)).click().perform()
                print("✅ Mot de passe soumis")
                self.human_delay(5, 8)
            except Exception as e:
                print(f"⚠ Impossible de trouver le bouton de connexion final: {str(e)[:70]}...")
                password_field.send_keys(Keys.ENTER)
                print("✅ Mot de passe soumis avec Entrée")
                self.human_delay(5, 8)
            
            # Vérification de la connexion
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/account'], .account-info, [data-test*='account']"))
                )
                print("🎉 Connexion réussie !")
                return True
            except:
                print("❌ Échec de la connexion après soumission")
                self.driver.save_screenshot("login_failed.png")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la séquence de login: {str(e)[:100]}")
            self.driver.save_screenshot("login_sequence_error.png")
            return False

    def run(self):
        if not self.email or not self.password:
            return {"status": "error", "message": "Identifiants manquants"}
            
        try:
            print("🔄 Initialisation du navigateur...")
            self.driver = self.init_driver()
            print("✅ Navigateur initialisé avec succès")
            
            print("🔑 Début du processus de connexion...")
            if not self.login_sequence():
                raise Exception("Échec processus login")
            
            print("⏳ Attente avant fermeture...")
            self.human_delay(10, 15)
            
            return {"status": "success", "message": "Connexion réussie"}

        except Exception as e:
            print(f"\n❌ ERREUR FINALE: {str(e)}")
            return {"status": "error", "message": str(e)}
            
        finally:
            if self.driver:
                try:
                    self.human_delay(2, 5)
                    print("🧹 Fermeture du navigateur...")
                    self.driver.quit()
                    print("✅ Navigateur fermé")
                except Exception as e:
                    print(f"⚠ Erreur lors de la fermeture: {str(e)}")

if __name__ == "__main__":
    print("\n=== FNAC LOGIN BOT ULTIME ===")
    print("⚠ Assurez-vous que Google Chrome est installé sur votre système")
    bot = FnacLoginBot()
    result = bot.run()
    print("\n📊 RESULTAT:", result)
    input("Appuyez sur Entrée pour quitter...")
