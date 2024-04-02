from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import stripe


app = Flask(__name__)


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345'
app.config['MYSQL_DB'] = 'user_details'
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
mysql = MySQL(app)

# Loading Home Page


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
	try:
		if request.method == 'POST' and 'mail' in request.form and 'password' in request.form:
			mail = request.form['mail']
			password = request.form['password']
			cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
			cursor.execute('SELECT * FROM users WHERE mail_id = % s AND password = % s', (mail, password, ))
			account = cursor.fetchone()
			cursor.execute('SELECT user_name FROM users WHERE mail_id = % s AND password = % s', (mail, password, ))
			# fetch the value from the dictionary
			user_name = cursor.fetchone()['user_name']
			cursor.execute('CREATE DATABASE IF NOT EXISTS `{}`'.format(user_name))
			cursor.execute('USE `{}`'.format(user_name))
			cursor.execute('CREATE TABLE IF NOT EXISTS products (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), price DECIMAL(10, 2))')# for selling page
			cursor.execute('CREATE TABLE IF NOT EXISTS cart (product_id INT AUTO_INCREMENT PRIMARY KEY, product_name VARCHAR(255), product_price DECIMAL(10, 2), product_quantity varchar(255))')# for addtocart page
			cursor.execute('CREATE TABLE IF NOT EXISTS critics (full_name varchar(200),email varchar(200),message varchar(500))')# for critics page
			if account:
				session['loggedin'] = True
				session['mail_id'] = account['mail_id']  # database la irukrathu
				session['user_name'] = account['user_name']  # database la irukrathu
				flash(f"Welcome {user_name} :)")
				return render_template('index.html')
			else:
				flash('Incorrect mail id / password !')
				return redirect(url_for("index"))
	except:
		flash('Incorrect Password')
		return render_template('login.html')
	return render_template('login.html')

@app.route('/logout')
def logout():
	session.pop('loggedin', None)
	session.pop('mail_id', None)
	session.pop('user_name', None)
	flash('Logged out successfully!')
	return redirect(url_for('index'))


@app.route('/Sign up', methods=['GET', 'POST'])
def Signup():
	msg = ''
	if request.method == 'POST' and 'user_name' in request.form and 'password1' in request.form and 'password2' in request.form and 'mail' in request.form:
		mail = request.form['mail']
		username = request.form['user_name']
		password1 = request.form['password1']
		password2 = request.form['password2']

		con = mysql.connection.cursor()
		con.execute('SELECT * FROM users WHERE mail_id = %s', (mail,))
		mysql.connection.commit()
		account = con.fetchone()
		con.execute('SELECT * FROM users WHERE user_name = %s', (username,))
		mysql.connection.commit()
		user_name_exist = con.fetchone()
		if account:
			flash('Account already exists !')
			return redirect(url_for("index"))
		elif user_name_exist:
			flash('User name already exists ! Try another name.')
			return redirect(url_for("index"))
		elif not re.match(r'[^@]+@[^@]+\.[^@]+', mail):
			flash('Invalid email address !')
			return redirect(url_for("index"))
		elif password1 != password2:
			flash("password doesn't match", category='warning')
			return redirect(url_for("index"))
		elif not re.match(r'[A-Za-z0-9]+', username):
			flash('Username must contain only characters and numbers !')
		# elif not username or not password1 or not password2 or not mail:
		# flash('Please fill out the form !')
		else:
			con = mysql.connection.cursor()
			sql = "insert into users values (%s,%s,%s,%s)"
			con.execute(sql, [mail, username, password1, password2])
			#mysql.connection.commit()
			con.execute(f"create table {username}(activity varchar(500),orders varchar(500))")
			mysql.connection.commit()
			con.close()
			flash('User Details Added.Now you can Login')
			return redirect(url_for("index"))
	return render_template('signup.html')


@app.route("/Contact us")
def contact():
    return render_template("contact.html")


@app.route("/Our team")
def ourteam():
    return render_template("our_team.html")


@app.route('/sell')
def sell():
	username = session['user_name']
	cur = mysql.connection.cursor()
	cur.execute('USE `{}`'.format(username))  # use the user's database
	cur.execute('SELECT * FROM products')
	products = cur.fetchall()
	cur.close()
	return render_template('sell.html', products=products)

@app.route('/add_product', methods=['POST'])
def add_product():
    username = session['user_name']
    name = request.form['name']
    price = request.form['price']
    cur = mysql.connection.cursor()
    cur.execute('USE `{}`'.format(username))  # use the user's database
    cur.execute('INSERT INTO products (name, price) VALUES (%s, %s)', (name, price))  # use parameterized queries
    mysql.connection.commit()
    cur.close()
    return redirect('/sell')

@app.route('/edit_product', methods=['POST'])
def edit_product():
    username = session['user_name']
    product_id = request.form['product_id']
    name = request.form['name']
    price = request.form['price']
    cur = mysql.connection.cursor()
    cur.execute('USE `{}`'.format(username))  # use the user's database
    cur.execute('UPDATE products SET name = %s, price = %s WHERE id = %s', (name, price, product_id))
    mysql.connection.commit()
    cur.close()
    return redirect('/sell')

@app.route('/delete_product', methods=['POST'])
def delete_product():
    username = session['user_name']
    product_id = request.form['product_id']
    cur = mysql.connection.cursor()
    cur.execute('USE `{}`'.format(username))  # use the user's database
    cur.execute('DELETE FROM products WHERE id = %s', (product_id,))
    mysql.connection.commit()
    cur.close()
    return redirect('/sell')


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
	product_quantity = request.form.get('number')
	product_name = request.form.get('product_name')
	product_price = request.form.get('product_price')	
	# Perform database insertion
	username = session['user_name']
	cursor = mysql.connection.cursor()
	cursor.execute('USE `{}`'.format(username))  # use the user's database
	insert_query = "INSERT INTO cart (product_quantity, product_name, product_price) VALUES (%s, %s, %s)"
	cursor.execute(insert_query, (product_quantity, product_name, product_price))
	mysql.connection.commit()	
	return redirect('/cart')


@app.route('/remove_from_cart/<int:cart_item_id>', methods=['POST'])
def remove_from_cart(cart_item_id):
    # Perform database deletion
	username = session['user_name']
	cursor = mysql.connection.cursor()
	cursor.execute('USE `{}`'.format(username))  # use the user's database
	delete_query = "DELETE FROM cart WHERE product_id = %s"
	cursor.execute(delete_query, (cart_item_id,))
	mysql.connection.commit()	
	return redirect('/cart')


@app.route('/cart')
def view_cart():
	username = session['user_name']
	cursor = mysql.connection.cursor()
	cursor.execute('USE `{}`'.format(username))  # use the user's database
	cursor.execute("SELECT * FROM cart")
	cart_items = cursor.fetchall()	
	cursor.close()
	return render_template('cart.html', cart_items=cart_items)


@app.route('/critic_message', methods=['POST'])
def submit_message():
	full_name = request.form.get('full_name')
	email = request.form.get('email')
	message = request.form.get('message')	
	# Perform database insertion
	username = session['user_name']
	cur = mysql.connection.cursor()
	cur.execute('USE `{}`'.format(username))  # use the user's database
	insert_query = "INSERT INTO critics (full_name, email, message) VALUES (%s, %s, %s)"
	cur.execute(insert_query, (full_name, email, message))
	mysql.connection.commit()
	flash('Message sent successfully')
	return render_template('contact.html')


@app.route('/card.html')
def card():
    return render_template('card.html')

@app.route('/card1.html')
def card1():
    return render_template('card1.html')

@app.route('/card.html')
def card2():
    return render_template('card2.html')

@app.route('/card3.html')
def card3():
    return render_template('card3.html')

@app.route('/card4.html')
def card4():
    return render_template('card4.html')

@app.route('/card5.html')
def card5():
    return render_template('card5.html')

@app.route('/card6.html')
def card6():
    return render_template('card6.html')

@app.route('/card7.html')
def card7():
    return render_template('card7.html')

@app.route('/card8.html')
def card8():
    return render_template('card8.html')

@app.route('/card9.html')
def card9():
    return render_template('card9.html')

@app.route('/card10.html')
def card10():
    return render_template('card10.html')

@app.route('/card11.html')
def card11():
    return render_template('card11.html')

@app.route('/card12.html')
def card12():
    return render_template('card12.html')

@app.route('/card13.html')
def card13():
    return render_template('card13.html')

@app.route('/card14.html')
def card14():
    return render_template('card14.html')

@app.route('/card15.html')
def card15():
    return render_template('card15.html')

@app.route('/card16.html')
def card16():
    return render_template('card16.html')

@app.route('/card17.html')
def card17():
    return render_template('card17.html')


stripe.api_key = 'sk_test_51NQ6NjSGvZqUy8UEzknxLASCBOQxo0mLgHMI2s0sjgwU5I1R94ny4x5uwf3lEPeM0U1pK9h5JJUHFatfAdanAtcj00Nzitd7f5'

@app.route('/process_payment', methods=['POST'])
def process_payment():
    # Retrieve payment information from the form
    amount = request.form['amount']
    token = request.form['stripeToken']
    email = request.form['email']

    try:
        # Create a charge using the Stripe API
        charge = stripe.Charge.create(
            amount=(amount),  # Amount in cents
            currency='usd',
            source=token,
            description='Payment'
        )

        # Perform additional actions after successful payment
        # For example, update the database or send a confirmation email
        
        return redirect(url_for('payment_success'))
    except stripe.error.CardError as e:
        # Handle card errors
        error_msg = e.error.message
        flash(f'Card Error: {error_msg}', 'error')
        return redirect(url_for('payment_success'))
    except stripe.error.StripeError as e:
        # Handle other Stripe errors
        flash(f'Stripe Error: {str(e)}', 'error')
        return redirect(url_for('payment_success'))

@app.route('/payment_success')
def payment_success():
    return render_template('payment_success.html')



if (__name__ == '__main__'):
    app.secret_key = "abc123"
    app.run(debug=True, host='0.0.0.0')
