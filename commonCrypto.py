# based off https://gist.github.com/syedrakib/241b68f5aeaefd7ef8e2
# PyCrypto is no longer maintained, needs pip install pycryptodome
# https://pycryptodome.readthedocs.io/en/latest/src/examples.html for AES encryption and decryption

from Crypto import Random
from Crypto.Random import get_random_bytes
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Cipher import AES

def generate_keys_RSA():
	# RSA modulus length must be a multiple of 256 and >= 1024
	modulus_length = 2048 # use larger value in production
	privatekey = RSA.generate(modulus_length, Random.new().read)
	publickey = privatekey.publickey()
	return privatekey, publickey

def encrypt_message_RSA(a_message , publickey):
	encryptor = PKCS1_OAEP.new(publickey)
	encrypted_msg = encryptor.encrypt(a_message.encode("utf-8"))
	return encrypted_msg

def decrypt_message_RSA(encrypted_msg, privatekey):
	decryptor = PKCS1_OAEP.new(privatekey)
	decrypted_msg = decryptor.decrypt(encrypted_msg)
	return decrypted_msg.decode("utf-8")

def generate_key_AES():
	key = get_random_bytes(16)
	return key

def encrypt_message_AES(a_message, key):
	encryptor = AES.new(key, AES.MODE_EAX)
	cipherText, tag = encryptor.encrypt_and_digest(a_message.encode("utf-8"))
	return cipherText, tag, encryptor.nonce
	
def decrypt_message_AES(encrypted_msg, key, nonce, tag):
	try:
		decryptor = AES.new(key, AES.MODE_EAX, nonce)
		decrypted_msg = decryptor.decrypt_and_verify(encrypted_msg, tag)
		return decrypted_msg.decode("utf-8")
	except ValueError:
		return None
	return None


# ########## Testing ##########

# a_message = "The quick brown fox jumped over the lazy dog"

# # RSA
# privatekey , publickey = generate_keys_RSA()
# encrypted_msg = encrypt_message_RSA(a_message , publickey)
# decrypted_msg = decrypt_message_RSA(encrypted_msg, privatekey)

# print("%s - (%d)" % (privatekey.exportKey() , len(privatekey.exportKey())))
# print( "%s - (%d)" % (publickey.exportKey() , len(publickey.exportKey())))
# print( " Original content: %s - (%d)" % (a_message, len(a_message)))
# print( "Encrypted message: %s - (%d)" % (encrypted_msg, len(encrypted_msg)))
# print( "Decrypted message: %s - (%d)" % (decrypted_msg, len(decrypted_msg)))

# # AES
# aesKey = generate_key_AES()
# encrypted_msg, tag, nonce = encrypt_message_AES(a_message , aesKey)
# decrypted_msg = decrypt_message_AES(encrypted_msg , aesKey, nonce, tag)

# # test tampering of message!
# encrypted_msg_tampered = encrypted_msg + b'aa'
# tampered_message = decrypt_message_AES(encrypted_msg_tampered , aesKey, nonce, tag)


# print("%s - (%d)" % (aesKey , len(aesKey)))
# print( "Encrypted message: %s - (%d)" % (encrypted_msg, len(encrypted_msg)))
# print( "tag: %s - (%d)" % (tag, len(tag)))
# print( "nonce: %s - (%d)" % (nonce, len(nonce)))
# print( "Decrypted message: %s - (%d)" % (decrypted_msg, len(decrypted_msg)))

# if tampered_message is not None:
# 	print( "tampered message: %s - (%d)" % (tampered_message, len(tampered_message)))
# else:
# 	print("Someone tampered with our tampered message!")
