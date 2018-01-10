from Crypto.Cipher import AES
import base64
import string
import random

def genpass(num):
	return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(num))

def encrypt(string, key):
	cipher = AES.new(key,AES.MODE_ECB)
	return base64.b64encode(cipher.encrypt(string.rjust(32)))

def decrypt(string, key):
	cipher = AES.new(key,AES.MODE_ECB)
	passout = cipher.decrypt(base64.b64decode(string))
	return passout.strip()
