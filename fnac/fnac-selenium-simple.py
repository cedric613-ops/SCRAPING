#!/usr/bin/env python3
"""
Bot de connexion Fnac - Version Selenium Standard
Pour tester sans undetected-chromedriver
"""

import time
import random
import json
import os
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

class FnacLoginBotSimple:
    def __init__(self):
        self.driver = None
        self.email, self.password = self.load_credentials()
        
    def load_credentials(self):
        try:
            with open('credentials.json') as f:
                data = json.load(f)
                return data.get('email'), data.get('password')
        except Exception as e:
            print(f"Erreur lecture credentials: {e}")
            return None, None

    def human_delay(self, min_sec=1, max_sec=3):
        """Délai humain aléatoire"""
        delay = random.uniform(min_sec, max_sec)
        print(f"⏳ Pause de {delay:.1f}s...")
        time.sleep(delay)

    def human_type(self, element, text):
        """Simule la frappe humaine avec délais variables"""
        for char in text:
            element.send_keys(char)
            # Délais plus longs et plus variables
            time.sleep(random.uniform(0.1, 0.4))
    
    def random_mouse_movement(self):
        """Simule des mouvements de souris aléatoires"""
        try:
            # Effectue des mouvements aléatoires sur la page
            actions = ActionChains(self.driver)
            for _ in range(random.randint(1, 3)):
                x = random.randint(100, 800)
                y = random.randint(100, 400)
                actions.move_by_offset(x, y)
            actions.perform()
            time.sleep(random.uniform(0.3, 0.8))
        except:
            pass
    
    def human_scroll(self):
        """Simule un scroll humain"""
        try:
            scroll_amount = random.randint(100, 300)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.5, 1.2))
        except:
            pass

    def init_driver(self):
        print("🔧 Initialisation du driver Selenium...")
        
        options = webdriver.ChromeOptions()
        
        # Mode headless désactivé pour éviter la détection DataDome
        # DataDome détecte facilement le mode headless
        # print("⚠️  Mode headless activé (sans interface graphique)")
        # options.add_argument("--headless=new")
        print("🌟 Mode avec interface graphique (meilleure anti-détection)")
        
        # User agent réaliste (Chrome sur Windows)
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        options.add_argument(f'user-agent={user_agent}')
        
        # Configuration de base pour stabilité et anti-détection
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--lang=fr-FR,fr")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Arguments supplémentaires pour ressembler à un vrai navigateur
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=IsolateOrigins,site-per-process")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-webgl")
        options.add_argument("--disable-popup-blocking")
        
        # Désactiver les infobars
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Préférences pour ressembler à un vrai navigateur
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.media_stream": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_settings.popups": 0,
        }
        options.add_experimental_option("prefs", prefs)
        
        try:
            print("📥 Téléchargement/vérification de ChromeDriver...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            print("✅ Driver Chrome initialisé (mode headless)")
            
            # Appliquer selenium-stealth pour masquer l'automatisation
            print("🔒 Application de selenium-stealth...")
            stealth(driver,
                languages=["fr-FR", "fr"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            print("✅ Stealth activé")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        return driver

    def handle_cookies(self):
        try:
            accept_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            accept_btn.click()
            print("✅ Cookies acceptés")
            self.human_delay(2, 3)
        except Exception as e:
            print(f"⚠ Pas de popup cookies")

    def login_sequence(self):
        try:
            print("🌐 Accès à Fnac.com...")
            self.driver.get("https://www.fnac.com/")
            
            # Délai plus long pour charger complètement la page
            print("⏳ Chargement de la page...")
            self.human_delay(5, 8)
            
            # Simuler un comportement humain : scroll léger
            self.human_scroll()
            self.human_delay(2, 4)
            
            self.handle_cookies()
            
            # Pause supplémentaire après les cookies
            self.human_delay(3, 5)
            
            # Faire une capture d'écran et sauvegarder le HTML pour déboguer
            self.driver.save_screenshot("fnac_home.png")
            with open("fnac_home.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print("📸 Capture d'écran et HTML sauvegardés")
            print(f"📝 Titre de la page: {self.driver.title}")
            
            # Simuler une lecture de la page
            print("👀 Simulation lecture de la page...")
            self.human_delay(4, 7)
            self.human_scroll()
            self.human_delay(2, 3)
            
            # Cliquer sur "Me connecter" - essayer plusieurs sélecteurs
            print("🔍 Recherche du bouton 'Me connecter'...")
            login_found = False
            
            selectors = [
                (By.XPATH, "//span[contains(text(), 'Me connecter')]"),
                (By.XPATH, "//a[contains(text(), 'Me connecter')]"),
                (By.XPATH, "//button[contains(text(), 'Me connecter')]"),
                (By.CSS_SELECTOR, "a[href*='identification']"),
                (By.CSS_SELECTOR, "[data-testid*='login']"),
                (By.XPATH, "//a[contains(@class, 'UserAccount')]"),
            ]
            
            for selector_type, selector_value in selectors:
                try:
                    # Attendre plus longtemps
                    login_btn = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    
                    # Simuler un mouvement de souris vers le bouton
                    print("🖱️  Déplacement vers le bouton...")
                    self.human_delay(1, 2)
                    
                    # Scroll vers l'élément
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", login_btn)
                    self.human_delay(0.8, 1.5)
                    
                    # Clic avec ActionChains pour simuler un vrai clic
                    ActionChains(self.driver).move_to_element(login_btn).pause(
                        random.uniform(0.5, 1.2)).click().perform()
                    
                    print(f"➡️ Clic sur 'Me connecter' avec sélecteur: {selector_value[:50]}")
                    login_found = True
                    
                    # Délai plus long après le clic
                    self.human_delay(5, 8)
                    break
                except:
                    continue
            
            if not login_found:
                print("❌ Bouton 'Me connecter' introuvable avec tous les sélecteurs")
                print(f"URL actuelle: {self.driver.current_url}")
                return False
            
            # Saisie de l'email
            print("📧 Recherche du champ email...")
            self.human_delay(2, 4)
            
            try:
                email_field = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
                )
                
                # Scroll vers le champ
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", email_field)
                self.human_delay(1, 2)
                
                # Clic avec délai
                print("🖱️  Clic sur le champ email...")
                email_field.click()
                self.human_delay(1, 2)
                
                # Frappe lente
                print("⌨️  Saisie de l'email...")
                self.human_type(email_field, self.email)
                print(f"✅ Email saisi: {self.email}")
                self.human_delay(2, 3)
            except:
                print("❌ Champ email introuvable")
                return False
            
            # Soumission email
            print("📤 Recherche du bouton de soumission...")
            self.human_delay(2, 3)
            
            try:
                submit_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
                )
                
                # Simuler réflexion avant de cliquer
                print("🤔 Vérification avant soumission...")
                self.human_delay(1.5, 3)
                
                # Scroll vers le bouton
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
                self.human_delay(0.8, 1.5)
                
                # Clic avec ActionChains
                ActionChains(self.driver).move_to_element(submit_btn).pause(
                    random.uniform(0.7, 1.5)).click().perform()
                print("✅ Email soumis")
                
                # Délai plus long pour le traitement
                self.human_delay(8, 12)
            except:
                print("⚠️ Bouton non trouvé, tentative avec Enter...")
                self.human_delay(1, 2)
                email_field.send_keys(Keys.ENTER)
                print("✅ Email soumis (Enter)")
                self.human_delay(8, 12)
            
            # Attendre le captcha ou le champ mot de passe
            print("⏳ Attente du champ mot de passe ou captcha...")
            print("⚠️ Si un captcha apparaît, résolvez-le manuellement")
            
            # Attendre très longtemps pour laisser le temps de résoudre le captcha
            # et simuler un humain qui réfléchit
            print("🕐 Pause prolongée (simulation humaine)...")
            self.human_delay(15, 25)
            
            # Saisie du mot de passe
            print("🔐 Recherche du champ mot de passe...")
            try:
                password_field = WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
                )
                password_field.click()
                self.human_delay(0.5, 1)
                self.human_type(password_field, self.password)
                print("✅ Mot de passe saisi")
                self.human_delay(1, 2)
            except:
                print("❌ Champ mot de passe introuvable")
                return False
            
            # Soumission finale
            print("📤 Soumission finale...")
            try:
                login_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
                )
                login_btn.click()
                print("✅ Connexion soumise")
                self.human_delay(5, 8)
            except:
                password_field.send_keys(Keys.ENTER)
                print("✅ Connexion soumise (Enter)")
                self.human_delay(5, 8)
            
            # Vérification
            print("🔍 Vérification de la connexion...")
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/account']"))
                )
                print("🎉 Connexion réussie !")
                return True
            except:
                print("⚠️ Impossible de vérifier la connexion")
                print(f"URL actuelle: {self.driver.current_url}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur: {str(e)}")
            return False

    def run(self):
        if not self.email or not self.password:
            return {"status": "error", "message": "Identifiants manquants"}
            
        try:
            print("🔄 Initialisation...")
            self.driver = self.init_driver()
            
            print("🔑 Début de la connexion...")
            if not self.login_sequence():
                raise Exception("Échec connexion")
            
            print("⏳ Connexion active - Gardez la fenêtre ouverte...")
            print("⏳ Appuyez sur Ctrl+C dans le terminal pour quitter")
            
            # Garder la fenêtre ouverte
            while True:
                time.sleep(1)
            
            return {"status": "success", "message": "Connexion réussie"}

        except KeyboardInterrupt:
            print("\n⚠️ Interruption utilisateur")
            return {"status": "interrupted", "message": "Arrêt manuel"}
        except Exception as e:
            print(f"\n❌ ERREUR: {str(e)}")
            return {"status": "error", "message": str(e)}
            
        finally:
            if self.driver:
                try:
                    print("\n🧹 Fermeture du navigateur...")
                    input("Appuyez sur Entrée pour fermer le navigateur...")
                    self.driver.quit()
                    print("✅ Navigateur fermé")
                except Exception as e:
                    print(f"⚠️ Erreur fermeture: {str(e)}")

if __name__ == "__main__":
    print("\n=== FNAC LOGIN BOT - Version Selenium Simple ===")
    print("Cette version utilise Selenium standard")
    print("Vous devrez résoudre le captcha MANUELLEMENT si demandé\n")
    bot = FnacLoginBotSimple()
    result = bot.run()
    print("\n📊 RESULTAT:", result)

