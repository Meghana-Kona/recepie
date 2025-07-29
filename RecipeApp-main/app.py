from flask import Flask, render_template, request, redirect, session, url_for, jsonify,flash,get_flashed_messages
from flask_mail import Mail, Message
import random, sqlite3, os


# ================== Flask Setup ===================
app = Flask(__name__)
app.secret_key = os.urandom(24)

# ================== Flask-Mail Setup ==============
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'lmoksha.132@gmail.com'
app.config['MAIL_PASSWORD'] = 'mpul kfev dcju ucji'
mail = Mail(app)

# ================= Razorpay (Mock Keys) ============


# ================== DB INIT =======================
# ================== DB INIT =======================
def init_db():
    with sqlite3.connect('database/recipes.db') as conn:
        cur = conn.cursor()

        # Users
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            phone TEXT,
            password TEXT
        )''')

        # Recipes
        cur.execute('''CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            image TEXT,
            ingredients TEXT,
            calories TEXT,
            process TEXT,
            video_url TEXT
        )''')

        # Feedback
        cur.execute('''CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            message TEXT
        )''')

        # Contact Messages
        cur.execute('''CREATE TABLE IF NOT EXISTS contact (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            message TEXT
        )''')

        # 🟡 Insert sample recipe if not exists
        cur.execute("SELECT * FROM recipes WHERE name = ?", ('Biryani',))
        if not cur.fetchone():
            cur.execute('''
                INSERT INTO recipes (name, description, ingredients, calories, process, video_url, image)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                'Biryani',
                'Spicy and aromatic rice dish',
                'Rice;Chicken;Spices;Onions;Yogurt',
                '500 kcal',
                '1. Marinate chicken; 2. Cook rice; 3. Layer and simmer.',
                'https://www.youtube.com/embed/your-video-id',
                'biryani.jpg'
            ))

        conn.commit()



# ================== Register ======================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        session['name'] = request.form['name']
        session['email'] = request.form['email']
        session['phone'] = request.form['phone']
        session['password'] = request.form['password']

        # Generate and store OTP
        otp = str(random.randint(1000, 9999))
        session['otp'] = otp

        # Send OTP email
        try:
            msg = Message("Your OTP for FlavorFiesta",
                          sender=app.config['MAIL_USERNAME'],
                          recipients=[session['email']])
            msg.body = f"Hello {session['name']},\n\nYour OTP is: {otp}\n\nThank you for registering at FlavorFiesta!"
            mail.send(msg)
            flash("OTP sent to your email. Please check your inbox.", "success")
            return redirect(url_for('verify_otp'))
        except Exception as e:
            flash("Error sending email. Please try again later.", "error")
            return redirect(url_for('register'))

    return render_template('register.html')


# ================== OTP Verify ======================
@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        user_otp = request.form['otp']
        if user_otp == session.get('otp'):
            name = session.get('name')
            email = session.get('email')
            phone = session.get('phone')
            password = session.get('password')

            with sqlite3.connect('database/recipes.db') as conn:
                cur = conn.cursor()

                # Check if email already exists
                cur.execute("SELECT * FROM users WHERE email = ?", (email,))
                if cur.fetchone():
                    flash("Email already registered. Please log in or use a different email.", "error")
                    return redirect(url_for('register'))

                # Insert new user
                cur.execute("INSERT INTO users (name, email, phone, password) VALUES (?, ?, ?, ?)",
                            (name, email, phone, password))
                conn.commit()

            # Clean up session
            session.pop('otp', None)
            session.pop('name', None)
            session.pop('email', None)
            session.pop('phone', None)
            session.pop('password', None)

            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))
        else:
            flash("Incorrect OTP. Please try again.", "error")
            return redirect(url_for('verify_otp'))

    return render_template('otp_verify.html')

@app.route('/resend_otp', methods=['POST'])
def resend_otp():
    if 'email' in session and 'name' in session:
        otp = str(random.randint(1000, 9999))
        session['otp'] = otp

        msg = Message("Your OTP for Recipe Hub", sender=app.config['MAIL_USERNAME'], recipients=[session['email']])
        msg.body = f"Hello {session['name']},\nYour new OTP is: {otp}"
        mail.send(msg)

        flash("OTP resent successfully. Please check your email.", "success")
    else:
        flash("Session expired. Please register again.", "error")
        return redirect(url_for('register'))

    return redirect(url_for('verify_otp'))

# ================== Login ======================



@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        flash("You're already logged in.", "info")
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        with sqlite3.connect('database/recipes.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
            user = cur.fetchone()

        if user:
            session['user_id'] = user[0]     # user[0] = id
            session['user_name'] = user[1]   # user[1] = name
            flash(f"Welcome, {user[1]}!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password. Please try again.", "error")

    return render_template('login.html')



@app.route('/chatbot', methods=['POST'])
def chatbot():
    user_msg = request.json.get('message', '').lower()

    # Predefined responses
    responses = {
    "help": "You can ask me about recipes, payment options, registration, or quick dish suggestions.",
    "hi": "Hii there!! How can I assist you today?",
    "hello": "Hello! Need help finding a recipe or making a payment?",
    "quick recipe": "Try our 15-min 'Paneer Stir Fry' or 'Garlic Butter Pasta'!",
    "veg": "We have lots of veg options! Try 'Veg Biryani', 'Aloo Curry', or 'Paneer Butter Masala'.",
    "nonveg": "We have lots of non-veg options! Try 'Butter Chicken', 'Chicken Biryani', or 'Fish Curry'.",
    "spicy": "You might love 'Spicy Chicken 65' or 'Andhra Pepper Chicken'.",
    "sweet": "Craving sweet? Try 'Rasgulla', 'Mysore Pak', or 'Gajar Ka Halwa'.",
    "dessert": "Yes! Try 'Gulab Jamun', 'Kheer', or 'Mango Kulfi'.",
    "snack": "Looking for snacks? Try 'Samosa', 'Cutlet', or 'Pakora'.",
    "popular": "Our most loved dish is 'Hyderabadi Dum Biryani'.",
    "biryani": "Our Biryani recipes take 40–60 mins depending on the style!",
    "breakfast": "Try 'Poha', 'Upma', or 'Idli-Sambar' for a healthy breakfast.",
    "lunch": "Biryani, Paneer Masala, or Fish Curry with rice are great lunch ideas!",
    "dinner": "Light dinner? Try 'Khichdi', 'Chapati with Sabji', or 'Tomato Soup'.",
    "healthy": "You can try 'Grilled Veg Salad', 'Sprouts Chaat', or 'Oats Upma'.",
    "easy": "Try 'Masala Maggi', 'Egg Bhurji', or 'Curd Rice'.",
    "kids": "Kids love 'Cheese Sandwich', 'Fruit Salad', and 'Mini Uttapam'.",
    "tiffin": "Perfect for lunchbox: 'Vegetable Pulao', 'Aloo Paratha', or 'Chapati Rolls'.",
    "order": "To order, just scan the QR code on the recipe card after login.",
    "payment": "Payments are accepted via UPI QR code using any app like GPay, PhonePe, or Paytm.",
    "scan": "Please scan the QR on the selected recipe card to make a payment.",
    "how to pay": "You can pay using any UPI app. Just scan our QR code shown under the recipe.",
    "register": "Click on the Register button in the top menu to create an account.",
    "login": "Click on the Login button in the top menu to access your account.",
    "logout": "Click on Logout from the top menu to end your session.",
    "contact": "You can contact us using the form on the Contact page.",
    "about": "We are a recipe sharing and ordering platform for food lovers!",
    "recipe video": "Recipe videos will be shown on the recipe detail page (YouTube embedded).",
    "recommend": "I recommend trying 'Paneer Butter Masala' or 'Chicken Dum Biryani'!",
    "what's new": "We just added 10+ new monsoon special recipes! Check them out!",
    "guide": "- You can type: 'help', 'veg', 'order', 'payment', 'quick recipe', 'login', 'register', etc.",
    "faq": "For common questions, please contact us and ask me there!",
    "how it works": "1. Search a recipe 2. View details 3. Make payment 4. Get directions to cook!",
    "ingredients": "Click on any recipe to view ingredients, steps, and calories.",
    "calories": "Each recipe shows calories per serving. Healthy options are also tagged!",
    "time": "Cooking time is shown on each recipe card. Most range from 15–60 mins."
}


    # Basic command matching
    for key, reply in responses.items():
        if key in user_msg:
            return jsonify({'reply': reply})

    # Fallback
    return jsonify({'reply': "Sorry, I didn't understand. Try asking 'suggest a recipe' or 'payment method'."})

    

# ================== Logout ======================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ================== Home Page ======================
@app.route('/')
def home():
    choice = request.args.get('choice', '').lower()
    mood = request.args.get('mood', '').lower()

    with sqlite3.connect('database/recipes.db') as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        if choice or mood:
            cur.execute("""
                SELECT * FROM recipes 
                WHERE LOWER(name) LIKE ? OR LOWER(description) LIKE ?
            """, ('%' + choice + '%', '%' + mood + '%'))
        else:
            cur.execute("SELECT * FROM recipes ORDER BY RANDOM() LIMIT 6")
        
        recipes = cur.fetchall()

    return render_template('index.html', recipes=recipes)


# ================== Search (Choice / Mood) ============
import requests

API_KEY = "7ae4ae39c9c14fa4be65e13ae0d2033b"

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    
    if not query:
        return render_template('search_results.html', query="", recipes=None)

    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        'query': query,
        'number': 5,
        'addRecipeInformation': True,
        'apiKey': API_KEY
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        recipes = data.get('results', [])
        return render_template('search_results.html', query=query, recipes=recipes)
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching recipes: {e}")
        return render_template('search_results.html', query=query, recipes=None)



# ================== Recipe Detail ======================
@app.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    with sqlite3.connect('database/recipes.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
        recipe = cur.fetchone()

    if recipe:
        return render_template('recipe_detail.html', recipe={
            'id': recipe[0],
            'name': recipe[1],
            'description': recipe[2],
            'image': recipe[3],
            'ingredients': recipe[4],
            'calories': recipe[5],
            'process': recipe[6],
            'video_url': recipe[7]
        })
    else:
        return "Recipe not found", 404

# ================== Add Feedback ======================
@app.route('/feedback', methods=['POST'])
def feedback():
    name = request.form['name']
    message = request.form['message']
    with sqlite3.connect('database/recipes.db') as conn:
        conn.execute("INSERT INTO feedback (name, message) VALUES (?, ?)", (name, message))
        conn.commit()
    flash("Thank you for your feedback!", "success")

# ================== Contact Form ======================
  # make sure this is imported

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # Save to SQLite
        with sqlite3.connect('database/recipes.db') as conn:
            conn.execute("INSERT INTO contact (name, email, message) VALUES (?, ?, ?)", (name, email, message))
            conn.commit()

        # Send email to admin
        msg = Message("New Contact Form Submission", sender=email, recipients=[app.config['MAIL_USERNAME']])
        msg.body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
        mail.send(msg)

        # ✅ Flash message for user, stay on same page
        flash("Thanks for your feedback! We'll get back to you soon.", "success")
        return render_template('contact.html')  # Stay on the same page

    return render_template('contact.html')




# ================== Razorpay Payment ======================

# ================== About Page ======================
@app.route('/about')
def about():
    return render_template('about.html')

# ================== Run ======================
if __name__ == '__main__':
    app.run(debug=True)
