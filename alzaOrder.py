from dataclasses import dataclass
from AlzaAuth import AlzaAuth
import json
import requests
from rich import print
from bs4 import BeautifulSoup
import re
import tls_client
from tamga import Tamga
from fakeBrnoAddress import FakeBrnoAddress, Address
from typing import Union
import random
import time
from secrets import ADDY_API, SCRAPEOPS_API
# Delivery types
ALZABOX = 1
ALZA_PRODEJNA = 2
PPL_PARCELSHOP = 12
BALIKOVNA = 3
DPD_PICKUP = 21
ZASILKOVNA = 4
ZBOX = 2




# Dataclass for credentials
@dataclass
class Credentials:
    username: str
    password: str

# Dataclass for save_order inputs
@dataclass
class SaveOrderInputs:
    deliveryId: int
    groupId: int
    parcelShopId: int | None
    paymentId: int

class AlzaOrder:
    def __init__(self, credentials=None, email=None, commodityId=None, count=1, save_order_inputs=None, address=None, delivery_types=None, delivery_limit=20, logger: Union[bool, Tamga] = True, order_address=None, proxy=None):
        """Initialize the AlzaOrder class."""
        if isinstance(logger, Tamga):
            self.logger = logger
        elif isinstance(logger, bool):
            self.logger = Tamga(
                logToFile=logger,
                logToConsole=logger
            )

        self.logger.info("Initializing AlzaOrder")
        self.credentials = credentials
        self.email = email
        self.commodityId = commodityId
        self.count = count
        self.save_order_inputs = save_order_inputs
        self.address = address
        self.order_id = None
        self.group_id = None
        self.delivery_types = delivery_types
        self.delivery_limit = delivery_limit
        if order_address is None:
            fake_address = FakeBrnoAddress()
            try:
                self.order_address = fake_address.sheet_address()
            except:
                self.order_address = fake_address.address()
        else:
            self.order_address = order_address
        self.proxy = proxy

        if self.credentials:
            self.logger.debug("Using credentials login")
            self.session = tls_client.Session(client_identifier="chrome_110")
            self.login()
        else:
            self.logger.debug("Using email-based session")
            self.session = tls_client.Session(
                client_identifier="chrome112",
                random_tls_extension_order=True
            )
            self._update_session_headers()

    def get_available_delivery_types(self):
        """Return available delivery types with descriptions."""
        return {
            "ALZABOX": ALZABOX,
            "ALZA_PRODEJNA": ALZA_PRODEJNA,
            "PPL_PARCELSHOP": PPL_PARCELSHOP,
            "BALIKOVNA": BALIKOVNA,
            "DPD_PICKUP": DPD_PICKUP,
            "ZASILKOVNA": ZASILKOVNA,
            "ZBOX": ZBOX
        }

    def select_delivery_types(self):
        """Allow user to select which delivery types to search for."""
        delivery_types = self.get_available_delivery_types()
        
        print("\nAvailable delivery types:")
        for i, (name, type_id) in enumerate(delivery_types.items(), 1):
            print(f"{i}. {name.replace('_', ' ').title()} (ID: {type_id})")
        
        selected_types = []
        while True:
            choice = input("\nEnter the number of a delivery type (or press Enter to finish): ").strip()
            if not choice:
                break
                
            try:
                index = int(choice) - 1
                if 0 <= index < len(delivery_types):
                    type_id = list(delivery_types.values())[index]
                    if type_id not in selected_types:
                        selected_types.append(type_id)
                        print(f"Added {list(delivery_types.keys())[index]}")
                    else:
                        print("Type already selected")
                else:
                    print("Invalid choice")
            except ValueError:
                print("Please enter a valid number")
        
        if not selected_types:
            print("No types selected, using all available types")
            selected_types = list(delivery_types.values())
        
        return selected_types
    
    def get_headers(self):
        response = requests.get(
        url='https://headers.scrapeops.io/v1/browser-headers',
        params={
            'api_key': SCRAPEOPS_API,
            'num_results': '1'}
        )

        return response.json().get('result')[0]

    def _update_session_headers(self):
        """Update session headers."""
        self.logger.debug("Updating session headers")
        # headers = {
        #     'accept': 'application/json, text/javascript, */*; q=0.01',
        #     'accept-language': 'cs-CZ',
        #     'cache-control': 'no-cache',
        #     'content-type': 'application/json; charset=UTF-8',
        #     # 'cookie': 'lb_id=a5b3441a642e59edf7054d955c5c785d; VZTX=12042019220; VST=89c71bb8-29fc-44ec-9d36-1e82d8a8f31c; CriticalCSS=7883470; __cf_bm=DDCGA5dfhnPsFbgY7_qkMI2m3ZSwxrmeboSJKStMciI-1738613278-1.0.1.1-ryuJFuVjnPUoDJA7Il8KuhOW9amHlIRWiW40pPpcYQOmcw.zwSz8Mg77GWSE9yF32VachZv0YFZGySPkP4cIGQ; .AspNetCore.Culture=c%3Dcs-CZ%7Cuic%3Dcs-CZ; IDOX=LxA8wijfCgw1baSEKzbNp0cVUUNmt1H9RbdatqXq5tg=',
        #     'dnt': '1',
        #     'origin': 'https://www.alza.cz',
        #     'priority': 'u=1, i',
        #     'referer': 'https://www.alza.cz/Order2.htm',
        #     'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Microsoft Edge";v="132"',
        #     'sec-ch-ua-mobile': '?0',
        #     'sec-ch-ua-platform': '"Windows"',
        #     'sec-fetch-dest': 'empty',
        #     'sec-fetch-mode': 'cors',
        #     'sec-fetch-site': 'same-origin',
        #     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
        #     'x-requested-with': 'XMLHttpRequest',
        # }
        headers = self.get_headers()
        self.session.headers.update(headers)
        if self.proxy is not None:
            self.session.proxies.update({'http': f"http://{self.proxy}", 'https': f"http://{self.proxy}"})

    def login(self):
        """Handle the login process."""
        try:
            self.logger.info("Starting login process")
            auth = AlzaAuth()
            auth.login(**self.credentials.__dict__)
            self.session = auth.session
            self._update_session_headers()
            self.logger.success("Login successful")
        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            raise

    def add_to_basket(self, commodityId=None, count=None):
        """Add items to the basket."""
        self.logger.debug("Starting add_to_basket")
        try:
            if commodityId is None:
                commodityId = self.commodityId
            if count is None:
                count = self.count

            if commodityId is None:
                self.logger.error("Missing commodityId")
                raise ValueError("commodityId must be provided")

            url = "https://www.alza.cz/api/basket/v1/items"
            json_data = {
                'items': [{'commodityId': commodityId, 'count': count}],
                'pageType': -1,
            }
            
            self.logger.info(f"Adding {count}x item {commodityId} to basket")
            response = self.session.post(url, json=json_data, timeout_seconds=5)
            response_data = self._check_response(response)
            self._check_added_to_basket(response_data)
            
            self.logger.success("Item added to basket")
            return response_data
        except Exception as e:
            self.logger.error(f"Failed to add to basket: {str(e)}")
            raise

    def _check_added_to_basket(self, response_data):
        """Validate if the item was successfully added to the basket."""
        self.logger.debug("Validating basket addition")
        if isinstance(response_data, dict):
            if 'crossSellAppAction' in response_data and 'gtmData' in response_data:
                self.logger.debug("Valid basket addition response")
                return True
            
            if 'message' in response_data:
                error_msg = response_data.get('message', 'Unknown error')
                self.logger.error(f"Basket addition failed: {error_msg}")
                if "nejde koupit" in error_msg:
                    raise Exception(f"Item unavailable: {error_msg}")
                raise Exception(f"Basket error: {error_msg}")
        
        self.logger.error(f"Unexpected basket response format")
        raise Exception("Unexpected response format")

    def fetch_order_id_and_group_id(self):
        """Fetch orderId and groupId from the Order2.htm page."""
        self.logger.info("Fetching order IDs")
        try:
            url = "https://www.alza.cz/Order2.htm"
            response = self.session.get(url, allow_redirects=True)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch order page: HTTP {response.status_code}")
                raise Exception(f"HTTP Error: {response.status_code}")

            soup = BeautifulSoup(response.text, 'html.parser')
            script = soup.find('script', string=re.compile(r'var _pageData\s*='))

            if script:
                match = re.search(r'var _pageData\s*=\s*({.*?});', script.string, re.DOTALL)
                if match:
                    try:
                        page_data = json.loads(match.group(1))
                        self.order_id = page_data.get('data', {}).get('orderId')
                        self.group_id = page_data.get('data', {}).get('groupIds', [None])[0]
                        
                        self.logger.success(f"Order IDs fetched: order_id={self.order_id}, group_id={self.group_id}")
                        return self.order_id, self.group_id
                    except (json.JSONDecodeError, KeyError) as e:
                        self.logger.error(f"Failed to parse order data: {str(e)}")
                        raise
            self.logger.warning(f"No order data found in page {response.text}")
            raise Exception("No data found in the page")
        except Exception as e:
            self.logger.critical(f"Failed to fetch order IDs: {str(e)}")
            raise

    def call_geocode_api(self, query, country="cz", limit=3):
        """Call the geocode API to get latitude and longitude."""
        self.logger.debug(f"Calling geocode API for query: {query}")
        try:
            url = "https://address-service.alza.cz/api/v1/geocode/search/country"
            params = {
                "query": query,
                "country": country,
                "limit": limit
            }
            response = self.session.get(url, params=params)

            if response.status_code == 200:
                self.logger.debug("Geocode API call successful")
                return response.json()
            else:
                self.logger.error(f"Geocode API error: {response.status_code} - {response.text}")
                raise Exception(f"Geocode API error: {response.status_code} - {response.text}")
        except Exception as e:
            self.logger.error(f"Geocode API call failed: {str(e)}")
            raise

    def call_personal_pickup_api(self, latitude, longitude):
        """Call the personalPickup API to get delivery points."""
        self.logger.debug(f"Calling personalPickup API for lat={latitude}, lon={longitude}")
        try:
            # Let user select delivery types
            if self.delivery_types is None:
                self.delivery_types = self.select_delivery_types()

            self.logger.debug(f"Selected delivery types: {self.delivery_types}")
            
            url = "https://www.alza.cz/api/personalPickup/v1/places"
            
            # Create params dict with selected delivery types
            params = {
                f"types[{i}]": type_id 
                for i, type_id in enumerate(self.delivery_types)
            }
            
            # Add other parameters
            params.update({
                "latitude": latitude,
                "longitude": longitude,
                "orderId": self.order_id,
                "groupId": self.group_id,
                "ordering": 0,
                "radius": 10000,
                "limit": self.delivery_limit,
                "offset": 0
            })
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                self.logger.debug("PersonalPickup API call successful")
                return response.json()
            else:
                self.logger.error(f"PersonalPickup API error: {response.status_code} - {response.text}")
                raise Exception(f"PersonalPickup API error: {response.status_code} - {response.text}")
        
        except Exception as e:
            self.logger.error(f"PersonalPickup API call failed: {str(e)}")
            raise

    def get_delivery_point_title(self, place):
        """
        Get the correct title for a delivery point.
        Uses name if the title appears to be just a numeric identifier.
        """
        name = place.get('name', '')
        title = place.get('title', '')
        
        # Helper function to check if string is likely a numeric identifier
        def is_numeric_identifier(s):
            # Remove any surrounding whitespace
            s = s.strip()
            # Check if it matches common identifier patterns:
            # - Single numbers (e.g., "123")
            # - Numbers with prefix/suffix separators (e.g., "ID-123", "123_A")
            import re
            identifier_pattern = r'^[A-Za-z-_]*\d+[A-Za-z-_]*$'
            return bool(re.match(identifier_pattern, s))
        
        # If title is empty or appears to be just a numeric identifier, use name
        if not title or is_numeric_identifier(title):
            return name
        # Otherwise use the title
        return title

    def select_delivery_point(self, pickup_result):
        """Allow the user to select a delivery point by number."""
        self.logger.debug("Selecting delivery point")
        try:
            pickup_places = pickup_result.get("pickupPlaces", {}).get("value", [])
            if not pickup_places:
                self.logger.error("No pickup places found in the API response")
                raise Exception("No pickup places found in the API response.")

            print("\nAvailable Delivery Points:")
            for i, place in enumerate(pickup_places):
                title = self.get_delivery_point_title(place)
                print(f"{i + 1}. {title} - {place.get('addressText')} (Price: {place.get('price')})")

            choice = int(input("\nEnter the number of the delivery point: ")) - 1
            if 0 <= choice < len(pickup_places):
                selected_place = pickup_places[choice]
                title = self.get_delivery_point_title(selected_place)
                self.logger.info(f"Selected delivery point: {title}")
                return {
                    "deliveryId": selected_place.get("deliveryId"),
                    "parcelShopId": selected_place.get("parcelShopId"),
                    "groupId": self.group_id
                }
            else:
                self.logger.error("Invalid delivery point choice")
                raise Exception("Invalid choice.")
        except Exception as e:
            self.logger.error(f"Failed to select delivery point: {str(e)}")
            raise

    def save_order(self, save_order_inputs=None):
        """Save the order details."""
        self.logger.debug("Saving order")
        try:
            if save_order_inputs is None:
                save_order_inputs = self.save_order_inputs

            if save_order_inputs is None:
                self.logger.error("Missing save_order_inputs")
                raise ValueError("save_order_inputs must be provided")

            url = "https://www.alza.cz/Services/EShopService.svc/SaveOrder2"
            json_data = {
                'selectedDeliveriesForGroups': [{
                    'deliveryId': save_order_inputs.deliveryId,
                    'groupId': save_order_inputs.groupId,
                    'deliveryTimeFrameId': None,
                    'deliveryTimeSlotId': None,
                    'parcelShopId': save_order_inputs.parcelShopId,
                }],
                'paymentId': save_order_inputs.paymentId,
                'deliveryZipId': 0,
                'paymentCardId': 0,
                'deliveryAccesoriesIds': '',
                'deliveryAddressId': None,
            }
            response = self.session.post(url, json=json_data)
            self.logger.success("Order saved successfully")
            return self._check_response(response)
        except Exception as e:
            self.logger.error(f"Failed to save order: {str(e)}")
            raise

    def confirm_order(self, save_order_inputs=None):
        """Confirm the order and handle expected ErrorLevel 113."""
        self.logger.debug("Confirming order")
        try:
            if save_order_inputs is None:
                save_order_inputs = self.save_order_inputs

            if self.save_order_inputs is None:
                self.logger.error("Missing save_order_inputs")
                raise ValueError("save_order_inputs must be provided")

            url = "https://www.alza.cz/Services/EShopService.svc/SaveAndConfirmOrder2"
            json_data = {
                'selectedDeliveriesForGroups': [{
                    'deliveryId': self.save_order_inputs.deliveryId,
                    'groupId': self.save_order_inputs.groupId,
                    'deliveryTimeFrameId': None,
                    'deliveryTimeSlotId': None,
                    'parcelShopId': self.save_order_inputs.parcelShopId,
                }],
                'paymentId': self.save_order_inputs.paymentId,
                'deliveryZipId': 0,
                'paymentCardId': 0,
                'deliveryAccesoriesIds': '',
                'deliveryAddressId': None,
            }
            response = self.session.post(url, json=json_data)

            if self._check_response(response, expected_error_level=113):
                self.logger.success("Order confirmed successfully")
            return response
        except Exception as e:
            self.logger.error(f"Failed to confirm order: {str(e)}")
            raise
        
    def gen_email(self):
        url = 'https://app.addy.io/api/v1/aliases'
        payload = {
            "domain": "bumbl.anonaddy.com",
            "description": "rtx",
            "format": "uuid",
        }
        
        headers = {
        'Authorization': f'Bearer {ADDY_API}',
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
        }

        response = requests.request('POST', url, headers=headers, json=payload)
        return response.json()["data"].get("email")

    def save_order3(self):
        """Save order details including user information."""
        self.logger.debug("Saving order details (step 3)")            
        try:
            # if self.credentials:
            #     email = self.credentials.username
            # elif self.email:   
            #     email = self.email
            # else:
            #     email = self.gen_email()
            url = "https://www.alza.cz/Services/EShopService.svc/SaveOrder3"
            payload = {
                "registerUser": False,
                "login": self.order_address.email,
                "password": None,
                "name": self.order_address.name,
                "street": self.order_address.street,
                "city": self.order_address.city_part,
                "zip": self.order_address.zip_code,
                "phone": self.order_address.phone_number,
                "email": self.order_address.email,
                "countryId": 0,
                "isic": "",
                "ico": None,
                "dic": None,
                "icDph": None,
                "bankAccount": None,
                "bankCode": None,
                "specificSymbol": None,
                "internalNumber": None,
                "iban": None,
                "bic": None,
                "bankAccountOwnerName": None,
                "deliveryName": None,
                "deliveryFirm": None,
                "deliveryStreet": None,
                "deliveryCity": None,
                "deliveryZip": None,
                "deliveryNote": None,
                "deliveryPhone": None,
                "news": True,
                "smsCode": None,
                "eduId": None,
                "personalIdentificationNumber": None,
                "validateTaxIdentificationNumber": None,
                "userVatSpecificationTypeValue": None
            }
            response = self.session.post(url, json=payload)
            self.logger.success("Order details saved successfully")
            return self._check_response(response)
        except Exception as e:
            self.logger.error(f"Failed to save order details: {str(e)}")
            raise

    def check_order4(self):
        """Check the order before final submission."""
        self.logger.debug("Checking order (step 4)")
        try:
            url = "https://www.alza.cz/Services/EShopService.svc/CheckOrder4"
            response = self.session.post(url)
            self.logger.success("Order check completed successfully")
            return self._check_response(response)
        except Exception as e:
            self.logger.error(f"Failed to check order: {str(e)}")
            raise

    def send_order4(self):
        """Finalize the order submission."""
        self.logger.debug("Sending order (step 4)")
        try:
            url = "https://www.alza.cz/Services/EShopService.svc/SendOrder4"
            payload = {
                "quotation": False,
                "internalDescription": "",
                "neoAgreement": False,
                "verificationId": None,
                "verificationCode": None,
                "consents": [{"consentId": "2", "value": True}]
            }
            response = self.session.post(url, json=payload)
            self.logger.success("Order sent successfully")
            return self._check_response(response)
        except Exception as e:
            self.logger.error(f"Failed to send order: {str(e)}")
            raise

    def finalize_order(self):
        """Final step to confirm the order and get the order details."""
        self.logger.debug("Finalizing order")
        try:
            url = "https://www.alza.cz/Order5.htm"
            response = self.session.post(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            self.order_link = "https://www.alza.cz" + soup.find('div', class_='doneInfoBlock').find('a')['href']
            self.logger.success(f"Order finalized successfully: {self.order_link}")
            return self.order_link
        except Exception as e:
            self.logger.error(f"Failed to finalize order: {str(e)}")
            raise

    def _check_response(self, response, expected_error_level=0):
        """Check if the response is JSON and parse it."""
        self.logger.debug("Checking API response")
        try:
            data = response.json()
            if 'd' in data and 'ErrorLevel' in data['d']:
                error_level = data['d']['ErrorLevel']
                error_message = data['d'].get('Message', 'No message')
                
                if error_level == expected_error_level or error_message is None:
                    self.logger.success(f"Request to {response.url} succesfull")
                    return True
                else:
                    self.logger.error(f"API Error response: {error_message}")
                    return False
            return data
        except ValueError:
            self.logger.error(f"Invalid JSON response - status code {response.status_code}")
            return response.text

    def make_order(self, choose_closest=True):
        """Execute the entire order process in one function call."""
        self.logger.info("Starting order process")
        try:
            if self.credentials:
                self.login()
            self.add_to_basket()
            if self.save_order_inputs is None:
                self.fetch_order_id_and_group_id()
                self.logger.debug(f"Using address: {self.address}")

                geocode_result = self.call_geocode_api(self.address)
                if geocode_result.get("items"):
                    position = geocode_result["items"][0].get("position", {})
                    latitude = position.get("lat")
                    longitude = position.get("lon")

                    pickup_result = self.call_personal_pickup_api(latitude, longitude)

                    if choose_closest:
                        pickup_places = pickup_result.get("pickupPlaces", {}).get("value", [])
                        if pickup_places:
                            delivery_details = {
                                "deliveryId": pickup_places[0].get("deliveryId"),
                                "parcelShopId": pickup_places[0].get("parcelShopId"),
                                                            "groupId": self.group_id
                            }
                            self.logger.info(f"Automatically selected closest delivery point: {pickup_places[0].get('name')}")
                        else:
                            self.logger.error("No pickup places found in the API response")
                            raise Exception("No pickup places found in the API response.")
                    else:
                        delivery_details = self.select_delivery_point(pickup_result)

                    self.save_order_inputs = SaveOrderInputs(
                        deliveryId=delivery_details["deliveryId"],
                        groupId=delivery_details["groupId"],
                        parcelShopId=delivery_details["parcelShopId"],
                        paymentId=211  # Default payment ID
                    )
                else:
                    self.logger.error("No items found in the geocode API response")
                    raise Exception("No items found in the geocode API response.")
            time.sleep(random.uniform(1, 3))
            self.save_order()
            time.sleep(random.uniform(1, 3))
            self.confirm_order()
            time.sleep(random.uniform(1, 3))
            self.save_order3()
            time.sleep(random.uniform(1, 3))
            self.check_order4()
            time.sleep(random.uniform(1, 3))
            self.send_order4()
            time.sleep(random.uniform(1, 3))
            self.finalize_order()
            self.logger.success("Order process completed successfully")
        except Exception as e:
            self.logger.critical(f"Order process failed: {str(e)}")
            raise

    def get_pickup_details(self):
        try:
            self.add_to_basket()
            self.fetch_order_id_and_group_id()
            self.logger.debug(f"Using address: {self.address}")

            geocode_result = self.call_geocode_api(self.address)

            self.fetch_order_id_and_group_id()
            self.logger.debug(f"Using address: {self.address}")

            if geocode_result.get("items"):
                position = geocode_result["items"][0].get("position", {})
                latitude = position.get("lat")
                longitude = position.get("lon")
                pickup_result = self.call_personal_pickup_api(latitude, longitude)
                delivery_details = self.select_delivery_point(pickup_result)

                order_inputs = SaveOrderInputs(
                    deliveryId=delivery_details["deliveryId"],
                    groupId=delivery_details["groupId"],
                    parcelShopId=delivery_details["parcelShopId"],
                    paymentId=163  # Default payment ID
                )

                return order_inputs
            else:
                    self.logger.error("No items found in the geocode API response")
                    raise Exception("No items found in the geocode API response.")
        except Exception as e:
            self.logger.critical(f"Order process failed: {str(e)}")
            raise

def main():
    # Example 1: Using credentials
    # credentials = Credentials(username='username', password='password')
    # alza_order_with_credentials = AlzaOrder(
    #     credentials=credentials,
    #     commodityId=12433839,
    #     count=1,
    #     address="Brno"
    # )
    # alza_order_with_credentials.make_order(choose_closest=False)

    # Example 2: Using only email
    alza_order_with_email = AlzaOrder(
        email="example@example.com",
        commodityId=12614383,
        count=1,
        address="Vinařská 499/5, 603 00 Brno - Pisárky",
        delivery_types=[ALZABOX],
        delivery_limit=4,
        proxy='104.207.42.3:3128'
    )
    alza_order_with_email.make_order()
    # alza_order_with_email = AlzaOrder(
    #     email="example@example.com",
    #     commodityId=12433839,
    #     count=1,
    #     save_order_inputs=SaveOrderInputs(deliveryId=1024, groupId=263684818, parcelShopId=1105722, paymentId=103),
    #     proxy='104.207.55.78:3128'
    # )
    # print(alza_order_with_email.get_pickup_details())
    # alza_order_with_email.make_order(choose_closest=False)

if __name__ == "__main__":
    main()