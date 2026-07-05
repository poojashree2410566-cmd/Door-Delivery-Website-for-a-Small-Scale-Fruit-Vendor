# data_structures.py
import time
from collections import deque

# --- Password Encryption (Compatible with C key=5 XOR cipher) ---
def xor_crypt(text, key=5):
    """Encrypts or decrypts text using a simple XOR cipher with the given key."""
    return "".join(chr(ord(c) ^ key) for c in text)


# --- Binary Search Tree (BST) for Fruits ---
class FruitNode:
    def __init__(self, name, price, stock, unit, description="Delicious and fresh fruit.", imageURL="N/A"):
        self.name = name
        self.price = float(price)
        self.stock = int(stock)
        self.unit = unit
        self.description = description
        self.imageURL = imageURL
        self.left = None
        self.right = None

    def to_dict(self):
        return {
            "name": self.name,
            "price": self.price,
            "stock": self.stock,
            "unit": self.unit,
            "description": self.description,
            "imageURL": self.imageURL
        }

class FruitBST:
    def __init__(self):
        self.root = None

    def insert(self, name, price, stock, unit, description="Delicious and fresh fruit.", imageURL="N/A"):
        new_node = FruitNode(name, price, stock, unit, description, imageURL)
        if not self.root:
            self.root = new_node
            return True
        
        current = self.root
        while True:
            # BST insertion sorted lexicographically by fruit name (case-insensitive for consistency)
            if name.lower() < current.name.lower():
                if current.left is None:
                    current.left = new_node
                    return True
                current = current.left
            elif name.lower() > current.name.lower():
                if current.right is None:
                    current.right = new_node
                    return True
                current = current.right
            else:
                # Fruit already exists, update its stock and price
                current.price = float(price)
                current.stock = int(stock)
                current.unit = unit
                if description != "Delicious and fresh fruit.":
                    current.description = description
                if imageURL != "N/A":
                    current.imageURL = imageURL
                return False

    def search(self, name):
        current = self.root
        name_lower = name.lower()
        while current:
            curr_lower = current.name.lower()
            if name_lower == curr_lower:
                return current
            elif name_lower < curr_lower:
                current = current.left
            else:
                current = current.right
        return None

    def get_all_fruits(self):
        """Returns list of all fruits sorted alphabetically (In-order traversal)."""
        fruits = []
        def _inorder(node):
            if node:
                _inorder(node.left)
                fruits.append(node.to_dict())
                _inorder(node.right)
        _inorder(self.root)
        return fruits

    def delete(self, name):
        """Delete a node from BST by name."""
        def _delete(node, name_val):
            if not node:
                return node
            
            name_val_lower = name_val.lower()
            curr_lower = node.name.lower()
            
            if name_val_lower < curr_lower:
                node.left = _delete(node.left, name_val)
            elif name_val_lower > curr_lower:
                node.right = _delete(node.right, name_val)
            else:
                # Node to delete found
                if not node.left:
                    return node.right
                elif not node.right:
                    return node.left
                
                # Node with two children: Get the inorder successor (smallest in the right subtree)
                temp = node.right
                while temp.left:
                    temp = temp.left
                
                # Copy successor content
                node.name = temp.name
                node.price = temp.price
                node.stock = temp.stock
                node.unit = temp.unit
                node.description = temp.description
                node.imageURL = temp.imageURL
                
                # Delete successor
                node.right = _delete(node.right, temp.name)
            return node
        
        self.root = _delete(self.root, name)


# --- FIFO Queue for Order Management ---
class OrderNode:
    def __init__(self, order_data):
        self.order = order_data  # Dictionary containing order details
        self.next = None

class FIFOOrderQueue:
    def __init__(self):
        self.front = None
        self.rear = None
        self.size = 0

    def enqueue(self, order_data):
        new_node = OrderNode(order_data)
        if not self.rear:
            self.front = self.rear = new_node
        else:
            self.rear.next = new_node
            self.rear = new_node
        self.size += 1

    def dequeue(self):
        if not self.front:
            return None
        temp = self.front
        self.front = self.front.next
        if not self.front:
            self.rear = None
        self.size -= 1
        return temp.order

    def to_list(self):
        orders = []
        current = self.front
        while current:
            orders.append(current.order)
            current = current.next
        return orders

    def update_status(self, order_id, new_status):
        current = self.front
        while current:
            if current.order.get("orderID") == order_id:
                current.order["status"] = new_status
                return True
            current = current.next
        return False

    def cancel_order(self, order_id):
        return self.update_status(order_id, "Cancelled")


# --- Hash Map Managers (for User & Cart) ---
class UserManager:
    """Manages user registry using a Python dictionary (Hash Map) for O(1) lookups."""
    def __init__(self):
        self.users = {}  # username -> {password, email, address}

    def register(self, username, password, email, address=""):
        if username in self.users:
            return False  # Already exists
        self.users[username] = {
            "username": username,
            "password": password,  # Stored as plain text in memory
            "email": email,
            "address": address
        }
        return True

    def login(self, username, password):
        if username in self.users:
            return self.users[username]["password"] == password
        return False

    def get_user(self, username):
        return self.users.get(username)

    def update_address(self, username, address):
        if username in self.users:
            self.users[username]["address"] = address
            return True
        return False


class CartManager:
    """Manages shopping carts for all users using a Hash Map (O(1) access)."""
    def __init__(self):
        self.carts = {}  # username -> {fruit_name -> {fruit_name, price, quantity, unit, img}}

    def add_to_cart(self, username, fruit_name, price, quantity, unit, img):
        if username not in self.carts:
            self.carts[username] = {}
        
        user_cart = self.carts[username]
        if fruit_name in user_cart:
            user_cart[fruit_name]["quantity"] += quantity
        else:
            user_cart[fruit_name] = {
                "name": fruit_name,
                "price": float(price),
                "quantity": float(quantity),
                "unit": unit,
                "img": img
            }
        
        # If quantity falls to 0 or below, remove it
        if user_cart[fruit_name]["quantity"] <= 0:
            self.remove_from_cart(username, fruit_name)

    def remove_from_cart(self, username, fruit_name):
        if username in self.carts and fruit_name in self.carts[username]:
            del self.carts[username][fruit_name]
            # Clean up empty carts
            if not self.carts[username]:
                del self.carts[username]
            return True
        return False

    def get_cart(self, username):
        if username in self.carts:
            return list(self.carts[username].values())
        return []

    def clear_cart(self, username):
        if username in self.carts:
            del self.carts[username]
