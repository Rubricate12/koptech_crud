from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = 'my_secret_key_12345678'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root' 
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'koptech'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

users = {
    "admin": "1234"
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

#rute publik
# landing page
@app.route('/')
def landing():
    return render_template('public/landing.html')

#rute staff menu
@app.route('/staff-menu')
def staff_menu():
    return render_template('public/staffmenu.html')

#rute login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        flash('You are already logged in.', 'info')
        # NOW REDIRECTS TO THE NEUTRAL STAFF MENU
        return redirect(url_for('staff_menu')) 

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        next_page = request.form.get('next')

        if username in users and users[username] == password:
            session['username'] = username  
            flash('Logged in successfully!', 'success')

            if next_page:
                return redirect(next_page)
            
            # NOW REDIRECTS TO THE NEUTRAL STAFF MENU
            return redirect(url_for('staff_menu')) 
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('auth/login.html')

#rute logout
@app.route('/logout')
def logout():
    session.clear() # Clear the entire session
    flash('You have been logged out.', 'info')
    return redirect(url_for('landing'))


#-------------------------------
#rute yang dilindungi/butuh login
#----------------------------------
#rute production
@app.route('/production/material-request')
@login_required
def production_material_request():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM material_requests ORDER BY request_date DESC")
    requests = cur.fetchall()
    cur.close()
    return render_template('production/material_request_list.html', requests=requests)

@app.route('/production/material-request/add', methods=['GET', 'POST'])
@login_required
def add_material_request():
    if request.method == 'POST':
        material_id = request.form['material_id']
        material_type = request.form['material_type']
        demand_qty = request.form['demand_qty']
        
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO material_requests(material_id, material_type, demand_qty) VALUES (%s, %s, %s)",
            (material_id, material_type, demand_qty)
        )
        mysql.connection.commit()
        cur.close()
        
        flash('Material request created successfully!', 'success')
        return redirect(url_for('production_material_request'))
    
    return render_template('production/add_material_request.html')

@app.route('/production/material-request/update/<int:request_id>', methods=['GET', 'POST'])
@login_required
def update_material_request(request_id):
    cur = mysql.connection.cursor()
    
    # Fetch the existing request data to show in the form
    cur.execute("SELECT * FROM material_requests WHERE request_id = %s", [request_id])
    request_data = cur.fetchone()

    if not request_data:
        flash('Material request not found!', 'danger')
        return redirect(url_for('production_material_request'))

    if request.method == 'POST':
        # This is the logic for when the user clicks "Save"
        material_id = request.form['material_id']
        material_type = request.form['material_type']
        demand_qty = request.form['demand_qty']

        # Execute the UPDATE query
        cur.execute("""
            UPDATE material_requests SET material_id = %s, material_type = %s, demand_qty = %s
            WHERE request_id = %s
        """, (material_id, material_type, demand_qty, request_id))
        
        mysql.connection.commit()
        cur.close()
        
        flash('Material request updated successfully!', 'success')
        return redirect(url_for('production_material_request'))

    cur.close()
    return render_template('production/update_material_request.html', request_data=request_data)


@app.route('/production/material-request/delete/<int:request_id>', methods=['POST'])
@login_required
def delete_material_request(request_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM material_requests WHERE request_id = %s", [request_id])
    mysql.connection.commit()
    cur.close()
    
    flash('Material request deleted successfully.', 'success')
    return redirect(url_for('production_material_request'))

@app.route('/production/material-availability')
@login_required
def list_material_availability():
    search_query = request.args.get('search')
    cur = mysql.connection.cursor()

    if search_query:
        search_term = f"%{search_query}%"
        # Search by material name or ID
        cur.execute("SELECT * FROM materials WHERE material_name LIKE %s OR material_id LIKE %s", (search_term, search_term))
    else:
        cur.execute("SELECT * FROM materials")
    
    materials = cur.fetchall()
    cur.close()

    return render_template('production/material_availability_list.html', materials=materials, search_query=search_query)

@app.route('/production/product-availability')
@login_required
def list_product_availability():
    search_query = request.args.get('search')
    cur = mysql.connection.cursor()

    if search_query:
        search_term = f"%{search_query}%"
        # Search by product name or ID
        cur.execute("SELECT * FROM products WHERE product_name LIKE %s OR product_id LIKE %s", (search_term, search_term))
    else:
        cur.execute("SELECT * FROM products")
    
    products = cur.fetchall()
    cur.close()

    return render_template('production/product_availability_list.html', products=products, search_query=search_query)

@app.route('/production/customer-orders')
@login_required
def list_production_customer_orders():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM customer_orders WHERE status = 'Pending'")
    orders = cur.fetchall()
    cur.close()
    return render_template('production/customer_order_list.html', orders=orders)

@app.route('/production/approve-customer-order/<string:co_id>', methods=['POST'])
@login_required
def approve_production_customer_order(co_id):
    cur = mysql.connection.cursor()
    # Update the status of the order to 'Approved'
    cur.execute("UPDATE customer_orders SET status = 'Approved' WHERE co_id = %s", [co_id])
    mysql.connection.commit()
    cur.close()

    flash(f"Customer Order {co_id} approved successfully.", 'success')
    return redirect(url_for('list_production_customer_orders'))

@app.route('/production/purchase-orders')
@login_required
def list_production_purchase_orders():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM purchase_orders WHERE status = 'Pending'")
    purchase_orders = cur.fetchall()
    cur.close()
    
    return render_template('production/purchase_order_list.html', purchase_orders=purchase_orders)

@app.route('/production/approve-purchase-order/<string:po_id>', methods=['POST'])
@login_required
def approve_production_purchase_order(po_id):
    cur = mysql.connection.cursor()
    # Update the status of the purchase order to 'Approved'
    cur.execute("UPDATE purchase_orders SET status = 'Approved' WHERE po_id = %s", [po_id])
    mysql.connection.commit()
    cur.close()

    flash(f"Purchase Order {po_id} approved successfully.", 'success')
    return redirect(url_for('list_production_purchase_orders'))


#----------------------------------
#rute warehouse

@app.route('/warehouse/material-availability')
@login_required
def list_warehouse_materials():
    search_query = request.args.get('search')
    cur = mysql.connection.cursor()
    if search_query:
        search_term = f"%{search_query}%"
        cur.execute("SELECT * FROM materials WHERE material_name LIKE %s OR material_id LIKE %s", (search_term, search_term))
    else:
        cur.execute("SELECT * FROM materials")
    materials = cur.fetchall()
    cur.close()
    return render_template('warehouse/material_list.html', materials=materials, search_query=search_query)

@app.route('/warehouse/material-availability/add', methods=['GET', 'POST'])
@login_required
def add_warehouse_material():
    if request.method == 'POST':
        material_id = request.form['material_id']
        material_name = request.form['material_name']
        material_description = request.form.get('material_description') # Use .get() for optional fields
        material_qty = request.form['material_qty']
        storage_location = request.form.get('storage_location')
        
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO materials(material_id, material_name, material_description, material_qty, storage_location) VALUES (%s, %s, %s, %s, %s)",
            (material_id, material_name, material_description, material_qty, storage_location)
        )
        mysql.connection.commit()
        cur.close()
        
        flash('Material created successfully!', 'success')
        return redirect(url_for('list_warehouse_materials'))
    
    return render_template('warehouse/add_material.html')


@app.route('/warehouse/material-availability/update/<string:material_id>', methods=['GET', 'POST'])
@login_required
def update_warehouse_material(material_id):
    cur = mysql.connection.cursor()
    
    # Fetch the existing material data
    cur.execute("SELECT * FROM materials WHERE material_id = %s", [material_id])
    material = cur.fetchone()

    if not material:
        flash('Material not found!', 'danger')
        return redirect(url_for('list_warehouse_materials'))

    if request.method == 'POST':
        material_name = request.form['material_name']
        material_description = request.form.get('material_description')
        material_qty = request.form['material_qty']
        storage_location = request.form.get('storage_location')
        
        # Execute the UPDATE query
        cur.execute("""
            UPDATE materials 
            SET material_name = %s, material_description = %s, material_qty = %s, storage_location = %s
            WHERE material_id = %s
        """, (material_name, material_description, material_qty, storage_location, material_id))
        
        mysql.connection.commit()
        cur.close()
        
        flash('Material updated successfully!', 'success')
        return redirect(url_for('list_warehouse_materials'))

    cur.close()
    return render_template('warehouse/update_material.html', material=material)

@app.route('/warehouse/material-availability/delete/<string:material_id>', methods=['POST'])
@login_required
def delete_warehouse_material(material_id):
    cur = mysql.connection.cursor()
    
    # Execute the DELETE query for the specific material_id
    cur.execute("DELETE FROM materials WHERE material_id = %s", [material_id])
    
    mysql.connection.commit()
    cur.close()
    
    flash('Material deleted successfully.', 'success')
    return redirect(url_for('list_warehouse_materials'))

@app.route('/warehouse/view-requests')
@login_required
def list_warehouse_requests():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM material_requests WHERE status = 'Pending'")
    requests = cur.fetchall()
    cur.close()
    return render_template('warehouse/request_list.html', requests=requests)

@app.route('/warehouse/approve-request/<int:request_id>', methods=['POST'])
@login_required
def approve_warehouse_request(request_id):
    cur = mysql.connection.cursor()
    
    cur.execute("SELECT material_id, demand_qty FROM material_requests WHERE request_id = %s", [request_id])
    request_data = cur.fetchone()

    if request_data:
        material_id_to_update = request_data['material_id']
        qty_to_decrease = request_data['demand_qty']

        cur.execute("UPDATE material_requests SET status = 'Approved' WHERE request_id = %s", [request_id])

        cur.execute("UPDATE materials SET material_qty = material_qty - %s WHERE material_id = %s", (qty_to_decrease, material_id_to_update))
        
        mysql.connection.commit()
        flash(f"Request {request_id} approved and inventory updated.", 'success')
    else:
        flash("Request not found.", 'danger')
        
    cur.close()
    return redirect(url_for('list_warehouse_requests'))

@app.route('/warehouse/good-receipt')
@login_required
def list_good_receipts():
    search_query = request.args.get('search')
    cur = mysql.connection.cursor()
    if search_query:
        search_term = f"%{search_query}%"
        cur.execute("SELECT * FROM material_good_receipts WHERE po_id LIKE %s", [search_term])
    else:
        cur.execute("SELECT * FROM material_good_receipts")
    receipts = cur.fetchall()
    cur.close()
    return render_template('warehouse/good_receipt_list.html', receipts=receipts, search_query=search_query)

@app.route('/warehouse/good-receipt/add', methods=['GET', 'POST'])
@login_required
def add_good_receipt():
    if request.method == 'POST':
        good_receipt_id = request.form['good_receipt_id']
        po_id = request.form['po_id']
        material_type = request.form.get('material_type')
        good_receipt_date = request.form['good_receipt_date']
        good_receipt_location = request.form.get('good_receipt_location')

        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO material_good_receipts(good_receipt_id, po_id, material_type, good_receipt_date, good_receipt_location) VALUES (%s, %s, %s, %s, %s)",
            (good_receipt_id, po_id, material_type, good_receipt_date, good_receipt_location)
        )
        mysql.connection.commit()
        cur.close()
        flash('Good Receipt created successfully!', 'success')
        return redirect(url_for('list_good_receipts'))
    
    return render_template('warehouse/add_good_receipt.html')

@app.route('/warehouse/good-receipt/update/<string:receipt_id>', methods=['GET', 'POST'])
@login_required
def update_good_receipt(receipt_id):
    cur = mysql.connection.cursor()
    
    # Fetch the existing record to pre-fill the form
    cur.execute("SELECT * FROM material_good_receipts WHERE good_receipt_id = %s", [receipt_id])
    receipt = cur.fetchone()

    if not receipt:
        flash('Good Receipt not found!', 'danger')
        return redirect(url_for('list_good_receipts'))

    if request.method == 'POST':
        # Get updated data from the submitted form
        po_id = request.form['po_id']
        material_type = request.form.get('material_type')
        good_receipt_date = request.form['good_receipt_date']
        good_receipt_location = request.form.get('good_receipt_location')
        
        # Execute the UPDATE query
        cur.execute("""
            UPDATE material_good_receipts 
            SET po_id = %s, material_type = %s, good_receipt_date = %s, good_receipt_location = %s
            WHERE good_receipt_id = %s
        """, (po_id, material_type, good_receipt_date, good_receipt_location, receipt_id))
        
        mysql.connection.commit()
        cur.close()
        
        flash('Good Receipt updated successfully!', 'success')
        return redirect(url_for('list_good_receipts'))

    cur.close()
    return render_template('warehouse/update_good_receipt.html', receipt=receipt)


@app.route('/warehouse/good-receipt/delete/<string:receipt_id>', methods=['POST'])
@login_required
def delete_good_receipt(receipt_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM material_good_receipts WHERE good_receipt_id = %s", [receipt_id])
    mysql.connection.commit()
    cur.close()
    flash('Good Receipt deleted successfully.', 'success')
    return redirect(url_for('list_good_receipts'))

@app.route('/warehouse/product-availability')
@login_required
def list_warehouse_products():
    search_query = request.args.get('search')
    cur = mysql.connection.cursor()
    if search_query:
        search_term = f"%{search_query}%"
        cur.execute("SELECT * FROM products WHERE product_name LIKE %s OR product_id LIKE %s", (search_term, search_term))
    else:
        cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    cur.close()
    return render_template('warehouse/product_list.html', products=products, search_query=search_query)

@app.route('/warehouse/product-availability/add', methods=['GET', 'POST'])
@login_required
def add_warehouse_product():
    if request.method == 'POST':
        product_id = request.form['product_id']
        product_name = request.form['product_name']
        product_description = request.form.get('product_description')
        product_qty = request.form['product_qty']
        storage_date = request.form.get('storage_date')
        storage_location = request.form.get('storage_location')
        
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO products(product_id, product_name, product_description, product_qty, storage_date, storage_location) VALUES (%s, %s, %s, %s, %s, %s)",
            (product_id, product_name, product_description, product_qty, storage_date, storage_location)
        )
        mysql.connection.commit()
        cur.close()
        
        flash('Product created successfully!', 'success')
        return redirect(url_for('list_warehouse_products'))
    
    return render_template('warehouse/add_product.html')

@app.route('/warehouse/product-availability/update/<string:product_id>', methods=['GET', 'POST'])
@login_required
def update_warehouse_product(product_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products WHERE product_id = %s", [product_id])
    product = cur.fetchone()
    if not product:
        flash('Product not found!', 'danger')
        return redirect(url_for('list_warehouse_products'))

    if request.method == 'POST':
        product_name = request.form['product_name']
        product_description = request.form.get('product_description')
        product_qty = request.form['product_qty']
        storage_date = request.form.get('storage_date')
        storage_location = request.form.get('storage_location')
        
        cur.execute("""
            UPDATE products SET product_name = %s, product_description = %s, product_qty = %s, storage_date = %s, storage_location = %s
            WHERE product_id = %s
        """, (product_name, product_description, product_qty, storage_date, storage_location, product_id))
        mysql.connection.commit()
        cur.close()
        
        flash('Product updated successfully!', 'success')
        return redirect(url_for('list_warehouse_products'))

    cur.close()
    return render_template('warehouse/update_product.html', product=product)

@app.route('/warehouse/product-availability/delete/<string:product_id>', methods=['POST'])
@login_required
def delete_warehouse_product(product_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM products WHERE product_id = %s", [product_id])
    mysql.connection.commit()
    cur.close()
    flash('Product deleted successfully.', 'success')
    return redirect(url_for('list_warehouse_products'))

@app.route('/warehouse/purchase-orders')
@login_required
def list_warehouse_purchase_orders():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM purchase_orders")
    purchase_orders = cur.fetchall()
    cur.close()
    return render_template('warehouse/purchase_order_list.html', purchase_orders=purchase_orders)


#----------------------------------
#rute finance
@app.route('/finance')
@login_required
def finance():
    search_query = request.args.get('search')
    
    cur = mysql.connection.cursor()

    if search_query:
        search_term = f"%{search_query}%"
        cur.execute("SELECT * FROM customer_orders WHERE name LIKE %s", [search_term])
    else:
        # If there is no search query, fetch all orders
        cur.execute("SELECT * FROM customer_orders")
    
    orders = cur.fetchall()
    cur.close()

    return render_template('finance/finance.html', orders=orders, search_query=search_query)

#tambah customer
@app.route('/finance/add', methods=['GET', 'POST'])
@login_required
def add_customer_order():
    if request.method == 'POST':
        co_id = request.form['co_id']
        name = request.form['customer_name']
        address = request.form['customer_address']
        product_id = request.form['product_id']
        payment = request.form['payment_method']
        qty = request.form['order_qty']
        phone = request.form['phone_number']

        # Create cursor, execute query, and commit to DB
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO customer_orders(co_id, name, address, product_id, payment, qty, phone) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (co_id, name, address, product_id, payment, qty, phone)
        )
        mysql.connection.commit()
        cur.close()
        
        flash('Customer order created successfully!', 'success')
        return redirect(url_for('finance'))

    return render_template('finance/add_customer_order.html')

#update customer
@app.route('/finance/update/<string:order_id>', methods=['GET', 'POST'])
@login_required
def update_customer_order(order_id):
    cur = mysql.connection.cursor()
    
    cur.execute("SELECT * FROM customer_orders WHERE co_id = %s", [order_id])
    order = cur.fetchone()

    if not order:
        flash('Order not found!', 'danger')
        return redirect(url_for('finance'))

    if request.method == 'POST':
        name = request.form['customer_name']
        address = request.form['customer_address']
        product_id = request.form['product_id']
        payment = request.form['payment_method']
        qty = request.form['order_qty']
        phone = request.form['phone_number']

        cur.execute(
            """
            UPDATE customer_orders SET 
            name = %s, address = %s, product_id = %s, payment = %s, qty = %s, phone = %s
            WHERE co_id = %s
            """,
            (name, address, product_id, payment, qty, phone, order_id)
        )
        mysql.connection.commit()
        cur.close()

        flash(f"Order {order_id} updated successfully!", 'success')
        return redirect(url_for('finance'))

    cur.close()
    return render_template('finance/update_customer_order.html', order=order)

@app.route('/finance/delete/<string:order_id>', methods=['POST'])
@login_required
def delete_customer_order(order_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM customer_orders WHERE co_id = %s", [order_id])
    mysql.connection.commit()
    cur.close()
    flash(f"Order {order_id} deleted successfully.", 'success')
    return redirect(url_for('finance'))

@app.route('/finance/product-invoice')
@login_required
def list_product_invoices():
    search_query = request.args.get('search')
    cur = mysql.connection.cursor()
    if search_query:
        search_term = f"%{search_query}%"
        cur.execute("SELECT * FROM product_invoices WHERE product_id LIKE %s OR co_id LIKE %s", (search_term, search_term))
    else:
        cur.execute("SELECT * FROM product_invoices")
    invoices = cur.fetchall()
    cur.close()
    return render_template('finance/product_invoice_list.html', invoices=invoices, search_query=search_query)

@app.route('/finance/product-invoice/add', methods=['GET', 'POST'])
@login_required
def add_product_invoice():
    if request.method == 'POST':
        product_id = request.form['product_id']
        co_id = request.form['co_id']
        invoice_date = request.form['invoice_date']
        price = request.form['price']
        shipping_cost = request.form['shipping_cost']
        billing_address = request.form['billing_address']
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO product_invoices(product_id, co_id, invoice_date, price, shipping_cost, billing_address) VALUES (%s, %s, %s, %s, %s, %s)",
            (product_id, co_id, invoice_date, price, shipping_cost, billing_address)
        )
        mysql.connection.commit()
        cur.close()
        flash('Product invoice created successfully!', 'success')
        return redirect(url_for('list_product_invoices'))
    
    return render_template('finance/add_product_invoice.html')

@app.route('/finance/product-invoice/update/<string:invoice_id>', methods=['GET', 'POST'])
@login_required
def update_product_invoice(invoice_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM product_invoices WHERE product_id = %s", [invoice_id])
    invoice = cur.fetchone()
    if not invoice:
        flash('Invoice not found!', 'danger')
        return redirect(url_for('list_product_invoices'))

    if request.method == 'POST':
        co_id = request.form['co_id']
        invoice_date = request.form['invoice_date']
        price = request.form['price']
        shipping_cost = request.form['shipping_cost']
        billing_address = request.form['billing_address']
        cur.execute("""
            UPDATE product_invoices SET co_id = %s, invoice_date = %s, price = %s, shipping_cost = %s, billing_address = %s
            WHERE product_id = %s
        """, (co_id, invoice_date, price, shipping_cost, billing_address, invoice_id))
        mysql.connection.commit()
        cur.close()
        flash('Product invoice updated successfully!', 'success')
        return redirect(url_for('list_product_invoices'))

    cur.close()
    return render_template('finance/update_product_invoice.html', invoice=invoice)

@app.route('/finance/product-invoice/delete/<string:invoice_id>', methods=['POST'])
@login_required
def delete_product_invoice(invoice_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM product_invoices WHERE product_id = %s", [invoice_id])
    mysql.connection.commit()
    cur.close()
    flash('Product invoice deleted successfully.', 'success')
    return redirect(url_for('list_product_invoices'))

@app.route('/finance/view-material-invoices')
@login_required
def view_finance_material_invoices():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM material_invoices")
    invoices = cur.fetchall()
    cur.close()
    return render_template('finance/material_invoice_list.html', invoices=invoices)

@app.route('/finance/view-purchase-orders')
@login_required
def view_finance_purchase_orders():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM purchase_orders")
    purchase_orders = cur.fetchall()
    cur.close()
    return render_template('finance/purchase_order_list.html', purchase_orders=purchase_orders)



#----------------------------------------
#rute purchasing

@app.route('/purchasing/good-receipt')
@login_required
def list_purchasing_good_receipts():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM purchasing_good_receipts")
    receipts = cur.fetchall()
    cur.close()
    return render_template('purchasing/good_receipt_list.html', receipts=receipts)

@app.route('/purchasing/material-invoice')
@login_required
def list_purchasing_material_invoices():
    search_query = request.args.get('search')
    cur = mysql.connection.cursor()
    if search_query:
        search_term = f"%{search_query}%"
        cur.execute("SELECT * FROM material_invoices WHERE po_id LIKE %s", [search_term])
    else:
        cur.execute("SELECT * FROM material_invoices")
    invoices = cur.fetchall()
    cur.close()
    return render_template('purchasing/material_invoice_list.html', invoices=invoices, search_query=search_query)

@app.route('/purchasing/material-invoice/add', methods=['GET', 'POST'])
@login_required
def add_purchasing_material_invoice():
    if request.method == 'POST':
        po_id = request.form['po_id']
        date = request.form['date']
        material_cost = request.form['material_cost']
        shipping_cost = request.form['shipping_cost']
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO material_invoices(po_id, date, material_cost, shipping_cost) VALUES (%s, %s, %s, %s)",
            (po_id, date, material_cost, shipping_cost)
        )
        mysql.connection.commit()
        cur.close()
        flash('Material invoice created successfully!', 'success')
        return redirect(url_for('list_purchasing_material_invoices'))
    return render_template('purchasing/add_material_invoice.html')

@app.route('/purchasing/material-invoice/update/<string:po_id>', methods=['GET', 'POST'])
@login_required
def update_purchasing_material_invoice(po_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM material_invoices WHERE po_id = %s", [po_id])
    invoice = cur.fetchone()
    if not invoice:
        flash('Invoice not found!', 'danger')
        return redirect(url_for('list_purchasing_material_invoices'))
    if request.method == 'POST':
        date = request.form['date']
        material_cost = request.form['material_cost']
        shipping_cost = request.form['shipping_cost']
        cur.execute("""
            UPDATE material_invoices SET date = %s, material_cost = %s, shipping_cost = %s
            WHERE po_id = %s
        """, (date, material_cost, shipping_cost, po_id))
        mysql.connection.commit()
        cur.close()
        flash('Invoice updated successfully!', 'success')
        return redirect(url_for('list_purchasing_material_invoices'))
    cur.close()
    return render_template('purchasing/update_material_invoice.html', invoice=invoice)

@app.route('/purchasing/material-invoice/delete/<string:po_id>', methods=['POST'])
@login_required
def delete_purchasing_material_invoice(po_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM material_invoices WHERE po_id = %s", [po_id])
    mysql.connection.commit()
    cur.close()
    flash('Invoice deleted successfully.', 'success')
    return redirect(url_for('list_purchasing_material_invoices'))

@app.route('/purchasing/material-request')
@login_required
def list_purchasing_material_requests():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM material_requests")
    requests = cur.fetchall()
    cur.close()
    return render_template('purchasing/material_request_list.html', requests=requests)

@app.route('/purchasing/purchase-order')
@login_required
def list_purchasing_purchase_orders():
    search_query = request.args.get('search')
    cur = mysql.connection.cursor()
    if search_query:
        search_term = f"%{search_query}%"
        cur.execute("SELECT * FROM purchase_orders WHERE company_name LIKE %s OR po_id LIKE %s", (search_term, search_term))
    else:
        cur.execute("SELECT * FROM purchase_orders")
    purchase_orders = cur.fetchall()
    cur.close()
    return render_template('purchasing/purchase_order_list.html', purchase_orders=purchase_orders, search_query=search_query)

@app.route('/purchasing/purchase-order/add', methods=['GET', 'POST'])
@login_required
def add_purchasing_purchase_order():
    if request.method == 'POST':
        po_id = request.form['po_id']
        company_name = request.form['company_name']
        company_address = request.form['company_address']
        material_id = request.form['material_id']
        vendor_id = request.form['vendor_id']
        purchase_order_qty = request.form['purchase_order_qty']
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO purchase_orders(po_id, company_name, company_address, material_id, vendor_id, purchase_order_qty) VALUES (%s, %s, %s, %s, %s, %s)",
            (po_id, company_name, company_address, material_id, vendor_id, purchase_order_qty)
        )
        mysql.connection.commit()
        cur.close()
        flash('Purchase order created successfully!', 'success')
        return redirect(url_for('list_purchasing_purchase_orders'))
    return render_template('purchasing/add_purchase_order.html')

@app.route('/purchasing/purchase-order/update/<string:po_id>', methods=['GET', 'POST'])
@login_required
def update_purchasing_purchase_order(po_id):
    cur = mysql.connection.cursor()
    
    # Fetch the existing record to show in the form
    cur.execute("SELECT * FROM purchase_orders WHERE po_id = %s", [po_id])
    po = cur.fetchone()

    # If the record doesn't exist, redirect with an error
    if not po:
        flash('Purchase Order not found!', 'danger')
        return redirect(url_for('list_purchasing_purchase_orders'))

    # This block runs when the user submits the 'Edit' form
    if request.method == 'POST':
        # Get updated data from the form
        company_name = request.form['company_name']
        company_address = request.form['company_address']
        material_id = request.form['material_id']
        vendor_id = request.form['vendor_id']
        purchase_order_qty = request.form['purchase_order_qty']

        # Execute the UPDATE query in the database
        cur.execute("""
            UPDATE purchase_orders 
            SET company_name = %s, company_address = %s, material_id = %s, vendor_id = %s, purchase_order_qty = %s
            WHERE po_id = %s
        """, (company_name, company_address, material_id, vendor_id, purchase_order_qty, po_id))
        
        mysql.connection.commit()
        cur.close()
        
        flash('Purchase Order updated successfully!', 'success')
        return redirect(url_for('list_purchasing_purchase_orders'))

    cur.close()
    return render_template('purchasing/update_purchase_order.html', po=po)


@app.route('/purchasing/purchase-order/delete/<string:po_id>', methods=['POST'])
@login_required
def delete_purchasing_purchase_order(po_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM purchase_orders WHERE po_id = %s", [po_id])
    mysql.connection.commit()
    cur.close()
    flash('Purchase Order deleted successfully.', 'success')
    return redirect(url_for('list_purchasing_purchase_orders'))

@app.route('/purchasing/vendors')
@login_required
def list_vendors():
    search_query = request.args.get('search')
    cur = mysql.connection.cursor()
    if search_query:
        search_term = f"%{search_query}%"
        cur.execute("SELECT * FROM vendors WHERE vendor_name LIKE %s", [search_term])
    else:
        cur.execute("SELECT * FROM vendors")
    vendors = cur.fetchall()
    cur.close()
    return render_template('purchasing/vendor_list.html', vendors=vendors, search_query=search_query)

@app.route('/purchasing/vendor/add', methods=['GET', 'POST'])
@login_required
def add_vendor():
    if request.method == 'POST':
        vendor_id = request.form['vendor_id']
        vendor_name = request.form['vendor_name']
        vendor_address = request.form.get('vendor_address')
        bank_account = request.form.get('bank_account')
        
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO vendors(vendor_id, vendor_name, vendor_address, bank_account) VALUES (%s, %s, %s, %s)",
            (vendor_id, vendor_name, vendor_address, bank_account)
        )
        mysql.connection.commit()
        cur.close()
        
        flash('Vendor created successfully!', 'success')
        return redirect(url_for('list_vendors'))
    
    return render_template('purchasing/add_vendor.html')

@app.route('/purchasing/vendor/update/<string:vendor_id>', methods=['GET', 'POST'])
@login_required
def update_vendor(vendor_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM vendors WHERE vendor_id = %s", [vendor_id])
    vendor = cur.fetchone()
    if not vendor:
        flash('Vendor not found!', 'danger')
        return redirect(url_for('list_vendors'))

    if request.method == 'POST':
        vendor_name = request.form['vendor_name']
        vendor_address = request.form.get('vendor_address')
        bank_account = request.form.get('bank_account')
        
        cur.execute("""
            UPDATE vendors SET vendor_name = %s, vendor_address = %s, bank_account = %s
            WHERE vendor_id = %s
        """, (vendor_name, vendor_address, bank_account, vendor_id))
        mysql.connection.commit()
        cur.close()
        
        flash('Vendor updated successfully!', 'success')
        return redirect(url_for('list_vendors'))

    cur.close()
    return render_template('purchasing/update_vendor.html', vendor=vendor)

@app.route('/purchasing/vendor/delete/<string:vendor_id>', methods=['POST'])
@login_required
def delete_vendor(vendor_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM vendors WHERE vendor_id = %s", [vendor_id])
    mysql.connection.commit()
    cur.close()
    flash('Vendor deleted successfully.', 'success')
    return redirect(url_for('list_vendors'))

if __name__ == '__main__':
    app.run(debug=True)