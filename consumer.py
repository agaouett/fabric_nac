import multiprocessing
import time
import pwn
import sys
import base64

pwn.context.log_level = "WARN"

def publish_public_key(pub_key_path: str, pub_key_namespace: str, face_id: str):
    interest_cmd = f"ndndpdk-ctrl insert-fib --name {pub_key_namespace} --nh {face_id}".split()
    with pwn.process(interest_cmd) as interest:
        print(f"Adding entry for {pub_key_namespace} to FIB on face {face_id}.")

    publish_cmd = f'ndndpdk-godemo --mtu 1500 put --name {pub_key_namespace} --file {pub_key_path} --chunk-size 4096'.split()
    with pwn.process(publish_cmd) as host:
        try:
            print(f"Publishing public key found at {pub_key_path} to namespace {pub_key_namespace}.\n")
            host.recvall()
        except KeyboardInterrupt:
            host.kill()
        

def get_content(content_name: str, face_id: str):
    ndnping_cmd = f"ndndpdk-godemo pingclient --name {content_name} --interval 250ms --lifetime 1000ms".split()

    with pwn.process(ndnping_cmd) as ping:
        # Uplink Opened
        line = ping.recvline().decode().strip('\n')
        print(line)
        # Uplink state changes to up
        line = ping.recvline().decode().strip('\n')
        print(line)
        print(f"Awaiting response to interest from server...\n")
        # Monitor for changes
        line = ping.recvline().decode().strip('\n')
        while "expired" in line: # Wait until we see something other than expired interest packets
            line = ping.recvline().decode().strip()
            print(line)
        if "us" in line: # Looking for microsecond timestamp
            print("Interest packet reply received.")

    time.sleep(1)

    interest_cmd = f"ndndpdk-ctrl insert-fib --name {content_name}.enc --nh {face_id}".split()
    with pwn.process(interest_cmd) as interest:
        print(f"Adding entry for {content_name}.enc to FIB on face {face_id}.\n")
        interest.recvall()

    save_loc = "/home/ubuntu/alice/downloads/may04.enc"
    get_cmd = f"ndndpdk-godemo --mtu 1500 get --name {content_name}.enc".split()
    with pwn.process(get_cmd) as get:
        dl_log = []
        print("Attempting to download file.")
        line = get.recvline().decode()
        dl_log.append(line)
        while "uplink closed" not in line:
            line = get.recvline().decode()
            dl_log.append(line)
        print(f"File retrieved. Saving to {save_loc}...")

    # Extract payload from received download log
    encrypted = []
    for line in dl_log:
        print(line)
        if "uplink" in line or "segments" in line:
            pass
        else:
            encrypted.append(line)
    
    with open(save_loc, 'w') as fout:
        for line in encrypted:
            fout.write(line)
    print("Encrypted file saved.\n")
    print("Getting content key...")

    c_key_namespace = "/bob/blog/c_key_for_alice"
    interest_cmd = f"ndndpdk-ctrl insert-fib --name {c_key_namespace} --nh {face_id}".split()
    print(f"Adding entry for {c_key_namespace} to FIB on face {face_id}.\n")
    with pwn.process(interest_cmd) as interest:
        interest.recvline()

    c_key_loc = "/home/ubuntu/alice/downloads/c_key_for_alice"
    get_cmd = f"ndndpdk-godemo --mtu 1500 get --name {c_key_namespace}".split()
    with pwn.process(get_cmd) as get:
        dl_log = []
        print("Attempting to download content key.")
        line = get.recvline().decode()
        dl_log.append(line)
        while "uplink closed" not in line:
            line = get.recvline().decode()
            dl_log.append(line)
        print(f"File retrieved. Saving to {c_key_loc}...")

        c_key_b64 = b''
        for line in dl_log:
            if "uplink" in line or "segments" in line:
                pass
            else:
                # Save as raw bytes
                c_key_b64 = line.encode().strip(b'\n')
        c_key = base64.b64decode(c_key_b64, altchars=None)
    
    with open(c_key_loc, 'wb') as key_file:
        key_file.write(c_key)
    print("File saved.")

    print("Decrypting content key with private key.")
    priv_key = "/home/ubuntu/alice/access/alice_key"
    dec_key = "/home/ubuntu/alice/downloads/c_key"
    decrypt_key_cmd = f"openssl rsautl -decrypt -oaep -inkey {priv_key} -in {c_key_loc} -out {dec_key}".split()
    with pwn.process(decrypt_key_cmd) as decrypt:
        result = decrypt.recvall()
    print(f"\nContent key decryption successful. Saved to {dec_key}")
    print("File and content key retrieved. Press Ctrl+C to exit.")
    sys.exit()


def main():
    # Capture face ID
    with pwn.process(['ndndpdk-ctrl', 'list-face'], ) as proc:
        print("Obtaining local face ID for Consumer Node.")
        line = proc.recvuntil(b'\"id\":\"').decode().strip('\n')
        face_id = proc.recvuntil(b'\"').decode().strip("\"")
        print(f'Face ID: {face_id}\n')

    pub_key_path = '/home/ubuntu/alice/access/alice_key.pub'
    pub_key_namespace = "/alice/access/alice_key.pub"
    content_name = "/bob/blog/may04"

    interest_cmd = f"ndndpdk-ctrl insert-fib --name {content_name} --nh {face_id}".split()
    with pwn.process(interest_cmd) as interest:
        print(f"Adding entry for {content_name} to FIB on face {face_id}.")
        interest.recvall()

    try:
        p1 = multiprocessing.Process(target=publish_public_key, args=(pub_key_path, pub_key_namespace, face_id))
        p2 = multiprocessing.Process(target=get_content, args=(content_name, face_id))

        p1.start()
        time.sleep(1)
        p2.start()

        p1.join()
        p2.join()
    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Exiting program.")
        p1.terminate()
        p2.terminate()
        sys.exit()

if __name__ == "__main__":
    main()