# based off https://gist.github.com/syedrakib/241b68f5aeaefd7ef8e2

# Inspired from http://coding4streetcred.com/blog/post/Asymmetric-Encryption-Revisited-(in-PyCrypto)
# PyCrypto docs available at https://www.dlitz.net/software/pycrypto/api/2.6/

from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64

def generate_keys():
	# RSA modulus length must be a multiple of 256 and >= 1024
	modulus_length = 2048 # use larger value in production
	privatekey = RSA.generate(modulus_length, Random.new().read)
	publickey = privatekey.publickey()
	return privatekey, publickey

def encrypt_message(a_message , publickey):
	encryptor = PKCS1_OAEP.new(publickey)
	encrypted_msg = encryptor.encrypt(a_message.encode("utf-8"))
	return encrypted_msg

def decrypt_message(encrypted_msg, privatekey):
	decryptor = PKCS1_OAEP.new(privatekey)
	decrypted_msg = decryptor.decrypt(encrypted_msg)
	return decrypted_msg.decode("utf-8")

########## BEGIN ##########

a_message = "The quick brown fox jumped over the lazy dog"
privatekey , publickey = generate_keys()
encrypted_msg = encrypt_message(a_message , publickey)
decrypted_msg = decrypt_message(encrypted_msg, privatekey)

print("%s - (%d)" % (privatekey.exportKey() , len(privatekey.exportKey())))
print( "%s - (%d)" % (publickey.exportKey() , len(publickey.exportKey())))
print( " Original content: %s - (%d)" % (a_message, len(a_message)))
print( "Encrypted message: %s - (%d)" % (encrypted_msg, len(encrypted_msg)))
print( "Decrypted message: %s - (%d)" % (decrypted_msg, len(decrypted_msg)))