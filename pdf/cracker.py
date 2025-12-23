import itertools
import pikepdf
from tqdm import tqdm
import string
from concurrent.futures import ThreadPoolExecutor
import argparse
import sys

def generate_passwords(chars, min_length, max_length):
    for length in range(min_length, max_length + 1):
        for password in itertools.product(chars, repeat=length):
            yield ''.join(password)

def load_wordlist(wordlist_file):
    with open(wordlist_file, 'r', encoding='utf-8', errors='ignore') as file:
        for line in file:
            yield line.strip()

def try_password(pdf_file, password):
    try:
        with pikepdf.open(pdf_file, password=password) as pdf:
            return password
    except (pikepdf.PasswordError, pikepdf._core.PasswordError):
        return None
    except Exception:
        return None

def decrypt_pdf(pdf_file, passwords, total_passwords, max_workers=4):
    # Kita menggunakan list agar bisa memproses secara paralel dengan benar
    with tqdm(total=total_passwords, desc='Decrypting PDF', unit='password') as pbar:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Mengirim semua tugas ke thread pool
            futures = [executor.submit(try_password, pdf_file, pwd) for pwd in passwords]

            for future in futures:
                found_password = future.result()
                if found_password:
                    pbar.close()
                    print(f'\n[+] Password found: {found_password}')
                    return found_password
                pbar.update(1)
    
    print('\n[-] Unable to decrypt PDF. Password not found.')
    return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Decrypt a password-protected PDF file.')
    parser.add_argument('pdf_file', help='Path to the password-protected PDF file.')
    parser.add_argument('-w', '--wordlist', help='Path to the passwords list file.', default=None)
    parser.add_argument('-g', '--generate', action='store_true', help='Generate passwords on the fly.')
    parser.add_argument('-min', '--min-length', type=int, help='Minimum length.', default=1)
    parser.add_argument('-max', '--max-length', type=int, help='Maximum length.', default=3)
    parser.add_argument('-c', '--charset', type=str, help='Characters for generation', default=string.ascii_letters + string.digits)
    parser.add_argument('--max_workers', type=int, help='Maximum parallel threads', default=4)

    args = parser.parse_args()

    passwords_list = []
    
    if args.generate:
        # Kita ubah generator menjadi list agar bisa menghitung 'total'
        passwords_list = list(generate_passwords(args.charset, args.min_length, args.max_length))
    elif args.wordlist:
        passwords_list = list(load_wordlist(args.wordlist))
    else:
        print("Error: Gunakan flag -w [wordlist] atau -g [generate].")
        sys.exit(1)

    total = len(passwords_list)
    decrypted_password = decrypt_pdf(args.pdf_file, passwords_list, total, args.max_workers)

    if decrypted_password:
        print(f"Final Result: Success! Password is: {decrypted_password}")
    else:
        print("Final Result: Failed to find password.")