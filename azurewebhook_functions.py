import time
import hashlib
import ast
import json
import requests
from temba_client.v2 import TembaClient
from temba_client.exceptions import TembaBadRequestError


class Broker:

    def __init__(self):
        print("A transferTo object is created.")

    def initiate_rapidpro_json(self, json_data):
        self.json_data = json_data
        self.phonee164 = "tel:" + self.json_data["phone"]
        print(self.phonee164)
        self.phone = self.json_data["phone"].replace("+", "")
        print(self.phone)
        print(json_data)

    def get_rapidpro_fields(self):
        client = TembaClient(self.rapidpro_url, self.rapidpro_apikey)
        try:
            contact = client.get_contacts(urn=self.phonee164).first()
            self.value = contact.fields["transferto_bundle"]
            self.simulate = contact.fields["transferto_simulate"]
            print(self.value)
            print(self.simulate)
            print(contact)
            return (contact.fields)

        except:
            raise ValueError("rapidpro query failed")

    def create_rapidpro_contact(self, name, phone, registration_number):
        client = TembaClient(self.rapidpro_url, self.rapidpro_apikey)
        fields = {"identification": registration_number}
        try:
            print(phone)
            existing_contacts = len(client.get_contacts(urn=[phone]).first().urns)
            print(existing_contacts)
            if (existing_contacts == 0):
                try:
                    contact = client.create_contact(
                        name=name,
                        urns=[phone],
                        groups=["Smoking Cessation"],
                        fields=fields,
                    )
                except ValueError:
                    print("Value Error")
                except TembaBadRequestError:
                    print("Number already allocated")
            elif (existing_contacts > 0):
                print("Contact already exists")
                contact = client.update_contact(
                    contact=phone,
                    name=name,
                    groups=["Smoking Cessation"],
                    fields=fields,
                )
            flow_start = client.create_flow_start(
                "df1e0286-55d5-464c-bae1-3d1cf3c8dd67",
                urns=[phone],
                restart_participants=True,
                extra=None,
            )
            print(flow_start)
        except:
            print("exception in rp update")
        return ("done")

    def read_transferto_credentials_file(self, filename):
        try:
            with open(filename, encoding="utf-8") as data_file:
                data = json.loads(data_file.read())
            self.apikey = data["transferto_apikey"]
            self.apisecret = data["transferto_apisecret"]
            self.login = data["transferto_login"]
            self.url_login = data["transferto_url_login"]
            self.token = data["transferto_token"]
            self.airtime_url = data["transferto_airtime_url"]
            self.products_url = data["transferto_products_url"]
            print(self.products_url)
        except:
            raise FileNotFoundError("Can't initiate the transferto Creds")

    def read_rapidpro_credentials_file(self, filename):
        try:
            with open(filename, encoding="utf-8") as data_file:
                data = json.loads(data_file.read())
            self.rapidpro_apikey = data["rapidpro_apikey"]
            self.rapidpro_url = data["rapidpro_url"]
            print(self.rapidpro_apikey)
            print(self.rapidpro_url)
        except:
            raise FileNotFoundError("Can't initiate the rapidpro credentials")

    def payload_generation(self):
        external_id = str(int(1000 * time.time()))

        # now create the json object that will be used
        fixed_recharge = {
            "account_number": self.phone,
            "product_id": self.product_id,
            "external_id": external_id,
            "simulation": self.simulate,
            "sender_sms_notification": "1",
            "sender_sms_text": "Sender message",
            "recipient_sms_notification": "1",
            "recipient_sms_text": "",
            "sender": {
                "last_name": "",
                "middle_name": " ",
                "first_name": "",
                "email": "",
                "mobile": "08443011",
            },
            "recipient": {
                "last_name": "",
                "middle_name": "",
                "first_name": "",
                "email": "",
                "mobile": self.phone,
            },
        }
        self.fixed_recharge = fixed_recharge
        return (fixed_recharge)

    def get_transferto_goods(self, url):
        """
        This function provides the GET functionality to the
        TransferTo API for Goods and Services
        """
        import requests
        import time
        import hashlib
        import hmac
        import base64

        nonce = int(time.time())
        message = bytes((self.apikey + str(nonce)).encode("utf-8"))
        secret = bytes(self.apisecret.encode("utf-8"))
        hmac = base64.b64encode(
            hmac.new(secret, message, digestmod=hashlib.sha256).digest()
        )
        headers = {}
        headers["X-TransferTo-apikey"] = self.apikey
        headers["X-TransferTo-nonce"] = str(nonce)
        headers["x-transferto-hmac"] = hmac
        try:
            response = requests.get(url, headers=headers)
        except:
            print("Failed get_transferto_goods")
        return (response)

    def post_transferto_goods(self, url):
        """
        This function provides the POST functionality to the
        TransferTo API for Goods and Services
        This function generates the header files for the TransferTo product
        API.
        It uses the APIKEY, APISECRET and URL endpoint.
        It feeds the payload to the API endpoint using a POST
        """
        import requests
        import time
        import hashlib
        import hmac
        import base64

        nonce = int(time.time())
        message = bytes((self.apikey + str(nonce)).encode("utf-8"))
        secret = bytes(self.apisecret.encode("utf-8"))
        hmac = base64.b64encode(
            hmac.new(secret, message, digestmod=hashlib.sha256).digest()
        )
        headers = {}
        headers["X-TransferTo-apikey"] = self.apikey
        headers["X-TransferTo-nonce"] = str(nonce)
        headers["x-transferto-hmac"] = hmac
        try:
            response = requests.post(url, headers=headers, json=self.fixed_recharge)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print("URL error")
        except requests.exceptions.Timeout:
            print("timeout error")
        except requests.exceptions.RequestException as e:
            print("catastrophics")

        return (response)

    def request_airtime_api(self, url):
        """
        This function forms the basis of using the transferTo airtime API
        """
        payload_action = self.payload_action
        key = str(int(1000 * time.time()))
        md5 = hashlib.md5()
        md5.update(payload_action["login"].encode("UTF-8"))
        md5.update(payload_action["token"].encode("UTF-8"))
        md5.update(key.encode("UTF-8"))
        payload_action.update({"key": key, "md5": md5.hexdigest()})
        response = requests.post(url, data=payload_action)
        return (response)

    def get_msisdn_products(self):
        """
        This function will
        1. Find the network provider of an MSISDN
        2. Return available products associated with that MSISDN
        3. Update the object with these products
        """
        self.payload_action = {
            "login": self.login,
            "token": self.token,
            "action": "msisdn_info",
            "destination_msisdn": self.phone,
        }

        msisdn_info = self.request_airtime_api(self.airtime_url)
        msisdn_info_json = self.jsonify_airtime_api_response(msisdn_info.content)
        operator_id = msisdn_info_json["operatorid"]
        country_id = msisdn_info_json["countryid"]
        url = self.products_url + "/countries/" + country_id + "/services"
        services = self.get_transferto_goods(url)
        url = self.products_url + "/operators/" + operator_id + "/products"
        products = self.get_transferto_goods(url)
        # return a dictionary using json.loads
        # products_json = json.loads(products.content.decode('utf8'))
        type_of_recharge = "fixed_value_recharges"
        self.products = products.json()

        return (products.json())

    def get_product_id(self):
        """
        This function will
        1. Iterate over a dictionary of possible products
        2. Return a product that contains a specific string defined in
        recharge_val
        """
        product_dict = self.products
        recharge_val = self.value
        for product in product_dict["fixed_value_recharges"]:
            product_name = product["product_short_desc"]
            print(product_name)
            if recharge_val in product_name:
                break

        self.product_id = product["product_id"]
        return (product["product_id"])

    def jsonify_airtime_api_response(self, transferto_content):
        """
        This function will return a json string of the airtime API
        It isn't pretty but it works.
        """
        stt = transferto_content.decode("utf8").replace("\r\n", '" , "').replace(
            "=", '" : "'
        )
        stt2 = '"' + stt
        stt3 = "{" + stt2.rstrip(', ,"') + '"' + "}"
        return (ast.literal_eval(stt3))

    def ping(self):
        """
        Implementation of the ping functionality to check that the API
        is actually up.
        """
        key = str(int(1000 * time.time()))
        md5 = hashlib.md5()
        md5.update(self.login.encode("UTF-8"))
        md5.update(self.token.encode("UTF-8"))
        md5.update(key.encode("UTF-8"))
        string = self.url_login + "=" + self.login + "&key=" + key + "&md5=" + md5.hexdigest() + "&action=ping"
        response = requests.get(string)
        return (response)
