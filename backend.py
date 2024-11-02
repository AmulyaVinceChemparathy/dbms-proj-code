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

# Route to render the home page
@app.route('/')
def index():
    return render_template('index.html')

# Route to display all clients
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

@app.route('/usecases/<int:client_id>', methods=['GET'])
def get_usecases(client_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Fetch the client from the clients table
    cur.execute("SELECT * FROM clients WHERE client_id = %s", (client_id,))
    client = cur.fetchone()
    
    usecases = []
    if client:
        cur.execute("""
        SELECT service_id, client_id, start_date, status, custom_price 
        FROM client_service WHERE client_id = %s
        """, (client_id,))
        usecases = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('usecases.html', usecases=usecases, client=client)

# Route to add a new use case for a specific client
@app.route('/usecases/add/<int:client_id>', methods=['GET', 'POST'])
def add_usecase(client_id):
    if request.method == 'POST':
        service_id = request.form['service_id']
        start_date = request.form['start_date']
        status = request.form['status']
        custom_price = request.form['custom_price']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO client_service (service_id, client_id, start_date, status, custom_price) VALUES (%s, %s, %s, %s, %s)",
            (service_id, client_id, start_date, status, custom_price))
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
    cur.execute("SELECT client_id FROM client_Service WHERE id = %s", (id,))
    client_id = cur.fetchone()[0]
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        cur.execute("UPDATE client_Service SET title = %s, description = %s WHERE id = %s",
                    (title, description, id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(f'/usecases/{client_id}')
    cur.execute("SELECT * FROM client_Service WHERE id = %s", (id,))
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

# Route to display all services (general services page)
@app.route('/services', methods=['GET'])
def display_services():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Fetching services from the database
    cur.execute("SELECT * FROM services")
    services = cur.fetchall()
    
    cur.close()
    conn.close()
    
    # Render the services.html template with the retrieved services and client_id
    return render_template('services.html', services=services)


@app.route('/service/add', methods=['GET', 'POST'])
def add_service():
    if request.method == 'POST':
        service_description = request.form['service_description']
        resources_required = request.form['resources_required']
        estimated_cost = float(request.form['estimated_cost'])
        developing_team = request.form['developing_team']
        actions = request.form['actions']

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO services (service_description, resources_required, estimated_cost, developing_team, actions) VALUES (%s, %s, %s, %s, %s)",
                (service_description, resources_required, estimated_cost, developing_team, actions)
            )
            conn.commit()
        except Exception as e:
            print(f"Error occurred: {e}")  # Log the error
            return "An error occurred while adding the service.", 500
        finally:
            cur.close()
            conn.close()

        return redirect('/services')
    return render_template('add_services.html')

@app.route('/service/delete/<int:id>', methods=['GET', 'POST'])
def delete_service(id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        # Delete the service from the database
        cur.execute("DELETE FROM services WHERE service_id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect('/services')

    # Check if the service exists
    cur.execute("SELECT COUNT(*) FROM services WHERE service_id = %s", (id,))
    service_count = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    # If the service exists, render the confirmation page
    if service_count > 0:
        return render_template('confirm_delete_service.html', service_id=id)
    else:
        return redirect('/services')  # Redirect if the service doesn't exist

@app.route('/service/update/<int:id>', methods=['GET', 'POST'])
def update_service(id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Fetch the current service details
    if request.method == 'POST':
        service_description = request.form['service_description']
        resources_required = request.form['resources_required']
        estimated_cost = request.form['estimated_cost']
        developing_team = request.form['developing_team']
        actions = request.form['actions']
        
        # Update the service in the database
        cur.execute("""
            UPDATE services
            SET service_description = %s,
                resources_required = %s,
                estimated_cost = %s,
                developing_team = %s,
                actions = %s
            WHERE service_id = %s
        """, (service_description, resources_required, estimated_cost, developing_team, actions, id))
        
        conn.commit()
        cur.close()
        conn.close()
        return redirect('/services')
    
    # Fetch the existing service data to populate the form
    cur.execute("SELECT * FROM services WHERE service_id = %s", (id,))
    service = cur.fetchone()
    cur.close()
    conn.close()
    
    if service:
        return render_template('update_service.html', service=service)
    else:
        return redirect('/services')  # Redirect if the service is not found

if __name__ == '__main__':
    app.run(debug=True)

