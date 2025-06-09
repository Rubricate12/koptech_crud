
## KOPTECH

Simple CRUD app with Flask Python
Follow these instructions to get a local copy up and running.

### Prerequisites

* Python 3.10+
* `pip` and `venv`
* A running MySQL server

### Installation & Setup

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/Rubricate12/koptech_crud.git
    cd koptechCorp
    ```

2.  **Create and activate a virtual environment:**
    * On Windows:
        ```sh
        python -m venv venv
        .\venv\Scripts\activate
        ```
    * On macOS/Linux:
        ```sh
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Create a `requirements.txt` file:**
    While inside your activated virtual environment, run this command to generate the requirements file. This is a crucial step for GitHub.
    ```sh
    pip freeze > requirements.txt
    ```
    Your `requirements.txt` file will now contain the necessary packages like `Flask` and `Flask-MySQLdb`.

4.  **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

### 🔧 Configuration

Before running the app, you must configure your database connection and secret key.

1.  Open `app.py` in your code editor.
2.  Find the MySQL configuration section and update it with your MySQL username and password.
    ```python
    # --- MySQL Connection Configuration ---
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'your_mysql_username' # CHANGE THIS
    app.config['MYSQL_PASSWORD'] = 'your_mysql_password' # CHANGE THIS
    app.config['MYSQL_DB'] = 'flask_app_db'
    ```
3.  Change the `app.secret_key` to a new, random string for security.

### 🗄️ Database Setup

1.  Connect to your MySQL server.
2.  Create the database:
    ```sql
    CREATE DATABASE flask_app_db;
    ```
3.  Use the database:
    ```sql
    USE flask_app_db;
    ```
4.  Run the following SQL script to create all the necessary tables, dont forget to create your own database and change it in app.py (or u can found them in SQLscript.txt):
    
    ```sql
    -- Full Database Schema --

    CREATE TABLE customer_orders (
        co_id VARCHAR(50) PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        address TEXT NOT NULL,
        product_id VARCHAR(50) NOT NULL,
        payment VARCHAR(50) NOT NULL,
        qty INT NOT NULL,
        phone VARCHAR(20) NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'Pending'
    );

    CREATE TABLE materials (
        material_id VARCHAR(50) PRIMARY KEY,
        material_name VARCHAR(255) NOT NULL,
        material_description TEXT,
        material_qty INT NOT NULL,
        storage_location VARCHAR(100)
    );

    CREATE TABLE material_requests (
        request_id INT AUTO_INCREMENT PRIMARY KEY,
        material_id VARCHAR(50) NULL,
        material_type VARCHAR(255),
        demand_qty INT NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'Pending',
        request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (material_id) REFERENCES materials(material_id) ON DELETE SET NULL
    );

    CREATE TABLE products (
        product_id VARCHAR(50) PRIMARY KEY,
        product_name VARCHAR(255) NOT NULL,
        product_description TEXT,
        product_qty INT NOT NULL,
        storage_date DATE,
        storage_location VARCHAR(100)
    );
    
    CREATE TABLE purchase_orders (
        po_id VARCHAR(50) PRIMARY KEY,
        company_name VARCHAR(255) NOT NULL,
        company_address TEXT NOT NULL,
        material_id VARCHAR(50) NOT NULL,
        vendor_id VARCHAR(50) NOT NULL,
        purchase_order_qty INT NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'Pending'
    );
    
    CREATE TABLE product_invoices (
        product_id VARCHAR(50) PRIMARY KEY,
        co_id VARCHAR(50) NOT NULL,
        invoice_date DATE NOT NULL,
        price DECIMAL(10, 2) NOT NULL,
        shipping_cost DECIMAL(10, 2) NOT NULL,
        billing_address TEXT NOT NULL,
        FOREIGN KEY (co_id) REFERENCES customer_orders(co_id) ON DELETE CASCADE
    );

    CREATE TABLE material_invoices (
        po_id VARCHAR(50) PRIMARY KEY,
        date DATE NOT NULL,
        material_cost DECIMAL(10, 2) NOT NULL,
        shipping_cost DECIMAL(10, 2) NOT NULL
    );

    CREATE TABLE purchasing_good_receipts (
        receipt_id INT AUTO_INCREMENT PRIMARY KEY,
        po_id VARCHAR(50) NOT NULL,
        material_type VARCHAR(255),
        order_qty INT NOT NULL,
        storage_date DATE,
        storage_location VARCHAR(255)
    );

    CREATE TABLE vendors (
        vendor_id VARCHAR(50) PRIMARY KEY,
        vendor_name VARCHAR(255) NOT NULL,
        vendor_address TEXT,
        bank_account VARCHAR(50)
    );
    ```

### ▶️ Running the Application

1.  Make sure you are in the project's root directory (`koptechCorp/`) in your terminal.
2.  Ensure your virtual environment is activated.
3.  Run the app:
    ```sh
    python app.py
    ```
4.  Open your web browser and navigate to `http://127.0.0.1:5000`.

## 📝 To-Do / Future Improvements

-   [ ] Implement real logic for the "Approve" buttons to update inventory and statuses.
-   [ ] Move user authentication to a `users` table in the database.
-   [ ] Implement role-based access control (e.g., Finance users cannot access Warehouse pages).
-   [ ] Add real pagination to the data tables.
-   [ ] Improve form validation and error handling.
