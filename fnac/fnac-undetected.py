#!/usr/bin/env python3
"""
Bot Fnac avec undetected-chromedriver
Passe DataDome automatiquement !
Basé sur : https://github.com/ultrafunkamsterdam/undetected-chromedriver
"""

import time
import random
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class FnacBotUndetected:
    def __init__(self):
        self.driver = None
        self.email, self.password = self.load_credentials()
        
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
        """Frappe caractère par caractère"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.1, 0.4))
    
    def init_driver(self):
        print("🔧 Initialisation undetected-chromedriver...")
        print("📚 Référence: https://github.com/ultrafunkamsterdam/undetected-chromedriver")
        
        options = uc.ChromeOptions()
        
        # Mode NON-headless maintenant que Xvfb est installé
        # Meilleure anti-détection sans headless
        # options.headless = True
        # options.add_argument("--headless")
        print("🌟 Mode graphique (avec Xvfb) - Meilleure anti-détection !")
        
        # Options minimales pour stabilité
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        try:
            print("Tentative 1: Configuration standard...")
            # undetected-chromedriver gère tout automatiquement !
            driver = uc.Chrome(options=options, use_subprocess=False)
            print("✅ Driver initialisé (config standard)")
            return driver
            
        except Exception as e:
            print(f"⚠️ Erreur config standard: {str(e)[:100]}")
            
            try:
                print("Tentative 2: Configuration minimale...")
                # Configuration ultra-minimale
                driver = uc.Chrome(headless=True, use_subprocess=False)
                print("✅ Driver initialisé (config minimale)")
                return driver
            except Exception as e2:
                print(f"❌ Erreur config minimale: {str(e2)[:100]}")
                
                try:
                    print("Tentative 3: Sans headless...")
                    options2 = uc.ChromeOptions()
                    options2.add_argument("--no-sandbox")
                    options2.add_argument("--disable-dev-shm-usage")
                    driver = uc.Chrome(options=options2, use_subprocess=False)
                    print("✅ Driver initialisé (sans headless)")
                    return driver
                except Exception as e3:
                    print(f"❌ Toutes les tentatives ont échoué: {str(e3)[:100]}")
                    return None
    
    def handle_cookies(self):
        """Accepter les cookies"""
        try:
            accept_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            accept_btn.click()
            print("✅ Cookies acceptés")
            self.human_delay(2, 3)
        except:
            print("⚠️ Pas de popup cookies")
    
    def login_to_fnac(self):
        """Processus complet de connexion"""
        try:
            # Accès au site
            print("\n🌐 Accès à fnac.com...")
            self.driver.get("https://www.fnac.com/")
            self.human_delay(5, 8)
            
            # Sauvegarder pour vérification
            with open("fnac_undetected.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            
            print(f"📝 Titre: {self.driver.title}")
            print(f"🔗 URL: {self.driver.current_url}")
            
            # Vérifier si DataDome est présent
            if "datadome" in self.driver.page_source.lower() or "captcha-delivery.com" in self.driver.page_source.lower():
                print("⚠️ Captcha DataDome détecté")
                print("⏳ Attente pour laisser undetected-chromedriver le contourner...")
                
                # Attendre BEAUCOUP plus longtemps (DataDome peut prendre du temps)
                for i in range(6):  # 6 tentatives
                    self.human_delay(5, 10)
                    print(f"   Tentative {i+1}/6...")
                    
                    # Vérifier si DataDome est passé
                    current_html = self.driver.page_source.lower()
                    if "datadome" not in current_html and "captcha-delivery.com" not in current_html:
                        print("✅ DataDome contourné automatiquement !")
                        break
                    
                    # Essayer de cliquer sur la checkbox DataDome si présente
                    try:
                        checkbox = self.driver.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                        if checkbox.is_displayed():
                            print("📋 Checkbox DataDome trouvée, tentative de clic...")
                            checkbox.click()
                            self.human_delay(3, 5)
                    except:
                        pass
                
                # Vérification finale
                if "datadome" in self.driver.page_source.lower():
                    print("❌ DataDome toujours présent après 60 secondes")
                    print("💡 DataDome nécessite peut-être:")
                    print("   - Une IP résidentielle (pas datacenter/VPS)")
                    print("   - Un proxy résidentiel rotatif")
                    print("   - CapSolver pour résolution automatique")
                    return False
                else:
                    print("✅ DataDome contourné !")
            
            # Gérer les cookies
            self.handle_cookies()
            self.human_delay(3, 5)
            
            # Chercher le bouton de connexion
            print("\n🔍 Recherche du bouton 'Me connecter'...")
            
            selectors = [
                (By.XPATH, "//span[contains(text(), 'Me connecter')]"),
                (By.XPATH, "//a[contains(text(), 'Me connecter')]"),
                (By.CSS_SELECTOR, "a[href*='identification']"),
                (By.XPATH, "//a[contains(@class, 'UserAccount')]"),
            ]
            
            login_found = False
            for selector_type, selector_value in selectors:
                try:
                    login_btn = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    
                    # Scroll vers l'élément
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", login_btn)
                    self.human_delay(1, 2)
                    
                    login_btn.click()
                    print(f"✅ Clic sur 'Me connecter'")
                    login_found = True
                    self.human_delay(5, 8)
                    break
                except:
                    continue
            
            if not login_found:
                print("❌ Bouton 'Me connecter' introuvable")
                print("💡 Le site est accessible mais la structure a peut-être changé")
                return False
            
            # Saisie de l'email
            print("\n📧 Saisie de l'email...")
            try:
                email_field = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
                )
                email_field.click()
                self.human_delay(1, 2)
                self.human_type(email_field, self.email)
                print(f"✅ Email saisi: {self.email}")
                self.human_delay(2, 3)
            except:
                print("❌ Champ email introuvable")
                return False
            
            # Soumission
            print("\n📤 Soumission de l'email...")
            try:
                submit_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
                )
                submit_btn.click()
                print("✅ Email soumis")
            except:
                email_field.send_keys(Keys.ENTER)
                print("✅ Email soumis (Enter)")
            
            self.human_delay(8, 12)
            
            # Attendre le champ mot de passe
            print("\n⏳ Attente du champ mot de passe...")
            self.human_delay(5, 10)
            
            try:
                password_field = WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
                )
                password_field.click()
                self.human_delay(1, 2)
                self.human_type(password_field, self.password)
                print("✅ Mot de passe saisi")
                self.human_delay(2, 3)
            except:
                print("❌ Champ mot de passe introuvable")
                # Vérifier si déjà connecté
                if "account" in self.driver.current_url.lower() or "mon compte" in self.driver.page_source.lower():
                    print("🎉 Connexion réussie (redirection automatique)")
                    return True
                return False
            
            # Soumission finale
            print("\n🔐 Connexion finale...")
            try:
                login_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
                )
                login_btn.click()
            except:
                password_field.send_keys(Keys.ENTER)
            
            print("✅ Mot de passe soumis")
            self.human_delay(5, 8)
            
            # Vérification
            print("\n🔍 Vérification de la connexion...")
            if "account" in self.driver.current_url.lower() or "mon compte" in self.driver.page_source.lower():
                print("🎉 CONNEXION RÉUSSIE !")
                return True
            else:
                print(f"⚠️ URL actuelle: {self.driver.current_url}")
                print("⚠️ Connexion incertaine")
                return False
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def run(self):
        if not self.email or not self.password:
            return {"status": "error", "message": "Identifiants manquants"}
        
        try:
            self.driver = self.init_driver()
            if not self.driver:
                return {"status": "error", "message": "Driver non initialisé"}
            
            print("\n" + "="*60)
            print("🚀 BOT FNAC avec UNDETECTED-CHROMEDRIVER")
            print("="*60)
            
            if self.login_to_fnac():
                print("\n✅ Processus de connexion terminé avec succès !")
                
                # Garder la session active
                print("\n⏳ Session active - Fermeture dans 10 secondes...")
                self.human_delay(10, 10)
                
                return {"status": "success", "message": "Connexion réussie"}
            else:
                return {"status": "partial", "message": "Connexion partielle ou échec"}
            
        except KeyboardInterrupt:
            print("\n⚠️ Interruption utilisateur")
            return {"status": "interrupted"}
        except Exception as e:
            print(f"\n❌ ERREUR: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}
        finally:
            if self.driver:
                print("\n🧹 Fermeture...")
                self.driver.quit()

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🤖 FNAC BOT - UNDETECTED CHROMEDRIVER")
    print("📚 https://github.com/ultrafunkamsterdam/undetected-chromedriver")
    print("🎯 Passe DataDome automatiquement")
    print("="*70 + "\n")
    
    bot = FnacBotUndetected()
    result = bot.run()
    
    print("\n" + "="*70)
    print(f"📊 RÉSULTAT FINAL: {result}")
    print("="*70 + "\n")

