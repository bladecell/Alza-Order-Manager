import gspread
import re
from tamga import Tamga
from curl_cffi import requests
from alzaOrder import AlzaOrder, ALZABOX, ALZA_PRODEJNA
import apprise
from typing import Union, List, Tuple
import random
import concurrent.futures
import time
from secrets import MATRIX_URL, SHEET, SCRAPEOPS_API



class AlzaOrderManager:
    def __init__(self, credentials_path: str, sheet_url: str, logger: Union[bool, Tamga] = True, proxy_file='./logs/proxy.txt'):
        self.credentials_path = credentials_path
        self.sheet_url = sheet_url
        self.client = gspread.service_account(credentials_path)
        self.sheet = self.client.open_by_url(sheet_url)
        self.worksheet = self.sheet.worksheet('alzaOrderList')
        self.order_sheet = self._get_or_create_order_sheet()
        self.apobj = apprise.Apprise()
        self.apobj.add(MATRIX_URL)
        if isinstance(logger, Tamga):
            self.logger = logger
        elif isinstance(logger, bool):
            self.logger = Tamga(
                logToFile=logger,
                logToConsole=logger
            )
        self._load_proxies(proxy_file)

    def _load_proxies(self, file_path):
        with open(file_path, "r") as f:
            self.proxy_list = [line.strip() for line in f if line.strip()]

    def _get_random_proxy(self):
        return random.choice(self.proxy_list)

    def _get_or_create_order_sheet(self):
        """
        Get or create the 'alzaOrders' worksheet.
        """
        try:
            return self.sheet.worksheet('alzaOrders')
        except gspread.WorksheetNotFound:
            # Create the worksheet if it doesn't exist
            return self.sheet.add_worksheet(title='alzaOrders', rows=100, cols=2)

    def gen_email(self, api: str) -> str:
        headers = {
            'Authorization': 'Bearer ' + api,
        }
        response = requests.post('https://quack.duckduckgo.com/api/email/addresses', headers=headers, impersonate="chrome120")
        return response.json()['address'] + '@duck.com'

    def is_available(self, product_id):
        time.sleep(random.uniform(1, 3))
        api_url = f"https://www.alza.cz/api/router/legacy/catalog/product/{product_id}"
        proxies = {"https": f"http://{self._get_random_proxy()}"}

        request = requests.get(api_url, impersonate="chrome120", timeout=5, headers=self.get_headers(), proxies=proxies)
        if request.status_code != 200:
            raise Exception(f"Request Status Code {request.status_code}")

        return request.json().get("data", {}).get("can_buy", False)

    def get_headers(self):
        response = requests.get(
            url='https://headers.scrapeops.io/v1/browser-headers',
            params={
                'api_key': SCRAPEOPS_API,
                'num_results': '1'}
        )
        return response.json().get('result')[0]

    def _process_record(self, record: dict) -> Tuple[str, AlzaOrder] | None:
        """Processes a single record to check availability and create an order."""
        match = re.search(r'd(\d{8}).htm$', record.get('url', ""))
        if match:
            commodity_id = match.group(1)
            try:
                if self.is_available(commodity_id):
                    self.logger.success(f"Item {commodity_id} is available")
                    temp_order = AlzaOrder(
                        commodityId=int(commodity_id),
                        count=1,
                        address=record.get('address'),
                        delivery_types=[ALZA_PRODEJNA],
                        logger=self.logger,
                        proxy=self._get_random_proxy()
                    )
                    return record.get('url'), temp_order
                else:
                    self.logger.warning(f"Item {commodity_id} is not available for purchase")
            except Exception as e:
                self.logger.error(f"Error checking availability for item {commodity_id}: {e}")
        return None

    def fetch_orders(self) -> List[Tuple[str, AlzaOrder]]:
        """
        Fetch orders from the 'alzaOrderList' worksheet using ThreadPoolExecutor.
        """
        records = self.worksheet.get_all_records()
        orders = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(self._process_record, records)

            for result in results:
                if result:
                    orders.append(result)

        return orders

    def write_order_to_sheet(self, item_url: str, order_link: str):
        """
        Write the item URL and order link to the 'alzaOrders' sheet.
        """
        # Find the next empty row
        next_row = len(self.order_sheet.get_all_values()) + 1
        # Update the sheet with the item URL and order link
        self.order_sheet.update(f'A{next_row}:B{next_row}', [[item_url, order_link]])
        self.logger.info(f"Written to 'alzaOrders': Item URL = {item_url}, Order Link = {order_link}")

    def process_orders(self):
        """
        Process orders and write them to the 'alzaOrders' sheet.
        """
        orders = self.fetch_orders()

        # Use a ThreadPoolExecutor to run orders concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:  # You can adjust the number of max_workers
            futures = [executor.submit(self.process_single_order, item_url, order) for item_url, order in orders]

            # Wait for all futures to complete
            concurrent.futures.wait(futures)

    def process_single_order(self, item_url, order):
        """
        Process a single order and handle exceptions.
        """
        try:
            order.make_order()
            # Write the item URL and order link to the 'alzaOrders' sheet
            self.write_order_to_sheet(item_url, order.order_link)
            self.sendNotification(f"RTX Order successful: {order.order_link}")
        except Exception as e:
            self.logger.error(f"Failed to make order: {e}")

    def sendNotification(self, markdown_message):
        self.apobj.notify(
            body=markdown_message,
        )


if __name__ == "__main__":
    credentials_path = 'credentials.json'
    sheet_url = SHEET

    order_manager = AlzaOrderManager(credentials_path, sheet_url)
    start_time = time.time()
    order_manager.process_orders()
    end_time = time.time()
    print(f"Time taken: {end_time-start_time}")
