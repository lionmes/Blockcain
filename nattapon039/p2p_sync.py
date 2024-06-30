import socket # นำเข้าโมดูล socket สำหรับการสร้างและใช้งาน sockets สำหรับการเชื่อมต่อแบบ TCP/IP
import threading # นำเข้าโมดูล threading สำหรับการจัดการกับ threads เพื่อให้โปรแกรมทำงานพร้อมกันได้
import json # นำเข้าโมดูล json สำหรับการทำงานกับ JSON (JavaScript Object Notation) ในการส่งข้อมูลระหว่างโหนด
import sys # นำเข้าโมดูล sys สำหรับการจัดการกับพารามิเตอร์และคำสั่งที่เข้ามาจาก command line
import os # นำเข้าโมดูล os สำหรับการทำงานระดับระบบปฏิบัติการ เช่น การจัดการไฟล์
import secrets # นำเข้าโมดูล secrets สำหรับการสร้างข้อมูลลับอย่างปลอดภัย เช่น การสร้าง wallet address

class Node: # นิยามคลาส Node ซึ่งเป็นโหนดในเครือข่าย blockchain
    def __init__(self, host, port): # เมธอด __init__ ในการสร้างอ็อบเจกต์ของคลาส Node ด้วยพารามิเตอร์ host และ port
        self.host = host # กำหนด host สำหรับโหนด
        self.port = port # กำหนด port สำหรับโหนด
        self.peers = []  # เก็บรายการ socket ของ peer ที่เชื่อมต่อ
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # สร้าง socket แบบ TCP
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # ตั้งค่า socket ให้ reuse address ได้
        self.transactions = []  # เก็บรายการ transactions ที่โหนดนี้ได้รับหรือสร้าง
        self.transaction_file = f"transactions_{port}.json"  # ชื่อไฟล์ที่ใช้บันทึก transactions ของโหนดนี้
        self.wallet_address = self.generate_wallet_address()  # สร้าง wallet address สำหรับโหนดนี้โดยใช้เมธอด generate_wallet_address

    def generate_wallet_address(self): # เมธอดสร้าง wallet address สำหรับโหนด.
        return '0x' + secrets.token_hex(20) # สร้าง wallet address แบบง่ายๆ โดยใช้ secrets.token_hex(20) เพื่อสร้างข้อมูลลับที่มีความปลอดภัย

    def start(self): # เริ่มต้นการทำงานของโหนดด้วยเมธอด start
        self.socket.bind((self.host, self.port)) # ผูก socket กับ host และ port ที่กำหนด
        self.socket.listen(1) # เปิดการรอการเชื่อมต่อแบบ listening mode โดยรอของมาจาก client ได้ 1 ครั้ง
        print(f"Node listening on {self.host}:{self.port}") # แสดงข้อความบอกว่าโหนดได้เริ่มต้นการทำงานแล้วและกำลังรอการเชื่อมต่อที่ {self.host}:{self.port}
        print(f"Your wallet address is: {self.wallet_address}") # แสดง wallet address ของโหนดนี้

        self.load_transactions()  # โหลด transactions จากไฟล์ที่เก็บ (ถ้ามีอยู่)

        # เริ่ม thread สำหรับรับการเชื่อมต่อใหม่
        accept_thread = threading.Thread(target=self.accept_connections) # สร้าง thread สำหรับรับการเชื่อมต่อใหม่โดยใช้เมธอด accept_connections
        accept_thread.start() # เริ่ม thread เพื่อทำการรับการเชื่อมต่อใหม่

    def accept_connections(self): # รับการเชื่อมต่อที่เข้ามา
        while True: # วนลูปตลอดเวลา
            # รอรับการเชื่อมต่อใหม่
            client_socket, address = self.socket.accept() # รอรับการเชื่อมต่อใหม่จาก client และรับ socket และที่อยู่ของ client
            print(f"New connection from {address}") # แสดงข้อความบอกว่ามีการเชื่อมต่อใหม่เข้ามาจาก address

            # เริ่ม thread ใหม่สำหรับจัดการการเชื่อมต่อนี้
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,)) # สร้าง thread ใหม่สำหรับจัดการการเชื่อมต่อนี้โดยใช้เมธอด handle_client
            client_thread.start() # เริ่ม thread เพื่อทำการจัดการการเชื่อมต่อนี้

    def handle_client(self, client_socket): # จัดการการเชื่อมต่อกับ client ด้วยเมธอด handle_client
        while True: # วนลูปตลอดเวลา
            try:
                # รับข้อมูลจาก client
                data = client_socket.recv(1024) # รับข้อมูลจาก client ขนาดไม่เกิน 1024 bytes
                if not data: # ถ้าไม่มีข้อมูลให้หยุดลูป
                    break 
                message = json.loads(data.decode('utf-8')) # แปลงข้อมูลที่รับมาเป็น JSON
                
                self.process_message(message, client_socket) # ส่งข้อมูลที่ได้รับไปยังเมธอด process_message เพื่อประมวลผล

            except Exception as e: # จัดการข้อผิดพลาดที่เกิดขึ้น
                print(f"Error handling client: {e}") # แสดงข้อความของ "Error handling client:" พร้อมกับแสดงข้อผิดพลาดที่เกิดขึ้น
                break # หยุดการทำงานของลูป

        client_socket.close() # ปิดการเชื่อมต่อกับ client ที่จัดการเสร็จสิ้น

    def connect_to_peer(self, peer_host, peer_port): #  เชื่อมต่อไปยัง peer ด้วยเมธอด connect_to_peer
        try:
            # สร้างการเชื่อมต่อไปยัง peer
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # สร้าง socket สำหรับการเชื่อมต่อแบบ TCP
            peer_socket.connect((peer_host, peer_port)) # เชื่อมต่อไปยัง peer ที่กำหนดด้วย peer_host และ peer_port
            self.peers.append(peer_socket) # เพิ่ม socket ของ peer ที่เชื่อมต่อไว้ใน self.peers
            print(f"Connected to peer {peer_host}:{peer_port}") # แสดงข้อความบอกว่าเชื่อมต่อไปยัง peer สำเร็จ
            self.request_sync(peer_socket) # ขอข้อมูล transactions ทั้งหมดจาก peer ที่เชื่อมต่อด้วยเมธอด request_sync
            peer_thread = threading.Thread(target=self.handle_client, args=(peer_socket,)) # สร้าง thread สำหรับรับข้อมูลจาก peer นี้โดยใช้เมธอด handle_client
            peer_thread.start() # เริ่ม thread เพื่อรับข้อมูลจาก peer

        except Exception as e: # จัดการข้อผิดพลาดที่เกิดขึ้น
            print(f"Error connecting to peer: {e}") # แสดงข้อความของ "Error connecting to peer:" พร้อมกับแสดงข้อผิดพลาดที่เกิดขึ้น

    def broadcast(self, message): # ส่งข้อมูลไปยังทุก peer ที่เชื่อมต่อด้วยเมธอด broadcast
        for peer_socket in self.peers: # วนลูปผ่านทุก socket ของ peer ที่เชื่อมต่ออยู่ใน self.peers
            try:
                peer_socket.send(json.dumps(message).encode('utf-8')) # ส่งข้อมูลที่ถูกแปลงเป็น JSON ไปยังทุก peer
            except Exception as e: # จัดการข้อผิดพลาดที่เกิดขึ้นในกรณีที่ส่งข้อมูลไม่ได้
                print(f"Error broadcasting to peer: {e}")
                self.peers.remove(peer_socket) # ลบ socket ของ peer ที่เกิดข้อผิดพลาดออกจาก self.peers

    def process_message(self, message, client_socket): # ประมวลผลข้อความที่ได้รับด้วยเมธอด process_message
        if message['type'] == 'transaction': # ถ้าชนิดของข้อความเป็น 'transaction' ให้ทำการประมวลผล transaction
            print(f"Received transaction: {message['data']}") # แสดงข้อความบอกว่าได้รับ transaction
            self.add_transaction(message['data']) # เพิ่ม transaction ลงในโหนดด้วยเมธอด add_transaction
        elif message['type'] == 'sync_request': #ถ้าชนิดของข้อความเป็น 'sync_request' ให้ส่ง transactions ทั้งหมดไปยัง client ที่ขอด้วยเมธอด send_all_transactions
            self.send_all_transactions(client_socket)
        elif message['type'] == 'sync_response': # ถ้าชนิดของข้อความเป็น 'sync_response' ให้รับข้อมูล transactions จาก peer ที่มากับข้อความด้วยเมธอด receive_sync_data
            self.receive_sync_data(message['data'])
        else: # ในกรณีอื่นที่ไม่ตรงกับเงื่อนไขข้างบน
            print(f"Received message: {message}") # แสดงข้อความบอกว่าได้รับข้อความ

    def add_transaction(self, transaction): # เพิ่ม transaction ใหม่ด้วยเมธอด add_transaction และบันทึกลงไฟล์
        if transaction not in self.transactions: # ถ้า transaction ยังไม่มีอยู่ใน self.transactions
            self.transactions.append(transaction) #เพิ่ม transaction เข้าไปใน self.transactions
            self.save_transactions() # บันทึก transactions ลงในไฟล์ด้วยเมธอด save_transactions
            print(f"Transaction added and saved: {transaction}") # แสดงข้อความบอกว่า transaction ถูกเพิ่มและบันทึกลงไฟล์

    def create_transaction(self, recipient, amount): # สร้าง transaction ใหม่ด้วยเมธอด create_transaction
        transaction = { # สร้าง transaction object ใหม่
            'sender': self.wallet_address, # wallet address ของโหนด
            'recipient': recipient, # ที่อยู่ wallet ของผู้รับ
            'amount': amount # จำนวนเงินที่จะส่ง
        }
        self.add_transaction(transaction) # เพิ่ม transaction ลงในโหนดด้วยเมธอด add_transaction
        self.broadcast({'type': 'transaction', 'data': transaction}) # ส่ง transaction ไปยังทุกๆ peer ที่เชื่อมต่อด้วยเมธอด broadcast

    def save_transactions(self): # บันทึก transactions ลงในไฟล์ด้วยเมธอด save_transactions
        with open(self.transaction_file, 'w') as f: # เปิดไฟล์เพื่อเขียน ('w') และใช้ชื่อไฟล์ self.transaction_file
            json.dump(self.transactions, f) # เขียน transactions ลงในไฟล์ JSON

    def load_transactions(self): # โหลด transactions จากไฟล์ด้วยเมธอด load_transactions
        if os.path.exists(self.transaction_file): # ถ้ามีไฟล์ transactions อยู่ในระบบ
            with open(self.transaction_file, 'r') as f: # เปิดไฟล์เพื่ออ่าน ('r') และใช้ชื่อไฟล์ self.transaction_file
                self.transactions = json.load(f) # โหลด transactions จากไฟล์ JSON และเก็บลงใน self.transactions
            print(f"Loaded {len(self.transactions)} transactions from file.") # แสดงข้อความบอกว่าโหลด transactions จากไฟล์สำเร็จ

    def request_sync(self, peer_socket): # ขอข้อมูลการซิงโครไนซ์กับ peer ด้วยเมธอด request_sync
        sync_request = json.dumps({"type": "sync_request"}).encode('utf-8') # แปลงข้อความเป็น JSON และ encode ให้อยู่ในรูปแบบ bytes
        peer_socket.send(sync_request) # ส่งข้อมูลการซิงโครไนซ์ไปยัง peer

    def send_all_transactions(self, client_socket): # ส่งข้อมูล transactions ทั้งหมดไปยังโหนดที่ขอซิงโครไนซ์ด้วยเมธอด send_all_transactions
        sync_data = json.dumps({ # ใช้เพื่อแปลง Python dictionary ที่มีข้อมูล transactions 
            "type": "sync_response",
            "data": self.transactions
        }).encode('utf-8') # แปลง JSON string เป็น bytes โดยใช้ UTF-8 encoding เพื่อให้ข้อมูลสามารถส่งผ่าน socket ไปยังโหนดอื่นได้
        client_socket.send(sync_data) # ส่งข้อมูลซิงโครไนซ์ไปยัง client ที่ขอซิงโครไนซ์

    def receive_sync_data(self, sync_transactions): # รับและประมวลผลข้อมูล transactions ที่ได้รับจากการซิงโครไนซ์ด้วยเมธอด receive_sync_data
        for tx in sync_transactions: # วนลูปผ่าน transactions ที่ได้รับมาจากฝั่งอื่น
            self.add_transaction(tx) # เพิ่ม transaction นี้เข้าไปในโหนดด้วยเมธอด add_transaction
        print(f"Synchronized {len(sync_transactions)} transactions.") # แสดงข้อความบอกว่าทำการซิงโครไนซ์ transactions เรียบร้อย

if __name__ == "__main__": # เช็คว่าไฟล์ถูก run โดยตรงหรือไม่
    if len(sys.argv) != 2: # ถ้าจำนวน argument ไม่เท่ากับ 2 (โดยที่ 0 คือชื่อไฟล์, 1 คือ port) ให้แสดงข้อความและออกจากโปรแกรม
        print("Usage: python script.py <port>")
        sys.exit(1)
      
    port = int(sys.argv[1]) # นำ port จาก command line argument แล้วแปลงเป็น integer
    node = Node("0.0.0.0", port)  # สร้าง object ของคลาส Node ด้วย host เป็น "0.0.0.0" และ port จาก command line argument
    node.start() # เริ่มเว็บเซิร์ฟเวอร์ของโหนด
    
    while True: # loop ที่รันตลอดเพื่อให้ผู้ใช้ทำการเลือกทำรายการตามที่ต้องการจนกว่าจะพิมพ์ '5' เพื่อออกจากโปรแกรม
        print("\n1. Connect to a peer") # แสดงตัวเลือก "Connect to a peer"
        print("2. Create a transaction") # แสดงตัวเลือก "Create a transaction"
        print("3. View all transactions") # แสดงตัวเลือก "View all transactions"
        print("4. View my wallet address") # แสดงตัวเลือก "View my wallet address"
        print("5. Exit") # แสดงตัวเลือก "Exit"
        choice = input("Enter your choice: ") # รับค่า input จากผู้ใช้เพื่อเลือกทำรายการ
        
        if choice == '1': # ถ้าผู้ใช้เลือก '1' (เชื่อมต่อกับ peer)
            peer_host = input("Enter peer host to connect: ") # รับ host ของ peer ที่ผู้ใช้ต้องการเชื่อมต่อ
            peer_port = int(input("Enter peer port to connect: ")) # รับ port ของ peer ที่ผู้ใช้ต้องการเชื่อมต่อและแปลงเป็น integer
            node.connect_to_peer(peer_host, peer_port) # เรียกใช้เมธอด connect_to_peer ของ node เพื่อเชื่อมต่อกับ peer ที่ระบุ
        elif choice == '2': # ถ้าผู้ใช้เลือก '2' (สร้าง transaction)
            recipient = input("Enter recipient wallet address: ") # รับที่อยู่ wallet ของผู้รับที่ผู้ใช้ต้องการส่งเงิน
            amount = float(input("Enter amount: ")) # รับจำนวนเงินที่ผู้ใช้ต้องการส่งและแปลงเป็น float
            node.create_transaction(recipient, amount) # เรียกใช้เมธอด create_transaction ของ node เพื่อสร้าง transaction และส่งไปยัง peer ที่เชื่อมต่ออยู่
        elif choice == '3': # ถ้าผู้ใช้เลือก '3' (ดู transactions ทั้งหมด)
            print("All transactions:") # แสดงข้อความบอกว่าจะแสดง transactions ทั้งหมด
            for tx in node.transactions: # วนลูปทุก transaction ใน node.transactions
                print(tx) # แสดงข้อมูล transaction แต่ละตัว
        elif choice == '4': # ถ้าผู้ใช้เลือก '4' (ดู wallet address ของตัวเอง)
            print(f"Your wallet address is: {node.wallet_address}") # แสดง wallet address ของโหนดนี้
        elif choice == '5': # ถ้าผู้ใช้เลือก '5' (ออกจากโปรแกรม)
            break # หยุดการทำงานของ loop while True และออกจากโปรแกรม
        else: # ถ้าผู้ใช้เลือกตัวเลือกอื่นที่ไม่ถูกต้อง
            print("Invalid choice. Please try again.") # แสดงข้อความบอกว่าเลือกไม่ถูกต้องและให้ผู้ใช้ลองใหม่

    print("Exiting...") # แสดงข้อความ "Exiting..." เมื่อโปรแกรมถูกปิดออกด้วยตัวเลือก '5' ด้วยคำสั่ง print("Exiting...").