from flask import Flask, render_template, request, redirect
import psycopg2

app = Flask(__name__)

# Configure PostgreSQL connection
app.config['PG_HOST'] = 'localhost'
app.config['PG_USER'] = 'postgres'
app.config['PG_PASSWORD'] = '1234'
app.config['PG_DB'] = 'crud'

# Function to establish a database connection
def get_db_connection():
    conn = psycopg2.connect(
        host=app.config['PG_HOST'],
        database=app.config['PG_DB'],
        user=app.config['PG_USER'],
        password=app.config['PG_PASSWORD']
    )
    return conn

# Route to display all clients
@app.route('/', methods=['GET'])
@app.route('/clients', methods=['GET'])
def get_clients():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients")
    clients = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('clients.html', clients=clients)

# Route to add a new client
@app.route('/client/add', methods=['GET', 'POST'])
def add_client():
    if request.method == 'POST':
        name = request.form['name']
        clientid = request.form['client_id']
        client_manager = request.form['client_manager']
        contact_info = request.form['contact_info']

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO clients (client_id, name, client_manager, contact_info) VALUES (%s, %s, %s, %s)",
                (clientid, name, client_manager, contact_info)
            )
            conn.commit()
            return redirect('/clients')
        except Exception as e:
            conn.rollback() 
        finally:
            cur.close()
            conn.close()
    return render_template('add_client.html')

# Route to update an existing client
@app.route('/client/update/<int:id>', methods=['GET', 'POST'])
def update_client(id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        client_manager = request.form['client_manager']
        contact_info = request.form['contact_info']
        services_used = request.form['services_used']  # This is now treated as text

        try:
            cur.execute(
                "UPDATE clients SET name = %s, client_manager = %s, contact_info = %s WHERE client_id = %s",
                (name, client_manager, contact_info, id)
            )
            cur.execute(
                "UPDATE client_service SET service_id = %s WHERE client_id = %s",
                (services_used, id)  # Treat services_used as a string
            )
            conn.commit()
        except Exception as e:
            print("An error occurred during update:", str(e))
            return "An error occurred during update."

        cur.close()
        conn.close()
        return redirect('/clients')

    cur.execute("SELECT * FROM clients WHERE client_id = %s", (id,))
    client = cur.fetchone()
    cur.close()
    conn.close()

    if client is None:
        return "Client not found", 404

    return render_template('update_client.html', client=client)

# Route to delete a client
@app.route('/client/delete/<int:id>', methods=['GET', 'POST'])
def delete_client(id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        cur.execute("DELETE FROM clients WHERE client_id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect('/clients')

    cur.execute("SELECT COUNT(*) FROM clients WHERE client_id = %s", (id,))
    usecase_count = cur.fetchone()[0]
    cur.close()
    conn.close()
    if usecase_count > 0:
        return render_template('confirm_delete.html', client_id=id, usecase_count=usecase_count)
    else:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM clients WHERE id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect('/clients')

# Route to display use cases for a specific client
# Route to display use cases for a specific client
@app.route('/usecases/<int:client_id>', methods=['GET'])
def get_usecases(client_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM client_service WHERE client_id = %s", (client_id,))
    usecases = cur.fetchall()
    
    # Fetch the client details
    cur.execute("SELECT * FROM clients WHERE client_id = %s", (client_id,))
    client = cur.fetchone()  # Fetch client info

    cur.close()
    conn.close()
    return render_template('usecases.html', usecases=usecases, client=client)
 

# Route to add a new use case for a specific client
@app.route('/usecase/add/<int:client_id>', methods=['GET', 'POST'])
def add_usecase(client_id):
    if request.method == 'POST':
        service_id = request.form['service_id']
        client_id = request.form['client_id']
        start_date = request.form['start_date']
        status = request.form['status']
        custom_price=request.form['custom_price']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO client_service (service_id,client_id, start_Date,status,custom_price) VALUES (%s,%s,%s,%s,%s)",
            (service_id,client_id,start_date,status,custom_price))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(f'/usecases/{client_id}')
    return render_template('add_usecase.html', client_id=client_id)

# Route to update a specific use case
@app.route('/usecase/update/<int:id>', methods=['GET', 'POST'])
def update_usecase(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT client_id FROM usecases WHERE id = %s", (id,))
    client_id = cur.fetchone()[0]
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        cur.execute("UPDATE usecases SET title = %s, description = %s WHERE id = %s",
                    (title, description, id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(f'/usecases/{client_id}')
    cur.execute("SELECT * FROM usecases WHERE id = %s", (id,))
    usecase = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('update_usecase.html', usecase=usecase, client_id=client_id)

# Route to delete a use case
@app.route('/usecase/delete/<int:id>', methods=['GET'])
def delete_usecase(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT client_id FROM usecases WHERE client_id = %s", (id,))
    client_id = cur.fetchone()[0]
    cur.execute("DELETE FROM client_service WHERE service_id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(f'/usecases/{client_id}')

if __name__ == '__main__':
    app.run(debug=True)
