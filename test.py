import requests

url = "https://www.datart.cz/kosik?do=addProduct&id=1576290"

payload = {}
headers = {
  'sec-ch-ua-platform': '"Windows"',
  'X-Requested-With': 'XMLHttpRequest',
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
  'Accept': '*/*',
  'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
  'DNT': '1',
  'sec-ch-ua-mobile': '?0',
  'Sec-Fetch-Site': 'same-origin',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Dest': 'empty',
  'host': 'www.datart.cz',
  'Cookie': '__exponea_ab_Global_segmentation__=Target%20Group; __exponea_etc__=6bc8b233-881a-4380-b2bd-0e21e93d1fdf; __exponea_time2__=0.02069258689880371; _ga=GA1.1.63997422.1739197706; _ga_0NHJLMQPVB=GS1.1.1739197705.1.1.1739198056.54.0.0; _gcl_au=1.1.1341734911.1739197708; _gcl_aw=GCL.1739197711.EAIaIQobChMIzeCUpai5iwMV_JqDBx175wcBEAAYASAAEgL4VfD_BwE; _gcl_gs=2.1.k1$i1739197704$u34322228; _uetsid=4a038ed0e7bb11efb5bc1b6cf70c8d0d; _uetvid=4a039bb0e7bb11efa0c287d2596416d0; cc-settings=%7B%22categories%22%3A%5B%22functionality_storage%22%2C%22personalization_storage%22%2C%22ad_storage%22%2C%22analytics_storage%22%5D%2C%22level%22%3A%5B%22functionality_storage%22%2C%22personalization_storage%22%2C%22ad_storage%22%2C%22analytics_storage%22%5D%2C%22revision%22%3A0%2C%22data%22%3A%7B%22last_action_date%22%3A%222025-02-10T14%3A28%3A28.037Z%22%7D%2C%22rfc_cookie%22%3Atrue%2C%22consent_date%22%3A%222025-02-10T14%3A28%3A27.921Z%22%2C%22consent_uuid%22%3A%22844bb0ee-3ae8-47f4-aa15-181c1440bfd1%22%2C%22last_consent_update%22%3A%222025-02-10T14%3A28%3A27.921Z%22%7D; udid=w6we0DFqPKTt5y3EQlE8o0fhGGGiTg_G@1739197717926@1739197717926; BIGipServerly/REuAVIBGDhezrpJNP3Q=!83vrdmnPXy1pdiKbUUZwSO1g9TorzsNg2szI8Uz/fD0GiCmNuTLdWvxCuIwcP9J7SOW+q7bjYEr0sh8=; PHPSESSID=b1eb8351-4a88-4ea4-9c99-0d1aa0165761; TS01e75142=016376dc4d785f8fbd9846229fd78ec9c079aac0cfb17e263a4c4e2fc4bd96bdf9afffc33ba6a3fd76411197031fe0931dab61d8b3577d8504f77b1ca5c4bc94a5558667be5cc0f7b2de5549f1a299834f98d3df63461bf245d0806c666c7f87ea754907f8; TS25f8cb17027=0882048cf5ab2000e8b6bcab60e8f56857a08832f2e0a4a9ac88399153e33d168eee97107c9fccf6083b509c1c11300066051468b2e82f7033e7f3b0a7cbf8a380155741bf725e89afd7095733a94f3db64057c13388dce350f6bbc67dffe660; __rtbh.lid=%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%22Bzll4jx17TpWMUzk9nRl%22%2C%22expiryDate%22%3A%222026-02-10T14%3A33%3A00.715Z%22%7D; __rtbh.uid=%7B%22eventType%22%3A%22uid%22%2C%22id%22%3A%220%22%2C%22expiryDate%22%3A%222026-02-10T14%3A33%3A01.237Z%22%7D; _nss=1; customer_history={"products":[{"index":0,"product":1578603},{"index":1,"product":1841373},{"index":2,"product":1576290}],"search":[]}; lux_uid=173919770531314657'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
