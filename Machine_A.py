from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
import base64
import os

KEY_DIR = "./key"
PRIVATE_KEY_FILE = os.path.join(KEY_DIR, "private_key.pem")
PUBLIC_KEY_FILE = os.path.join(KEY_DIR, "public_key.pem")

def generate_keys():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    os.makedirs(KEY_DIR, exist_ok=True)

    # Save private key securely (Machine A only)
    with open(PRIVATE_KEY_FILE, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

    # Save public key for sharing
    with open(PUBLIC_KEY_FILE, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

    print(f"\n[✔] Keys generated and saved in '{KEY_DIR}/' folder.\n")
    print(f"[🔑] Share '{PUBLIC_KEY_FILE}' with Machine B.\n")

    return private_key, public_key

def load_private_key():
    with open(PRIVATE_KEY_FILE, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def decrypt_message(ciphertext, private_key):
    with Progress(SpinnerColumn(), TextColumn("Decrypting..."), BarColumn(), transient=True) as progress:
        task = progress.add_task("Decrypting", total=1)
        decrypted_text = private_key.decrypt(
            base64.b64decode(ciphertext),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        progress.update(task, advance=1)
    return decrypted_text.decode()

def main():
    #print("\n[RSA Chat Decryption Tool - Machine A]")
    if not os.path.exists(PRIVATE_KEY_FILE):
        generate_keys()
'''
    private_key = load_private_key()

    while True:
        ciphertext = input()
        try:
            decrypted = decrypt_message(ciphertext, private_key)
            print(f"\n[🔓] Decrypted Message: {decrypted}\n")

        except Exception:
            print("\n[❌] Decryption failed! Invalid input or wrong key.\n")
'''
if __name__ == "__main__":
    main()
