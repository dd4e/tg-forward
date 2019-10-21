"""Token module"""

import base64
import os
from functools import lru_cache
from logging import getLogger
from typing import Tuple

import rsa
from rsa import PrivateKey, PublicKey


class Token:
    logger = getLogger("tg-fwd")

    def __init__(self, pub_key_path: str, priv_key_path: str, salt: int, rsa_nbits: int = 512):
        self.__pub_key_path = pub_key_path
        self.__priv_key_path = priv_key_path
        self.__salt = salt
        try:
            self.logger.info("Trying to load RSA keys")
            self.__pub_key, self.__priv_key = self._load_rsa_keys()
            self.logger.info("RSA keys successfully loaded!")
        except OSError as err:
            self.logger.warning("Unable to load RSA keys")
            self.logger.debug(err)
            self.__pub_key, self.__priv_key = self._generate_rsa_keys(rsa_nbits)
            self._save_rsa_keys()
            self.logger.info("RSA keys successfully initialized!")

    @classmethod
    def _generate_rsa_keys(cls, nbits: int) -> Tuple[PublicKey, PrivateKey]:
        cls.logger.debug("Generate RSA key with %i bits", nbits)
        return rsa.newkeys(nbits)

    def _load_rsa_keys(self) -> Tuple[PublicKey, PrivateKey]:
        """Load RSA keys from filesystem"""
        self.logger.debug("Load public key from %s", self.__pub_key_path)
        with open(self.__pub_key_path, "rb") as pem_file:
            pub_key_data = pem_file.read()
        self.logger.debug("RSA public key loaded")

        self.logger.debug("Load private key from %s", self.__priv_key_path)
        with open(self.__priv_key_path, "rb") as pem_file:
            priv_key_data = pem_file.read()
        self.logger.debug("RSA private key loaded")

        return PublicKey.load_pkcs1(pub_key_data), PrivateKey.load_pkcs1(priv_key_data)

    def _save_rsa_keys(self):
        """Save RSA keys to file system"""
        self.logger.debug("Save RSA keys to file system")
        for path, key in [(self.__pub_key_path, self.__pub_key), (self.__priv_key_path, self.__priv_key)]:
            with open(path, "wb") as pem_file:
                pem_file.write(key.save_pkcs1())
            self.logger.debug("Key successfully saved to %s", path)
            os.chmod(path, 0o400)
        self.logger.debug("RSA keys successfully saved")

    @lru_cache(maxsize=1000)
    def to_token(self, tid: int) -> str:
        token = rsa.encrypt(str(tid + self.__salt).encode(), self.__pub_key)
        return base64.b64encode(token).decode()

    @lru_cache(maxsize=1000)
    def to_tid(self, token: str) -> int:
        open_msg = rsa.decrypt(base64.b64decode(token), self.__priv_key)
        return int(open_msg) - self.__salt
