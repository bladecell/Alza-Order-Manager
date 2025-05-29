import tls_client
import re
import json
from urllib.parse import urljoin, parse_qs, urlparse
from rich import print
import secrets
from bs4 import BeautifulSoup

class AlzaAuth:
    def __init__(self):
        self.session = tls_client.Session(
            client_identifier="chrome112",
            random_tls_extension_order=True
        )
        self.base_url = "https://identity.alza.cz"
        self.callback_url = "https://www.alza.cz/external/callback"
        self.session.proxies.update({'http': 'http://156.228.177.216:3128', 'https': 'https://156.228.177.216:3128'})

    def extract_verification_token(self, html):
        """Extract CSRF token from login page HTML with better error handling"""
        try:
            match = re.search(
                r'name="__RequestVerificationToken"[^>]*value="([^"]+)"',
                html,
                re.DOTALL
            )
            if not match:
                raise ValueError("Verification token not found in page")
            return match.group(1)
        except Exception as e:
            print(f"[red]Error extracting token: {str(e)}[/red]")
            raise

    def get_login_page(self):
        """Fetch initial login page with improved error handling"""
        try:
            params = {
                'ReturnUrl': '/connect/authorize/callback?' + '&'.join([
                    'acr_values=country%3ACZ%20regLink%3AProduction_registration%20source%3AWeb',
                    'client_id=alza',
                    'culture=cs-CZ',
                    'nonce=random_nonce',
                    'redirect_uri=https%3A%2F%2Fwww.alza.cz%2Fexternal%2Fcallback%3Fnav%3DLz9sb2dvdXRTdWNjZXNzPTE',
                    'response_mode=form_post',
                    'response_type=code%20id_token',
                    'scope=email%20openid%20profile%20alza%20offline_access',
                    f'state={secrets.token_urlsafe(32)}'
                ])
            }

            response = self.session.get(
                f"{self.base_url}/account/login",
                params=params,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
                    'Accept-Language': 'en-US,en;q=0.9'
                }
            )

            
            if response.status_code != 200:
                raise ValueError(f"Login page returned status {response.status_code}")

            return response
        except Exception as e:
            print(f"[red]Failed to get login page: {str(e)}[/red]")
            raise

    def parse_form_response(self, html):
        """Parse form data using BeautifulSoup"""
        try:
            
            with open("debug_form.html", "w", encoding="utf-8") as f:
                f.write(html)

            
            soup = BeautifulSoup(html, 'html.parser')

            
            form = soup.find('form')
            if not form:
                raise ValueError("No form found in the response")

            
            inputs = form.find_all('input', {'type': 'hidden'})
            if not inputs:
                raise ValueError("No hidden input fields found in the form")

            
            form_data = {}
            required_fields = ['code', 'id_token', 'scope', 'state', 'session_state']

            for input_field in inputs:
                name = input_field.get('name')
                value = input_field.get('value')
                if name in required_fields:
                    form_data[name] = value
                    print(f"[green]✓ Found {name}[/green]")

            
            missing_fields = [field for field in required_fields if field not in form_data]
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

            return form_data

        except Exception as e:
            print(f"[red]Error parsing form data: {str(e)}[/red]")
            print("[yellow]First 1000 characters of response:[/yellow]")
            print(html[:1000])
            print("\n[yellow]Saved full response to debug_form.html[/yellow]")
            raise

    def login(self, username, password):
        """Complete authentication flow with enhanced error handling"""
        try:
            
            login_page = self.get_login_page()
            verification_token = self.extract_verification_token(login_page.text)
            print("[green]✓ Obtained verification token[/green]")

            
            login_payload = {
                'ReturnUrl': parse_qs(urlparse(login_page.url).query)['ReturnUrl'][0],
                'CountryCode': 'CZ',
                'Username': username,
                'Password': password,
                '__RequestVerificationToken': verification_token
            }

            login_response = self.session.post(
                f"{self.base_url}/account/login",
                data=login_payload,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Origin': self.base_url,
                    'Referer': login_page.url,
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
                },
                allow_redirects=False
            )

            
            if login_response.status_code != 302:
                print(f"[red]Unexpected login response: {login_response.status_code}[/red]")
                print(f"[yellow]Response text:[/yellow] {login_response.text[:500]}")
                return False

            
            oauth_redirect = urljoin(self.base_url, login_response.headers.get('Location'))
            oauth_response = self.session.get(
                oauth_redirect,
                allow_redirects=False,
                headers={'Referer': login_page.url}
            )

            if oauth_response.status_code != 302:
                print(f"[red]Unexpected OAuth response: {oauth_response.status_code}[/red]")
                return False

            
            final_url = urljoin(self.base_url, oauth_response.headers.get('Location'))
            form_response = self.session.get(final_url, allow_redirects=False)

            if form_response.status_code != 200:
                print(f"[red]Failed to get final form: {form_response.status_code}[/red]")
                return False

            
            try:
                form_data = self.parse_form_response(form_response.text)
                print("[green]✓ Successfully parsed form data[/green]")
            except Exception as e:
                print(f"[red]Failed to parse form data: {str(e)}[/red]")
                return False

            
            callback_response = self.session.post(
                "https://www.alza.cz/external/callback?nav=Lz9sb2dvdXRTdWNjZXNzPTE",
                data=form_data,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Origin': self.base_url,
                    'Referer': final_url,
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
                }
            )

            
            if 'ApplicationCookie' not in self.session.cookies:
                print("[red]Missing applicationcookie in final response[/red]")
                print("[yellow]Final cookies:[/yellow]", self.session.cookies)
                print("[yellow]Callback response status:[/yellow]", callback_response.status_code)
                print("[yellow]Callback response text:[/yellow]", callback_response.text[:1000])
                return False

            print("[green]✓ Authentication successful[/green]")
            return True

        except Exception as e:
            print(f"[red]✗ Authentication failed: {str(e)}[/red]")
            return False

    def get_application_cookie(self):
        """Retrieve the application cookie from session"""
        return self.session.cookies.get('ApplicationCookie')

    def get_cookies(self):
        """Get all cookies as dict"""
        return dict(self.session.cookies)


def main():
    auth = AlzaAuth()

    
    credentials = {
        'username': 'exit-guts-district@duck.com',
        'password': 'tinkling-flammable-smelting'
    }

    if auth.login(**credentials):
        print("\n[bold]Authentication Details:[/bold]")
        print(f"Application Cookie: [cyan]{auth.get_application_cookie()}[/cyan]")

        
        test_response = auth.session.get("https://www.alza.cz/")
        if test_response.status_code == 200:
            print("\n[green]✓ Successfully accessed account page[/green]")
            with open("account_page.html", "w", encoding="utf-8") as f:
                f.write(test_response.text)
            print("[green]✓ Account page saved to account_page.html[/green]")
        else:
            print(f"\n[red]✗ Account page access failed ({test_response.status_code})[/red]")
    else:
        print("[red]✗ Authentication failed[/red]")


if __name__ == "__main__":
    main()