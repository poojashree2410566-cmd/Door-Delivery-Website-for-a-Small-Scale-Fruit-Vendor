# server.py
import os
import csv
import time
from flask import Flask, request, jsonify, send_from_directory
from data_structures import FruitBST, FIFOOrderQueue, UserManager, CartManager, xor_crypt

app = Flask(__name__, static_folder=".", static_url_path="")

# --- Initialize Custom Data Structures ---
fruit_bst = FruitBST()
order_queue = FIFOOrderQueue()
user_manager = UserManager()
cart_manager = CartManager()

# Default image URLs for premium aesthetics
FRUIT_IMAGES = {
    "apple": "https://static.wikia.nocookie.net/fruits-information/images/2/2b/Apple.jpg",
    "banana": "https://upload.wikimedia.org/wikipedia/commons/9/9b/Cavendish_Banana_DS.jpg",
    "orange": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR7DKgxlyCzYOP6grBXISFNNcc5D40YcORPpg&s",
    "grapes": "https://5.imimg.com/data5/XN/BA/MY-44512510/fresh-grape-500x500.jpg",
    "mango": "https://5.imimg.com/data5/TU/TO/MY-14521890/fresh-mango-250x250.jpg",
    "pineapple": "https://5.imimg.com/data5/SELLER/Default/2022/11/JU/WQ/DZ/162935399/pineapple.jpg",
    "strawberry": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRstkjwiPxbadqVjuPJuj3ntjrD0h1LjB59Mw&s",
    "papaya": "https://5.imimg.com/data5/ZQ/GV/CJ/SELLER-106350662/papaya-fruit.jpg",
    "watermelon": "https://static.wikia.nocookie.net/fruits-information/images/b/b9/Watermelon.jpg",
    "dragonfruit": "https://www.shutterstock.com/image-photo/one-whole-dragon-fruit-isolated-600nw-2296025373.jpg",
    "pomegranate": "https://st.depositphotos.com/11537288/53603/i/450/depositphotos_536039398-stock-photo-pomegranate-fruit-isolated-white-background.jpg",
    "jackfruit": "https://media.istockphoto.com/id/1411962468/photo/young-jackfruit-on-white-background.jpg?s=612x612&w=0&k=20&c=wo384rXnbm6x4qrVskdYEZxdzXpd-g3jEeXWWDr8MPI="
}

# --- File Loading Functions ---

def load_users():
    if not os.path.exists("users.txt"):
        return
    with open("users.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=2)
            if len(parts) >= 2:
                username = parts[0]
                encrypted_pwd = parts[1]
                decrypted_pwd = xor_crypt(encrypted_pwd)
                
                email_or_address = parts[2] if len(parts) > 2 else ""
                email = ""
                address = ""
                # Compatibility checks
                if "@" in email_or_address and " " not in email_or_address:
                    email = email_or_address
                elif "@" in email_or_address:
                    subparts = email_or_address.split(maxsplit=1)
                    email = subparts[0]
                    address = subparts[1]
                else:
                    address = email_or_address
                    email = f"{username}@example.com"
                
                user_manager.register(username, decrypted_pwd, email, address)

def save_users():
    with open("users.txt", "w", encoding="utf-8") as f:
        for user in user_manager.users.values():
            encrypted_pwd = xor_crypt(user["password"])
            email = user.get("email", "") or f"{user['username']}@example.com"
            address = user.get("address", "")
            f.write(f"{user['username']} {encrypted_pwd} {email} {address}\n")

def load_fruits():
    if not os.path.exists("fruits.txt"):
        return
    with open("fruits.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 4:
                name = parts[0]
                price = float(parts[1])
                stock = int(parts[2])
                unit = parts[3]
                
                desc = f"Fresh and tasty {name}."
                img = FRUIT_IMAGES.get(name.lower(), "https://via.placeholder.com/120")
                fruit_bst.insert(name, price, stock, unit, desc, img)

def save_fruits():
    fruits = fruit_bst.get_all_fruits()
    with open("fruits.txt", "w", encoding="utf-8") as f:
        for fruit in fruits:
            f.write(f"{fruit['name']} {fruit['price']:.2f} {fruit['stock']} {fruit['unit']}\n")

def load_cart():
    if not os.path.exists("cart.txt"):
        return
    with open("cart.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 4:
                username = parts[0]
                fruit_name = parts[1]
                qty = float(parts[2])
                total = float(parts[3])
                
                fruit = fruit_bst.search(fruit_name)
                if fruit:
                    price = fruit.price
                    unit = fruit.unit
                    img = fruit.imageURL
                else:
                    price = total / qty if qty > 0 else 0.0
                    unit = "unit"
                    img = "https://via.placeholder.com/120"
                
                cart_manager.add_to_cart(username, fruit_name, price, qty, unit, img)

def save_cart():
    with open("cart.txt", "w", encoding="utf-8") as f:
        for username, user_cart in cart_manager.carts.items():
            for fruit_name, item in user_cart.items():
                total = item["quantity"] * item["price"]
                f.write(f"{username} {fruit_name} {item['quantity']:.2f} {total:.2f}\n")

def load_orders():
    if not os.path.exists("orders.csv"):
        return
    with open("orders.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 5:
                order_id = row[0]
                username = row[1]
                status = row[2]
                items_str = row[3]
                total = float(row[4])
                
                items = []
                if items_str:
                    item_parts = items_str.split("|")
                    for part in item_parts:
                        if not part:
                            continue
                        subparts = part.split(":")
                        if len(subparts) >= 3:
                            name = subparts[0]
                            qty = float(subparts[1])
                            price = float(subparts[2])
                            img = FRUIT_IMAGES.get(name.lower(), "https://via.placeholder.com/120")
                            items.append({
                                "name": name,
                                "quantity": qty,
                                "price": price,
                                "img": img
                            })
                
                order_data = {
                    "orderID": order_id,
                    "customerName": username,
                    "status": status,
                    "items": items,
                    "totalAmount": total,
                    "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
                order_queue.enqueue(order_data)

def save_orders():
    orders = order_queue.to_list()
    with open("orders.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for order in orders:
            items_serialized = "|".join(
                f"{item['name']}:{item['quantity']:.0f}:{item['price']:.2f}" 
                for item in order["items"]
            )
            writer.writerow([
                order["orderID"],
                order["customerName"],
                order["status"],
                items_serialized,
                f"{order['totalAmount']:.2f}"
            ])

# Load all files on startup
load_users()
load_fruits()
load_cart()
load_orders()


# --- HTTP Frontend Routing ---

@app.route("/")
def serve_index():
    return send_from_directory(".", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    if path in ["login.html", "cart.html", "orders.html", "user.html", "admin.html"]:
        return send_from_directory(".", path)
    return send_from_directory(".", path)


# --- REST API Endpoints ---

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    
    if not username or not password or not email:
        return jsonify({"success": False, "message": "Missing required fields"}), 400
    
    # Check if username password constraints match (needs letters, numbers, special characters)
    # Replicate C isValidPassword: has Letter, has Digit, has Special char
    has_l = any(c.isalpha() for c in password)
    has_d = any(c.isdigit() for c in password)
    has_s = any(not c.isalnum() for c in password)
    
    if not (has_l and has_d and has_s):
        return jsonify({"success": False, "message": "Password must include letters, numbers, and special characters!"}), 400
        
    success = user_manager.register(username, password, email)
    if success:
        save_users()
        return jsonify({"success": True, "message": "Signup successful!"})
    else:
        return jsonify({"success": False, "message": "Username already exists!"}), 400

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    if not username or not password:
        return jsonify({"success": False, "message": "Missing credentials"}), 400
        
    # Admin login check
    if username == "admin" and password == "admin123":
        return jsonify({"success": True, "isAdmin": True, "user": {"username": "admin", "email": "admin@fruits.com"}})
        
    success = user_manager.login(username, password)
    if success:
        user = user_manager.get_user(username)
        return jsonify({"success": True, "isAdmin": False, "user": {"username": user["username"], "email": user["email"]}})
    else:
        return jsonify({"success": False, "message": "Invalid username or password!"}), 401

@app.route("/api/fruits", methods=["GET"])
def get_fruits():
    # Returns sorted fruits from BST
    fruits = fruit_bst.get_all_fruits()
    return jsonify(fruits)

@app.route("/api/fruits", methods=["POST"])
def add_fruit():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    price = data.get("price")
    stock = data.get("stock")
    unit = data.get("unit", "kg").strip()
    description = data.get("description", "Fresh and delicious fruit.").strip()
    imageURL = data.get("imageURL", "").strip()
    
    if not name or price is None or stock is None:
        return jsonify({"success": False, "message": "Missing fields"}), 400
        
    if not imageURL or imageURL == "N/A":
        imageURL = FRUIT_IMAGES.get(name.lower(), "https://via.placeholder.com/120")
        
    # BST insertion
    fruit_bst.insert(name, price, stock, unit, description, imageURL)
    save_fruits()
    return jsonify({"success": True, "message": "Product saved successfully!"})

@app.route("/api/fruits/<string:name>", methods=["DELETE"])
def delete_fruit(name):
    node = fruit_bst.search(name)
    if not node:
        return jsonify({"success": False, "message": "Fruit not found!"}), 404
        
    fruit_bst.delete(name)
    save_fruits()
    return jsonify({"success": True, "message": f"Fruit '{name}' deleted successfully!"})

@app.route("/api/cart", methods=["GET"])
def get_cart():
    username = request.args.get("username", "").strip()
    if not username:
        return jsonify({"success": False, "message": "Username required"}), 400
    
    cart_items = cart_manager.get_cart(username)
    return jsonify(cart_items)

@app.route("/api/cart/update", methods=["POST"])
def update_cart():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    fruit_name = data.get("name", "").strip()
    price = data.get("price")
    quantity = data.get("quantity")  # this is the change/value to add
    unit = data.get("unit", "kg").strip()
    img = data.get("img", "").strip()
    
    if not username or not fruit_name or quantity is None or price is None:
        return jsonify({"success": False, "message": "Missing fields"}), 400
        
    if not img:
        img = FRUIT_IMAGES.get(fruit_name.lower(), "https://via.placeholder.com/120")
        
    cart_manager.add_to_cart(username, fruit_name, price, quantity, unit, img)
    save_cart()
    return jsonify({"success": True, "cart": cart_manager.get_cart(username)})

@app.route("/api/cart/remove", methods=["POST"])
def remove_from_cart():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    fruit_name = data.get("name", "").strip()
    
    if not username or not fruit_name:
        return jsonify({"success": False, "message": "Missing fields"}), 400
        
    success = cart_manager.remove_from_cart(username, fruit_name)
    save_cart()
    if success:
        return jsonify({"success": True, "message": "Item removed from cart"})
    else:
        return jsonify({"success": False, "message": "Item not found in cart"}), 404

@app.route("/api/checkout", methods=["POST"])
def checkout():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    
    if not username:
        return jsonify({"success": False, "message": "Username required"}), 400
        
    cart_items = cart_manager.get_cart(username)
    if not cart_items:
        return jsonify({"success": False, "message": "Your cart is empty!"}), 400
        
    # Check inventory and deduct stock in BST
    insufficient_stock = []
    for item in cart_items:
        fruit_node = fruit_bst.search(item["name"])
        if not fruit_node:
            insufficient_stock.append(f"{item['name']} (not found)")
        elif fruit_node.stock < item["quantity"]:
            insufficient_stock.append(f"{item['name']} (available: {fruit_node.stock}, requested: {item['quantity']})")
            
    if insufficient_stock:
        return jsonify({
            "success": False, 
            "message": f"Insufficient stock for: {', '.join(insufficient_stock)}"
        }), 400
        
    # Deduct stock
    for item in cart_items:
        fruit_node = fruit_bst.search(item["name"])
        fruit_node.stock -= int(item["quantity"])
    save_fruits()
    
    # Place order
    order_id = f"ORD{int(time.time())}"
    total = sum(item["quantity"] * item["price"] for item in cart_items)
    
    order_data = {
        "orderID": order_id,
        "customerName": username,
        "status": "Pending",
        "items": cart_items,
        "totalAmount": total,
        "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    order_queue.enqueue(order_data)
    save_orders()
    
    # Clear cart
    cart_manager.clear_cart(username)
    save_cart()
    
    return jsonify({
        "success": True, 
        "message": f"Order placed successfully! Order ID: {order_id}",
        "orderID": order_id
    })

@app.route("/api/orders", methods=["GET"])
def get_orders():
    username = request.args.get("username", "").strip()
    all_orders = order_queue.to_list()
    
    # If a specific user is requesting (and not admin), filter by username
    if username and username != "admin":
        filtered_orders = [o for o in all_orders if o["customerName"] == username]
        return jsonify(filtered_orders)
        
    return jsonify(all_orders)

@app.route("/api/orders/status", methods=["POST"])
def update_order_status():
    data = request.get_json() or {}
    order_id = data.get("orderID", "").strip()
    status = data.get("status", "").strip()
    
    if not order_id or not status:
        return jsonify({"success": False, "message": "Missing fields"}), 400
        
    success = order_queue.update_status(order_id, status)
    if success:
        save_orders()
        return jsonify({"success": True, "message": f"Order {order_id} status updated to {status}."})
    else:
        return jsonify({"success": False, "message": "Order not found"}), 404

@app.route("/api/orders/cancel", methods=["POST"])
def cancel_order():
    data = request.get_json() or {}
    order_id = data.get("orderID", "").strip()
    
    if not order_id:
        return jsonify({"success": False, "message": "OrderID required"}), 400
        
    success = order_queue.cancel_order(order_id)
    if success:
        save_orders()
        return jsonify({"success": True, "message": "Order cancelled successfully."})
    else:
        return jsonify({"success": False, "message": "Order not found"}), 404

@app.route("/api/user/address", methods=["GET"])
def get_address():
    username = request.args.get("username", "").strip()
    if not username:
        return jsonify({"success": False, "message": "Username required"}), 400
        
    user = user_manager.get_user(username)
    if user:
        return jsonify({"success": True, "address": user.get("address", ""), "email": user.get("email", "")})
    else:
        return jsonify({"success": False, "message": "User not found"}), 404

@app.route("/api/user/address", methods=["POST"])
def update_address():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    address = data.get("address", "").strip()
    
    if not username or address is None:
        return jsonify({"success": False, "message": "Missing fields"}), 400
        
    success = user_manager.update_address(username, address)
    if success:
        save_users()
        return jsonify({"success": True, "message": "Address updated successfully!"})
    else:
        return jsonify({"success": False, "message": "User not found"}), 404


if __name__ == "__main__":
    # Load default fruits if fruits.txt is empty or doesn't exist
    if not os.path.exists("fruits.txt") or os.path.getsize("fruits.txt") == 0:
        # Prepopulate with C backend defaults
        fruit_bst.insert("Apple", 180, 100, "kg", "Sweet and Juicy Kashmir Apple", FRUIT_IMAGES["apple"])
        fruit_bst.insert("Banana", 50, 100, "dozen", "Fresh and Ripe Bananas", FRUIT_IMAGES["banana"])
        fruit_bst.insert("Orange", 120, 100, "kg", "Sweet and Tart Oranges", FRUIT_IMAGES["orange"])
        fruit_bst.insert("Grapes", 100, 100, "kg", "Sweet and Sour Grapes", FRUIT_IMAGES["grapes"])
        fruit_bst.insert("Mango", 220, 100, "kg", "Tropical mango delight", FRUIT_IMAGES["mango"])
        fruit_bst.insert("Pineapple", 90, 100, "kg", "Sweet, tangy and fresh Pineapple", FRUIT_IMAGES["pineapple"])
        fruit_bst.insert("Strawberry", 300, 100, "kg", "Farm fresh Strawberries", FRUIT_IMAGES["strawberry"])
        fruit_bst.insert("Papaya", 50, 100, "kg", "Healthy and nutrient-rich Papaya", FRUIT_IMAGES["papaya"])
        fruit_bst.insert("Watermelon", 40, 100, "kg", "Juicy Watermelon perfect for Summer", FRUIT_IMAGES["watermelon"])
        fruit_bst.insert("Dragonfruit", 60, 100, "piece", "Exotic and sweet Dragonfruit", FRUIT_IMAGES["dragonfruit"])
        fruit_bst.insert("Pomegranate", 150, 100, "kg", "Juicy Pomegranate bursting with sweetness", FRUIT_IMAGES["pomegranate"])
        fruit_bst.insert("Jackfruit", 80, 100, "kg", "Sweet and fresh Jackfruit", FRUIT_IMAGES["jackfruit"])
        save_fruits()
        
    print("Starting Flask web server on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=True)
