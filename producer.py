import multiprocessing
import time
import pwn
import sys
import base64

pwn.context.log_level = "WARN"

c_key_loc = "/home/ubuntu/bob/blog/c_key"

# Makes a file available to consumer
def host_file(namespace: str, file_loc: str, face_id: str):
    interest_cmd = f"ndndpdk-ctrl insert-fib --name {namespace} --nh {face_id}".split()
    with pwn.process(interest_cmd) as interest:
        print(f"Adding entry for {namespace} to FIB on face {face_id}.")

    host_cmd = f"ndndpdk-godemo --mtu 1500 put --name {namespace} --file {file_loc} --chunk-size 4096".split()
    with pwn.process(host_cmd) as host:
        try:
            print(f"Publishing file {file_loc} to server as {namespace}.\n")
            host.recvall()
        except KeyboardInterrupt:
            host.kill()

# Monitors interest packets. 
# Once interest is determined, retrieves consumer's public key then encrypts
# content key with consumer's public key
def monitor_interests(namespace: str, face_id: str, surpress: bool):
    monitor_cmd = f"ndndpdk-godemo pingserver --name {namespace}".split()
    with pwn.process(monitor_cmd) as interests:
        if not surpress:
            print(f"Monitoring for incoming interest packets for {namespace}.")
            # Uplink Opened
            line = interests.recvline().decode().strip('\n')
            print(line)
            # Uplink state changes to up
            line = interests.recvline().decode().strip('\n')
            print(line)
            # Monitor for interests
            line = interests.recvline().decode().strip('\n')
            print(line)
            print("Interest packet received.")
            interests.recvall(1) # Flush remaining responses

    # Add entry to FIB to get consumer public key
    pub_key_namespace = "/alice/access/alice_key.pub"
    interest_cmd = f"ndndpdk-ctrl insert-fib --name {pub_key_namespace} --nh {face_id}".split()
    with pwn.process(interest_cmd) as interest:
        interest.recvline()

    get_cmd = f"ndndpdk-godemo --mtu 1500 get --name {pub_key_namespace}".split()
    with pwn.process(get_cmd) as get:
        dl_log = []
        print("Retrieving public key for user.")
        line = get.recvline().decode()
        dl_log.append(line)
        while "uplink closed" not in line:
            line = get.recvline().decode()
            dl_log.append(line)

    print(f"Key retrieved. Encrypting content key with user's public key...\n")

    # Extract payload from received download log
    consumer_pub = []
    for line in dl_log:
        if "uplink" in line or "segments" in line:
            pass
        else:
            # Save as raw bytes
            consumer_pub.append(line.encode())
    save_key_loc = "/home/ubuntu/bob/blog/alice_key.pub"
    with open(save_key_loc, 'wb') as fout:
        for line in consumer_pub:
            fout.write(line)

    # Encrypt content key with consumer's public key
    c_key_consumer = c_key_loc + "_for_alice"
    encrypt_cmd = f"openssl rsautl -encrypt -oaep -pubin -inkey {save_key_loc} -in {c_key_loc}".split()
    with pwn.process(encrypt_cmd) as encrypt:
        result = encrypt.recvall()
        # Convert to base64 before saving
        b64_result = base64.b64encode(result, altchars=None)
        # Save base64 output to file
        with open(c_key_consumer, 'wb') as file:
            file.write(b64_result)
            #append a newline for easier parsing
            file.write(b'\n')
    
    # Host content key for consumer
    print("Hosting content key for consumer retrieval.")
    c_key_namespace = "/bob/blog/c_key_for_alice"
    interest_cmd = f"ndndpdk-ctrl insert-fib --name {c_key_namespace} --nh {face_id}".split()
    with pwn.process(interest_cmd) as interest:
        interest.recvline()

    host_cmd = f"ndndpdk-godemo --mtu 1500 put --name {c_key_namespace} --file {c_key_consumer} --chunk-size 4096".split()
    with pwn.process(host_cmd) as host:
        try:
            print(f"Publishing file {c_key_consumer} to server as {c_key_namespace}.\n")
            host.recvall()
        except KeyboardInterrupt:
            host.kill()

def main():
    # Capture face ID
    with pwn.process(['ndndpdk-ctrl', 'list-face'], ) as proc:
        print("Obtaining local face ID for Producer Node.")
        line = proc.recvuntil(b'\"id\":\"').decode().strip('\n')
        face_id = proc.recvuntil(b'\"').decode().strip("\"")
        print(f'Face ID: {face_id}\n')

    file_loc = "/home/ubuntu/bob/blog/may04"
    file_loc_enc = file_loc + ".enc"
    namespace = "/bob/blog/may04"
    namespace_enc = namespace + ".enc"

    interest_cmd = f"ndndpdk-ctrl insert-fib --name {namespace} --nh {face_id}".split()
    with pwn.process(interest_cmd) as interest:
        print(f"Adding entry for {namespace} for discovery on {face_id}.")
        interest.recvall()

    try:
        # Host encrypted blog post
        p1 = multiprocessing.Process(target=host_file, args=(namespace_enc, file_loc_enc, face_id))
        # Monitor incoming interests for blog posts
        p2 = multiprocessing.Process(target=monitor_interests, args=(namespace, face_id, False))

        p1.start()
        time.sleep(0.1)
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