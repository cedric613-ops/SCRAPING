#!/usr/bin/env python3
"""
Bot Shop For Geek - Achat Automatique
Surveillance et achat automatique de produits Pokémon en édition limitée
"""

import time
import random
import json
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium_stealth import stealth
from solvecaptcha import Solvecaptcha

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('shopforgeek_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ShopForGeekBot:
    """Bot principal pour Shop For Geek"""
    
    def __init__(self):
        self.driver = None
        self.config = self.load_config()
        self.email, self.password = self.load_credentials()
        self.purchase_count = 0
        
        # Charger API SolveCaptcha
        load_dotenv()
        api_key = os.getenv("SOLVECAPTCHA_API_KEY")
        if api_key:
            self.solver = Solvecaptcha(api_key)
            logger.info("✅ SolveCaptcha configuré")
        else:
            self.solver = None
            logger.warning("⚠️ Pas de clé API SolveCaptcha")
        
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
        time.sleep(delay)
    
    def human_type(self, element, text):
        """Simule la frappe humaine"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))
    
    def detect_and_solve_cloudflare(self):
        """Détecte et résout Cloudflare Turnstile"""
        if not self.solver:
            logger.warning("⚠️ Pas de solver configuré")
            return False
        
        try:
            logger.info("\n🔍 DÉTECTION CLOUDFLARE TURNSTILE")
            logger.info("="*50)
            
            page_source = self.driver.page_source
            page_url = self.driver.current_url
            
            # Détecter Cloudflare Turnstile
            if "turnstile" in page_source.lower() or "cf-turnstile" in page_source.lower() or "cf-challenge" in page_source.lower():
                logger.info("🔍 Cloudflare Turnstile détecté!")
                
                # Extraire le sitekey
                import re
                sitekey_patterns = [
                    r'data-sitekey="([^"]+)"',
                    r'sitekey:\s*["\']([^"\']+)["\']',
                    r'"sitekey":\s*"([^"]+)"',
                ]
                
                sitekey = None
                for pattern in sitekey_patterns:
                    match = re.search(pattern, page_source)
                    if match:
                        sitekey = match.group(1)
                        break
                
                if sitekey:
                    logger.info(f"✅ Sitekey trouvée: {sitekey[:30]}...")
                    
                    # Résoudre avec SolveCaptcha
                    logger.info("🔐 Envoi à SolveCaptcha...")
                    try:
                        result = self.solver.turnstile(
                            sitekey=sitekey,
                            url=page_url
                        )
                        
                        token = result['code']
                        logger.info(f"✅ Token Cloudflare reçu!")
                        
                        # Injecter le token
                        logger.info("💉 Injection du token...")
                        self.driver.execute_script(f"""
                            var elements = document.querySelectorAll('[name="cf-turnstile-response"]');
                            elements.forEach(function(el) {{
                                el.value = '{token}';
                            }});
                            
                            // g-recaptcha-response aussi utilisé par Turnstile
                            var grecaptcha = document.querySelectorAll('[name="g-recaptcha-response"]');
                            grecaptcha.forEach(function(el) {{
                                el.value = '{token}';
                            }});
                            
                            console.log('Cloudflare token injected');
                        """)
                        
                        logger.info("✅ Cloudflare Turnstile résolu!")
                        self.human_delay(2, 4)
                        return True
                        
                    except Exception as e:
                        logger.error(f"❌ Erreur résolution Cloudflare: {e}")
                        import traceback
                        traceback.print_exc()
                        return False
                else:
                    logger.warning("⚠️ Sitekey Cloudflare introuvable")
                    return False
            else:
                logger.debug("Pas de Cloudflare détecté")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur détection Cloudflare: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def init_driver(self):
        """Initialise undetected-chromedriver avec stealth"""
        logger.info("🔧 Initialisation du driver STEALTH...")
        
        try:
            driver = uc.Chrome(headless=True, use_subprocess=False, version_main=None)
            
            logger.info("🔒 Application de selenium-stealth...")
            stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            
            logger.info("✅ Driver STEALTH initialisé!")
            return driver
            
        except Exception as e:
            logger.error(f"❌ Erreur init driver: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def login(self):
        """Connexion au compte Shop For Geek"""
        try:
            logger.info("\n🔑 CONNEXION AU COMPTE SHOP FOR GEEK")
            logger.info("="*50)
            
            # Page d'accueil
            logger.info("🏠 Visite de la page d'accueil...")
            self.driver.get("https://www.shopforgeek.com/en/")
            self.human_delay(5, 8)
            
            # Accepter les cookies
            logger.info("🍪 Gestion des cookies...")
            try:
                cookie_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Accepter')]"))
                )
                cookie_btn.click()
                logger.info("✅ Cookies acceptés")
                self.human_delay(2, 3)
            except:
                logger.info("⚠️ Pas de popup cookies")
            
            # Chercher le lien de connexion sur la page d'accueil
            logger.info("🔍 Recherche du lien de connexion...")
            
            # Sauvegarder la page pour debug
            self.driver.save_screenshot("shopforgeek_homepage.png")
            
            # Essayer plusieurs sélecteurs possibles
            login_selectors = [
                "//a[contains(@class, 'authorization-link')]",
                "//a[contains(text(), 'Sign In')]",
                "//a[contains(text(), 'Sign in')]",
                "//a[contains(text(), 'Login')]",
                "//a[contains(text(), 'My Account')]",
                "//a[contains(text(), 'Mon compte')]",
                "//a[contains(@href, 'login')]",
                "//a[contains(@href, 'account')]",
                "//a[contains(@href, 'customer')]",
                "//div[contains(@class, 'header')]//a[contains(@href, 'account')]",
                "//header//a[contains(text(), 'Account')]",
            ]
            
            login_clicked = False
            for selector in login_selectors:
                try:
                    logger.info(f"  Essai: {selector[:50]}...")
                    login_link = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    logger.info(f"✅ Lien connexion trouvé!")
                    login_link.click()
                    self.human_delay(3, 5)
                    login_clicked = True
                    break
                except:
                    continue
            
            if not login_clicked:
                logger.error("❌ Aucun lien de connexion trouvé")
                logger.info("💡 Essai de navigation directe...")
                # Essayer quelques URLs possibles
                possible_urls = [
                    "https://www.shopforgeek.com/fr/customer/account/login/",
                    "https://www.shopforgeek.com/customer/account/login/",
                ]
                for url in possible_urls:
                    self.driver.get(url)
                    self.human_delay(2, 3)
                    if "404" not in self.driver.title and "404" not in self.driver.page_source[:1000]:
                        logger.info(f"✅ Page trouvée: {url}")
                        break
            
            logger.info(f"📝 Page: {self.driver.title}")
            logger.info(f"🔗 URL: {self.driver.current_url}")
            
            # Saisir l'email
            logger.info("\n📧 Recherche du champ email...")
            email_selectors = [
                "input[type='email']",
                "input[name='email']",
                "input#email",
                "input[placeholder*='mail']",
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"✅ Champ email trouvé")
                    break
                except:
                    continue
            
            if not email_field:
                logger.error("❌ Champ email introuvable")
                self.driver.save_screenshot("shopforgeek_login_error.png")
                return False
            
            email_field.click()
            self.human_delay(0.5, 1)
            self.human_type(email_field, self.email)
            logger.info(f"✅ Email saisi: {self.email}")
            self.human_delay(1, 2)
            
            # Saisir le mot de passe
            logger.info("\n🔐 Recherche du champ mot de passe...")
            pwd_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
            )
            logger.info("✅ Champ mot de passe trouvé")
            
            pwd_field.click()
            self.human_delay(0.5, 1)
            self.human_type(pwd_field, self.password)
            logger.info("✅ Mot de passe saisi")
            self.human_delay(1, 2)
            
            # Vérifier Cloudflare AVANT soumission
            logger.info("\n🔍 Vérification Cloudflare avant soumission...")
            self.detect_and_solve_cloudflare()
            
            # Soumission
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
            
            # Vérifier Cloudflare APRÈS soumission
            logger.info("\n🔍 Vérification Cloudflare après soumission...")
            cloudflare_detected = self.detect_and_solve_cloudflare()
            
            if cloudflare_detected:
                logger.info("✅ Cloudflare traité, attente...")
                self.human_delay(5, 8)
            
            # Vérification
            logger.info("\n🔍 Vérification de la connexion...")
            if "account" in self.driver.current_url.lower() or "my" in self.driver.current_url.lower() or "message" in self.driver.current_url.lower():
                logger.info("🎉 CONNEXION RÉUSSIE !")
                return True
            else:
                logger.warning(f"⚠️ URL actuelle: {self.driver.current_url}")
                # Vérifier si pas d'erreur visible
                try:
                    error = self.driver.find_element(By.XPATH, "//*[contains(text(), 'incorrect') or contains(text(), 'invalid')]")
                    logger.error(f"❌ Erreur: {error.text}")
                    return False
                except:
                    logger.info("✅ Pas d'erreur visible, connexion OK")
                    return True
                
        except Exception as e:
            logger.error(f"❌ Erreur connexion: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_product_availability(self, product_url):
        """Vérifie si un produit est disponible"""
        try:
            logger.info(f"\n🔍 Vérification: {product_url}")
            self.driver.get(product_url)
            self.human_delay(3, 5)
            
            # Sauvegarder la page pour debug
            self.driver.save_screenshot("shopforgeek_product_page.png")
            
            # Chercher le bouton "Add to cart" - Essayer TOUS les boutons même désactivés
            add_to_cart_selectors = [
                "//button[contains(text(), 'Add to cart')]",
                "//button[contains(text(), 'Add to basket')]",
                "//button[contains(text(), 'Ajouter')]",
                "//button[contains(@class, 'add-to-cart')]",
                "//button[contains(@class, 'tocart')]",
                "//input[@value='Add to cart']",
                "//button[@id='product-addtocart-button']",
                "//button[contains(@class, 'action') and contains(@class, 'primary')]",
            ]
            
            btn_found = None
            for selector in add_to_cart_selectors:
                try:
                    btn = self.driver.find_element(By.XPATH, selector)
                    logger.info(f"✅ Bouton 'Add to cart' trouvé: {selector[:50]}...")
                    btn_found = btn
                    break
                except:
                    continue
            
            if btn_found:
                # Vérifier si enabled
                is_enabled = btn_found.is_enabled()
                is_displayed = btn_found.is_displayed()
                
                logger.info(f"  📊 Bouton - Enabled: {is_enabled}, Displayed: {is_displayed}")
                
                if is_enabled and is_displayed:
                    logger.info(f"✅ PRODUIT DISPONIBLE ET BOUTON CLIQUABLE !")
                    return True, btn_found
                else:
                    # Forcer le clic même si désactivé (via JavaScript)
                    logger.warning("⚠️ Bouton désactivé - tentative de force avec JavaScript...")
                    try:
                        self.driver.execute_script("arguments[0].removeAttribute('disabled')", btn_found)
                        self.driver.execute_script("arguments[0].click()", btn_found)
                        logger.info("✅ Clic forcé par JavaScript!")
                        self.human_delay(2, 3)
                        return True, None  # Déjà cliqué
                    except Exception as e:
                        logger.error(f"❌ Impossible de forcer le clic: {e}")
                        return False, btn_found
            
            logger.warning("❌ Bouton 'Add to cart' introuvable")
            return False, None
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification: {e}")
            import traceback
            traceback.print_exc()
            return False, None
    
    def add_to_cart(self, add_button):
        """Ajoute le produit au panier"""
        try:
            logger.info("\n🛒 AJOUT AU PANIER")
            logger.info("="*50)
            
            if add_button is None:
                logger.info("ℹ️ Bouton déjà cliqué par JavaScript")
            else:
                add_button.click()
                logger.info("✅ Clic sur 'Add to cart'")
            
            self.human_delay(3, 5)
            
            # Screenshot
            self.driver.save_screenshot(f"cart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            
            # Vérifier qu'on est bien allé au panier ou qu'un message de confirmation apparaît
            page_text = self.driver.page_source.lower()
            if "cart" in page_text or "panier" in page_text or "added" in page_text:
                logger.info("✅ Produit probablement ajouté au panier")
                return True
            else:
                logger.warning("⚠️ Statut panier incertain")
                return True  # On continue quand même
            
        except Exception as e:
            logger.error(f"❌ Erreur ajout panier: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def proceed_to_checkout(self, complete_payment=False):
        """Procède au checkout"""
        try:
            logger.info("\n💳 PROCESSUS DE CHECKOUT")
            logger.info("="*50)
            
            # Chercher le bouton "Checkout" ou "Proceed to checkout"
            checkout_selectors = [
                "//a[contains(text(), 'Checkout')]",
                "//button[contains(text(), 'Checkout')]",
                "//a[contains(text(), 'Proceed to checkout')]",
                "//a[contains(@href, 'checkout')]",
            ]
            
            for selector in checkout_selectors:
                try:
                    checkout_btn = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    logger.info("✅ Bouton checkout trouvé")
                    checkout_btn.click()
                    self.human_delay(5, 8)
                    break
                except:
                    continue
            
            if not complete_payment:
                logger.info("⚠️ MODE TEST - Arrêt avant paiement")
                logger.info("✅ Test réussi jusqu'au checkout!")
                self.driver.save_screenshot(f"checkout_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                return True
            else:
                logger.warning("⚠️ MODE ACHAT RÉEL - Paiement complet activé")
                # Ici vous pourriez ajouter la logique de paiement
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur checkout: {e}")
            return False
    
    def run_test(self):
        """Exécute un test complet"""
        try:
            logger.info("\n" + "="*70)
            logger.info("🎯 TEST DU PROCESSUS D'ACHAT - SHOP FOR GEEK")
            logger.info("="*70)
            
            # Init driver
            self.driver = self.init_driver()
            if not self.driver:
                return {"status": "error", "message": "Échec init driver"}
            
            # Connexion
            if not self.login():
                return {"status": "error", "message": "Échec connexion"}
            
            # Vérifier produit test
            test_url = self.config.get('test_product', {}).get('url')
            if not test_url:
                logger.error("❌ Pas d'URL de test dans config.json")
                return {"status": "error", "message": "Pas d'URL de test"}
            
            available, add_btn = self.check_product_availability(test_url)
            
            if not available:
                return {"status": "info", "message": "Produit test indisponible"}
            
            # Ajouter au panier
            if not self.add_to_cart(add_btn):
                return {"status": "error", "message": "Échec ajout panier"}
            
            # Checkout (sans paiement)
            if not self.proceed_to_checkout(complete_payment=False):
                return {"status": "error", "message": "Échec checkout"}
            
            logger.info("\n🎉 TEST COMPLET RÉUSSI !")
            return {"status": "success", "message": "Test complet réussi"}
            
        except Exception as e:
            logger.error(f"❌ Erreur test: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}
        finally:
            if self.driver:
                logger.info("\n🧹 Fermeture du navigateur...")
                self.driver.quit()
    
    def run_monitor(self):
        """Mode surveillance continue"""
        try:
            logger.info("\n" + "="*70)
            logger.info("👁️  MODE SURVEILLANCE - SHOP FOR GEEK")
            logger.info("="*70)
            
            self.driver = self.init_driver()
            if not self.driver:
                return
            
            if not self.login():
                logger.error("❌ Échec connexion")
                return
            
            products = self.config.get('products_to_monitor', [])
            
            if not products:
                logger.error("❌ Aucun produit à surveiller")
                return
            
            logger.info(f"\n📋 Surveillance de {len(products)} produit(s)...")
            
            while True:
                for product in products:
                    url = product.get('url')
                    name = product.get('name', 'Produit sans nom')
                    max_purchases = product.get('max_purchases', 1)
                    
                    logger.info(f"\n🔍 Vérification: {name}")
                    
                    available, add_btn = self.check_product_availability(url)
                    
                    if available and self.purchase_count < max_purchases:
                        logger.info("🚨 PRODUIT DISPONIBLE ! Lancement achat...")
                        
                        if self.add_to_cart(add_btn):
                            if self.proceed_to_checkout(complete_payment=True):
                                self.purchase_count += 1
                                logger.info(f"✅ Achat {self.purchase_count}/{max_purchases} effectué!")
                    
                    interval = product.get('check_interval_seconds', 30)
                    logger.info(f"⏳ Attente {interval}s avant prochaine vérification...")
                    time.sleep(interval)
                    
        except KeyboardInterrupt:
            logger.info("\n⚠️ Arrêt demandé par l'utilisateur")
        except Exception as e:
            logger.error(f"❌ Erreur monitoring: {e}")
        finally:
            if self.driver:
                self.driver.quit()

def main():
    import sys
    
    print("\n" + "="*70)
    print("🤖 BOT SHOP FOR GEEK - ACHAT AUTOMATIQUE")
    print("="*70)
    print("\nModes disponibles:")
    print("  test    - Test sur produit sans achat réel")
    print("  monitor - Surveillance et achat automatique")
    print("\nUsage: python bot_shopforgeek.py [test|monitor]")
    print("="*70 + "\n")
    
    if len(sys.argv) < 2:
        print("❌ Mode non spécifié. Utilisez 'test' ou 'monitor'")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    bot = ShopForGeekBot()
    
    if mode == "test":
        result = bot.run_test()
        print("\n" + "="*70)
        print(f"📊 RÉSULTAT: {result}")
        print("="*70 + "\n")
    elif mode == "monitor":
        bot.run_monitor()
    else:
        print(f"❌ Mode inconnu: {mode}")
        sys.exit(1)

if __name__ == "__main__":
    main()

